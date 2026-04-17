"""
Validation Script - Skyfusion Analytics Caudal Predictor
=======================================================

Script para validación del modelo LSTM de predicción de caudales.
Calcula métricas de regresión: RMSE, MAE, R².

Métricas implementadas:
- RMSE (Root Mean Square Error)
- MAE (Mean Absolute Error)
- R² (Coefficient of Determination)
- MAPE (Mean Absolute Percentage Error)
- NS (Nash-Sutcliffe Efficiency)

Autor: Skyfusion Analytics - Data Engineering
Fecha: 2026-04-16
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    mean_absolute_percentage_error
)

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')

import tensorflow as tf

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RegressionMetrics:
    """Calculador de métricas de regresión"""
    
    @staticmethod
    def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calcula Root Mean Square Error"""
        return float(np.sqrt(mean_squared_error(y_true, y_pred)))
    
    @staticmethod
    def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calcula Mean Absolute Error"""
        return float(mean_absolute_error(y_true, y_pred))
    
    @staticmethod
    def r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calcula R² (Coefficient of Determination)"""
        return float(r2_score(y_true, y_pred))
    
    @staticmethod
    def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calcula Mean Absolute Percentage Error"""
        return float(mean_absolute_percentage_error(y_true, y_pred)) * 100
    
    @staticmethod
    def nse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calcula Nash-Sutcliffe Efficiency Coefficient"""
        numerator = np.sum((y_true - y_pred) ** 2)
        denominator = np.sum((y_true - np.mean(y_true)) ** 2)
        return float(1 - (numerator / denominator))
    
    @staticmethod
    def pbias(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calcula Percent Bias"""
        return float(100 * np.sum(y_pred - y_true) / np.sum(y_true))
    
    @staticmethod
    def kge(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calcula Kling-Gupta Efficiency"""
        r = np.corrcoef(y_true, y_pred)[0, 1]
        alpha = np.std(y_pred) / np.std(y_true)
        beta = np.mean(y_pred) / np.mean(y_true)
        
        kge = 1 - np.sqrt((r - 1)**2 + (alpha - 1)**2 + (beta - 1)**2)
        return float(kge)
    
    @staticmethod
    def calculate_all(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calcula todas las métricas"""
        metrics = {
            'rmse': RegressionMetrics.rmse(y_true, y_pred),
            'mae': RegressionMetrics.mae(y_true, y_pred),
            'r2': RegressionMetrics.r2(y_true, y_pred),
            'mape': RegressionMetrics.mape(y_true, y_pred),
            'nse': RegressionMetrics.nse(y_true, y_pred),
            'pbias': RegressionMetrics.pbias(y_true, y_pred),
            'kge': RegressionMetrics.kge(y_true, y_pred)
        }
        return metrics


class ValidationPipeline:
    """Pipeline de validación del modelo"""
    
    def __init__(
        self,
        model_dir: str = '../../data/models/caudal_predictor',
        data_dir: str = '../../data/historical'
    ):
        self.model_dir = Path(model_dir)
        self.data_dir = Path(data_dir)
        
        self.model = None
        self.scaler = None
        self.config = None
        self.feature_cols = None
    
    def load_model_and_scaler(self) -> bool:
        """Carga el modelo y el scaler"""
        logger.info("Cargando modelo y escalador...")
        
        model_path = self.model_dir / 'caudal_lstm_model.keras'
        if not model_path.exists():
            model_path = self.model_dir / 'best_model.keras'
        scaler_path = self.model_dir / 'scaler.save'
        config_path = self.model_dir / 'model_config.json'
        
        if not model_path.exists():
            logger.error(f"Modelo no encontrado: {model_path}")
            return False
        
        if not scaler_path.exists():
            logger.error(f"Escalador no encontrado: {scaler_path}")
            return False
        
        try:
            self.model = tf.keras.models.load_model(model_path)
            logger.info(f"Modelo cargado: {model_path}")
            
            import joblib
            self.scaler = joblib.load(scaler_path)
            logger.info(f"Escalador cargado: {scaler_path}")
            
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"Configuración cargada: {self.config}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error cargando artefactos: {e}")
            return False
    
    def load_test_data(
        self,
        test_ratio: float = 0.15
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Carga y prepara datos de prueba.
        
        Returns:
            Tuple de (X_test, y_test) con datos escalados
        """
        logger.info("Cargando datos de prueba...")
        
        caudal_path = self.data_dir / 'streamflow.csv'
        
        if caudal_path.exists():
            df = pd.read_csv(caudal_path, parse_dates=['date'])
        else:
            logger.warning("Archivo de datos no encontrado, usando datos de entrenamiento")
            df = self._generate_synthetic_data()
        
        df = df.sort_values('date').reset_index(drop=True)
        df = df.ffill().bfill()
        
        if 'precipitation' not in df.columns:
            df['precipitation'] = np.random.exponential(10, len(df))
        if 'width' not in df.columns:
            df['width'] = 15 + np.random.normal(0, 2, len(df))
        
        feature_cols = ['caudal', 'precipitation', 'width',
                       'sin_month', 'cos_month', 'sin_day', 'cos_day']
        
        df['month'] = df['date'].dt.month
        df['day_of_year'] = df['date'].dt.dayofyear
        df['sin_month'] = np.sin(2 * np.pi * df['month'] / 12)
        df['cos_month'] = np.cos(2 * np.pi * df['month'] / 12)
        df['sin_day'] = np.sin(2 * np.pi * df['day_of_year'] / 365)
        df['cos_day'] = np.cos(2 * np.pi * df['day_of_year'] / 365)
        
        feature_cols = [c for c in feature_cols if c in df.columns]
        self.feature_cols = feature_cols
        
        data = df[feature_cols].values
        
        if self.scaler is not None:
            data = self.scaler.transform(data)
        
        sequence_length = self.config.get('sequence_length', 30) if self.config else 30
        
        X, y = [], []
        for i in range(sequence_length, len(data)):
            X.append(data[i - sequence_length:i])
            y.append(data[i, 0])
        
        X = np.array(X)
        y = np.array(y)
        
        X = X.reshape((X.shape[0], sequence_length, len(feature_cols)))
        
        n_test = int(len(X) * test_ratio)
        X_test = X[-n_test:]
        y_test = y[-n_test:]
        
        logger.info(f"Datos de prueba: {len(X_test)} muestras")
        
        return X_test, y_test, df
    
    def _generate_synthetic_data(self) -> pd.DataFrame:
        """Genera datos sintéticos para prueba"""
        dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='D')
        n = len(dates)
        
        np.random.seed(123)
        
        caudal = 50 + 20 * np.sin(2 * np.pi * np.arange(n) / 365) + \
                 np.random.normal(0, 5, n)
        caudal = np.clip(caudal, 5, 150)
        
        return pd.DataFrame({
            'date': dates,
            'caudal': caudal,
            'precipitation': np.random.exponential(10, n),
            'width': 15 + np.random.normal(0, 2, n)
        })
    
    def inverse_transform_predictions(
        self,
        y_pred_scaled: np.ndarray,
        y_true_scaled: np.ndarray,
        feature_idx: int = 0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Invierte la transformación de escalado para obtener valores en unidades originales.
        
        Args:
            y_pred_scaled: Predicciones escaladas
            y_true_scaled: Valores reales escalados
            feature_idx: Índice de la característica a desescalar
            
        Returns:
            Tuple de (y_pred_original, y_true_original)
        """
        if self.scaler is None:
            return y_pred_scaled, y_true_scaled
        
        n_samples = len(y_pred_scaled)
        n_features = self.scaler.n_features_in_
        
        dummy_pred = np.zeros((n_samples, n_features))
        dummy_pred[:, feature_idx] = y_pred_scaled.flatten()
        y_pred_original = self.scaler.inverse_transform(dummy_pred)[:, feature_idx]
        
        dummy_true = np.zeros((n_samples, n_features))
        dummy_true[:, feature_idx] = y_true_scaled.flatten()
        y_true_original = self.scaler.inverse_transform(dummy_true)[:, feature_idx]
        
        return y_pred_original, y_true_original
    
    def validate(self) -> Dict[str, float]:
        """
        Ejecuta la validación completa.
        
        Returns:
            Diccionario con todas las métricas
        """
        logger.info("=" * 60)
        logger.info("VALIDACIÓN DEL MODELO DE PREDICCIÓN DE CAUDALES")
        logger.info("=" * 60)
        
        if not self.load_model_and_scaler():
            logger.error("No se pudieron cargar los artefactos del modelo")
            return {}
        
        X_test, y_test_scaled, df = self.load_test_data()
        
        logger.info("\nRealizando predicciones...")
        y_pred_scaled = self.model.predict(X_test, verbose=0).flatten()
        
        y_pred_original, y_true_original = self.inverse_transform_predictions(
            y_pred_scaled, y_test_scaled
        )
        
        logger.info("\nCalculando métricas...")
        
        metrics = RegressionMetrics.calculate_all(y_true_original, y_pred_original)
        
        logger.info("\n" + "=" * 60)
        logger.info("RESULTADOS DE VALIDACIÓN")
        logger.info("=" * 60)
        logger.info(f"\nMétricas principales:")
        logger.info(f"  RMSE: {metrics['rmse']:.4f} (unidades originales)")
        logger.info(f"  MAE:  {metrics['mae']:.4f} (unidades originales)")
        logger.info(f"  R²:   {metrics['r2']:.4f}")
        logger.info(f"\nMétricas adicionales:")
        logger.info(f"  MAPE:    {metrics['mape']:.2f}%")
        logger.info(f"  NSE:     {metrics['nse']:.4f}")
        logger.info(f"  P-Bias:  {metrics['pbias']:.4f}%")
        logger.info(f"  KGE:     {metrics['kge']:.4f}")
        
        logger.info("\n" + "=" * 60)
        logger.info("INTERPRETACIÓN DE MÉTRICAS")
        logger.info("=" * 60)
        
        self._interpret_results(metrics)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'model_path': str(self.model_dir / 'caudal_lstm_model.keras'),
            'metrics': metrics,
            'n_samples': len(y_pred_original),
            'config': self.config
        }
        
        self._save_results(results)
        
        return metrics
    
    def _interpret_results(self, metrics: Dict[str, float]):
        """Interpreta los resultados de las métricas"""
        
        r2 = metrics['r2']
        nse = metrics['nse']
        kge = metrics['kge']
        
        logger.info("\n--- Interpretación R² ---")
        if r2 >= 0.9:
            logger.info("  Excelente: El modelo explica >90% de la varianza")
        elif r2 >= 0.7:
            logger.info("  Bueno: El modelo explica 70-90% de la varianza")
        elif r2 >= 0.5:
            logger.info("  Aceptable: El modelo explica 50-70% de la varianza")
        else:
            logger.info("  Insuficiente: El modelo explica <50% de la varianza")
        
        logger.info("\n--- Interpretación NSE ---")
        if nse >= 0.9:
            logger.info("  Excelente: Muy buena bondad de ajuste")
        elif nse >= 0.7:
            logger.info("  Bueno: Buena bondad de ajuste")
        elif nse >= 0.5:
            logger.info("  Aceptable: Bondad de ajuste moderada")
        elif nse >= 0.0:
            logger.info("  Pobre: El modelo es peor que la media")
        else:
            logger.info("  Inaceptable: El modelo es peor que usar la media")
        
        logger.info("\n--- Interpretación KGE ---")
        if kge >= 0.9:
            logger.info("  Excelente: El modelo reproduce bien la dinámica")
        elif kge >= 0.7:
            logger.info("  Bueno: El modelo es aceptable")
        elif kge >= 0.5:
            logger.info("  Aceptable: El modelo tiene limitaciones")
        else:
            logger.info("  Inaceptable: El modelo necesita mejoras")
    
    def _save_results(self, results: Dict):
        """Guarda los resultados de la validación"""
        output_path = self.model_dir / 'validation_results.json'
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\nResultados guardados en: {output_path}")
    
    def cross_validate(
        self,
        n_splits: int = 5,
        sequence_length: int = 30
    ) -> Dict:
        """
        Realiza validación cruzada temporal.
        
        Args:
            n_splits: Número de particiones para validación cruzada
            sequence_length: Longitud de secuencia
            
        Returns:
            Diccionario con métricas promediadas
        """
        logger.info("=" * 60)
        logger.info(f"VALIDACIÓN CRUZADA TEMPORAL ({n_splits} pliegues)")
        logger.info("=" * 60)
        
        logger.info("Cargando datos...")
        
        caudal_path = self.data_dir / 'streamflow.csv'
        
        if caudal_path.exists():
            df = pd.read_csv(caudal_path, parse_dates=['date'])
        else:
            df = self._generate_synthetic_data()
        
        df = df.sort_values('date').reset_index(drop=True)
        df = df.ffill().bfill()
        
        if 'precipitation' not in df.columns:
            df['precipitation'] = np.random.exponential(10, len(df))
        if 'width' not in df.columns:
            df['width'] = 15 + np.random.normal(0, 2, len(df))
        
        df['month'] = df['date'].dt.month
        df['day_of_year'] = df['date'].dt.dayofyear
        df['sin_month'] = np.sin(2 * np.pi * df['month'] / 12)
        df['cos_month'] = np.cos(2 * np.pi * df['month'] / 12)
        df['sin_day'] = np.sin(2 * np.pi * df['day_of_year'] / 365)
        df['cos_day'] = np.cos(2 * np.pi * df['day_of_year'] / 365)
        
        feature_cols = ['caudal', 'precipitation', 'width',
                       'sin_month', 'cos_month', 'sin_day', 'cos_day']
        feature_cols = [c for c in feature_cols if c in df.columns]
        
        data = df[feature_cols].values
        
        if self.scaler is not None:
            data = self.scaler.transform(data)
        
        chunk_size = (len(data) - sequence_length) // n_splits
        
        all_metrics = []
        
        for i in range(n_splits):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size + sequence_length, len(data))
            
            test_start = start_idx + sequence_length
            test_end = end_idx
            
            if test_start >= len(data):
                continue
            
            X_test = []
            y_test = []
            
            for j in range(test_start, min(test_end, len(data))):
                X_test.append(data[j - sequence_length:j])
                y_test.append(data[j, 0])
            
            if len(X_test) == 0:
                continue
            
            X_test = np.array(X_test).reshape(-1, sequence_length, len(feature_cols))
            y_test = np.array(y_test)
            
            y_pred = self.model.predict(X_test, verbose=0).flatten()
            
            metrics = RegressionMetrics.calculate_all(y_test, y_pred)
            all_metrics.append(metrics)
            
            logger.info(f"\nPliegue {i + 1}/{n_splits}:")
            logger.info(f"  RMSE: {metrics['rmse']:.4f}")
            logger.info(f"  MAE: {metrics['mae']:.4f}")
            logger.info(f"  R²: {metrics['r2']:.4f}")
        
        avg_metrics = {}
        for key in all_metrics[0].keys():
            avg_metrics[key] = np.mean([m[key] for m in all_metrics])
            avg_metrics[f'{key}_std'] = np.std([m[key] for m in all_metrics])
        
        logger.info("\n" + "=" * 60)
        logger.info("RESULTADOS PROMEDIADOS")
        logger.info("=" * 60)
        logger.info(f"\nRMSE: {avg_metrics['rmse']:.4f} (+/- {avg_metrics['rmse_std']:.4f})")
        logger.info(f"MAE: {avg_metrics['mae']:.4f} (+/- {avg_metrics['mae_std']:.4f})")
        logger.info(f"R²: {avg_metrics['r2']:.4f} (+/- {avg_metrics['r2_std']:.4f})")
        
        return avg_metrics


def main():
    parser = argparse.ArgumentParser(
        description='Validación del modelo de predicción de caudales'
    )
    
    parser.add_argument(
        '--model-dir', type=str,
        default='../../data/models/caudal_predictor',
        help='Directorio del modelo'
    )
    parser.add_argument(
        '--data-dir', type=str,
        default='../../data/historical',
        help='Directorio de datos'
    )
    parser.add_argument(
        '--cross-validate', action='store_true',
        help='Ejecutar validación cruzada'
    )
    parser.add_argument(
        '--n-splits', type=int, default=5,
        help='Número de pliegues para validación cruzada'
    )
    
    args = parser.parse_args()
    
    validator = ValidationPipeline(
        model_dir=args.model_dir,
        data_dir=args.data_dir
    )
    
    if args.cross_validate:
        validator.cross_validate(n_splits=args.n_splits)
    else:
        metrics = validator.validate()
        
        if metrics:
            print("\n" + "=" * 60)
            print("MÉTRICAS FINALES")
            print("=" * 60)
            print(f"RMSE: {metrics['rmse']:.4f}")
            print(f"MAE:  {metrics['mae']:.4f}")
            print(f"R²:   {metrics['r2']:.4f}")
            print("=" * 60)


if __name__ == '__main__':
    main()
