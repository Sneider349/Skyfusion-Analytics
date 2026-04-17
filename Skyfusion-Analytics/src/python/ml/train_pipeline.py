"""
Pipeline de Entrenamiento para Predicción de Extensión de Agua
Skyfusion Analytics

Pipeline completo para:
1. Generación de dataset (sintético o desde GEE)
2. Entrenamiento del modelo CNN-LSTM-Attention
3. Evaluación y validación
4. Exportación para inferencia
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import sys
sys.path.append(str(Path(__file__).parent))

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import tensorflow as tf

from data_generator import WaterDatasetGenerator, DatasetConfig, COMBEIMA_CONFIG
from water_extension_model import WaterExtensionModel


class TrainingPipeline:
    """
    Pipeline completo de entrenamiento para predicción de extensión de agua.
    """
    
    def __init__(
        self,
        output_dir: str = '../../data/training',
        model_dir: str = '../../data/models'
    ):
        self.output_dir = Path(output_dir)
        self.model_dir = Path(model_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.dataset_generator = None
        self.model = None
        self.training_history = None
        
    def generate_dataset(
        self,
        n_samples: int = 1000,
        use_synthetic: bool = True,
        start_date: str = '2020-01-01',
        end_date: str = '2025-12-31'
    ) -> Dict[str, np.ndarray]:
        """
        Genera dataset para entrenamiento.
        
        Args:
            n_samples: Número de muestras (para datos sintéticos)
            use_synthetic: Si usar datos sintéticos o GEE
            start_date: Fecha inicio (para GEE)
            end_date: Fecha fin (para GEE)
            
        Returns:
            Diccionario con datos
        """
        print('\n' + '='*60)
        print('FASE 1: GENERACIÓN DE DATASET')
        print('='*60)
        
        if use_synthetic:
            print('Generando dataset sintético...')
            self.dataset_generator = WaterDatasetGenerator()
            data = self.dataset_generator.generate_synthetic_dataset(
                n_samples=n_samples
            )
            dataset_name = 'water_extension_synthetic'
        else:
            print('Conectando a Google Earth Engine...')
            self.dataset_generator = WaterDatasetGenerator(
                catchment=COMBEIMA_CONFIG
            )
            
            service_account = os.getenv('GEE_SERVICE_ACCOUNT')
            private_key = os.getenv('GEE_PRIVATE_KEY_PATH')
            
            if service_account and private_key:
                self.dataset_generator.initialize_gee(
                    service_account,
                    private_key
                )
                
                print(f'Extrayendo datos desde {start_date} hasta {end_date}...')
                time_series = self.dataset_generator.extract_time_series(
                    start_date,
                    end_date
                )
                
                data = self.dataset_generator.prepare_gee_dataset(time_series)
                dataset_name = 'water_extension_gee'
            else:
                print('GEE no configurado. Usando datos sintéticos...')
                return self.generate_dataset(n_samples, use_synthetic=True)
        
        print(f'\nDataset generado:')
        print(f'  - Muestras: {len(data["y_water_mask"])}')
        print(f'  - Features satelitales: {data["X_satellite"].shape}')
        print(f'  - Features climáticas: {data["X_climate"].shape}')
        print(f'  - Máscaras de agua: {data["y_water_mask"].shape}')
        
        if self.dataset_generator:
            self.dataset_generator.save_dataset(data, dataset_name)
        
        return data
    
    def prepare_training_data(
        self,
        data: Dict[str, np.ndarray],
        horizon: int = 7
    ) -> Tuple[Dict, np.ndarray, Dict, np.ndarray, Dict, np.ndarray]:
        """
        Prepara datos para entrenamiento.
        
        Args:
            data: Dataset completo
            horizon: Horizonte de predicción
            
        Returns:
            Tupla de (X_train, y_train, X_val, y_val, X_test, y_test)
        """
        print(f'\nPreparando datos para horizonte {horizon} días...')
        
        X, y = self.dataset_generator.prepare_sequences(data, horizon)
        X_train, X_val, X_test, y_train, y_val, y_test = \
            self.dataset_generator.split_dataset(X, y)
        
        print(f'  - Entrenamiento: {len(y_train)} muestras')
        print(f'  - Validación: {len(y_val)} muestras')
        print(f'  - Prueba: {len(y_test)} muestras')
        
        print(f'\nFormas de datos:')
        print(f'  X_train[satellite]: {X_train["satellite_input"].shape}')
        print(f'  X_train[climate]: {X_train["climate_input"].shape}')
        print(f'  X_train[static]: {X_train["static_input"].shape}')
        print(f'  y_train: {y_train.shape}')
        
        return X_train, y_train, X_val, y_val, X_test, y_test
    
    def train_model(
        self,
        X_train: Dict[str, np.ndarray],
        y_train: np.ndarray,
        X_val: Dict[str, np.ndarray],
        y_val: np.ndarray,
        horizon: int = 7,
        epochs: int = 50,
        batch_size: int = 8,
        use_class_weights: bool = True
    ) -> WaterExtensionModel:
        """
        Entrena el modelo para un horizonte específico.
        
        Args:
            X_train: Datos de entrenamiento
            y_train: Labels de entrenamiento
            X_val: Datos de validación
            y_val: Labels de validación
            horizon: Horizonte de predicción
            epochs: Número de épocas
            batch_size: Tamaño de batch
            use_class_weights: Si usar pesos de clase
            
        Returns:
            Modelo entrenado
        """
        print('\n' + '='*60)
        print(f'FASE 2: ENTRENAMIENTO (HORIZONTE {horizon} DÍAS)')
        print('='*60)
        
        self.model = WaterExtensionModel(
            sequence_length=10,
            patch_size=64,
            horizons=[horizon],
            model_path=str(self.model_dir)
        )
        
        self.model.build_model()
        
        if use_class_weights:
            class_weights = self.model.compute_class_weights(y_train)
            print(f'\nPesos de clase: {class_weights}')
        
        print(f'\nIniciando entrenamiento...')
        print(f'  - Épocas: {epochs}')
        print(f'  - Batch size: {batch_size}')
        print(f'  - Dispositivo: GPU' if len(tf.config.list_physical_devices('GPU')) > 0 else '  - Dispositivo: CPU')
        
        self.training_history = self.model.train(
            X_train,
            y_train,
            X_val,
            y_val,
            epochs=epochs,
            batch_size=batch_size,
            model_name=f'water_extension_h{horizon}',
            use_class_weights=use_class_weights
        )
        
        return self.model
    
    def evaluate_model(
        self,
        X_test: Dict[str, np.ndarray],
        y_test: np.ndarray,
        horizon: int = 7
    ) -> Dict[str, float]:
        """
        Evalúa el modelo en datos de prueba.
        
        Args:
            X_test: Datos de prueba
            y_test: Labels de prueba
            horizon: Horizonte evaluado
            
        Returns:
            Diccionario con métricas
        """
        print('\n' + '='*60)
        print(f'FASE 3: EVALUACIÓN (HORIZONTE {horizon} DÍAS)')
        print('='*60)
        
        if self.model is None:
            raise ValueError('Modelo no entrenado')
        
        metrics = self.model.evaluate(X_test, y_test)
        
        print('\nMétricas de evaluación:')
        print(f'  - Loss: {metrics.get("loss", "N/A"):.4f}')
        print(f'  - Binary Accuracy: {metrics.get("binary_accuracy", "N/A"):.4f}')
        print(f'  - IoU (Mean): {metrics.get("iou", "N/A"):.4f}')
        print(f'  - Precision: {metrics.get("precision", "N/A"):.4f}')
        print(f'  - Recall: {metrics.get("recall", "N/A"):.4f}')
        print(f'  - AUC: {metrics.get("auc", "N/A"):.4f}')
        print(f'  - Water IoU: {metrics.get("water_iou", "N/A"):.4f}')
        
        print('\nDistribución de clases:')
        print(f'  - TP (True Positives): {metrics.get("true_positives", "N/A")}')
        print(f'  - TN (True Negatives): {metrics.get("true_negatives", "N/A")}')
        print(f'  - FP (False Positives): {metrics.get("false_positives", "N/A")}')
        print(f'  - FN (False Negatives): {metrics.get("false_negatives", "N/A")}')
        
        return metrics
    
    def run_full_pipeline(
        self,
        n_samples: int = 1000,
        horizons: List[int] = None,
        epochs: int = 50,
        batch_size: int = 8,
        use_synthetic: bool = True
    ) -> Dict[int, Dict]:
        """
        Ejecuta pipeline completo de entrenamiento.
        
        Args:
            n_samples: Número de muestras
            horizons: Lista de horizontes [7, 14, 30]
            epochs: Épocas por horizonte
            batch_size: Tamaño de batch
            use_synthetic: Si usar datos sintéticos
            
        Returns:
            Diccionario con resultados por horizonte
        """
        horizons = horizons or [7, 14, 30]
        
        print('\n' + '#'*60)
        print('# SKYFUSION ANALYTICS - PIPELINE DE ENTRENAMIENTO')
        print('# Predicción de Extensión de Agua (CNN-LSTM-Attention)')
        print('#'*60)
        
        start_time = datetime.now()
        
        data = self.generate_dataset(
            n_samples=n_samples,
            use_synthetic=use_synthetic
        )
        
        results = {}
        
        for horizon in horizons:
            X_train, y_train, X_val, y_val, X_test, y_test = \
                self.prepare_training_data(data, horizon)
            
            self.train_model(
                X_train, y_train,
                X_val, y_val,
                horizon=horizon,
                epochs=epochs,
                batch_size=batch_size
            )
            
            metrics = self.evaluate_model(X_test, y_test, horizon)
            
            results[horizon] = {
                'metrics': metrics,
                'training_time': str(datetime.now() - start_time)
            }
        
        self._save_training_report(results, start_time)
        
        print('\n' + '#'*60)
        print('# ENTRENAMIENTO COMPLETADO')
        print(f'# Tiempo total: {datetime.now() - start_time}')
        print('#'*60)
        
        return results
    
    def _save_training_report(
        self,
        results: Dict,
        start_time: datetime
    ):
        """Guarda reporte de entrenamiento."""
        report = {
            'training_start': start_time.isoformat(),
            'training_end': datetime.now().isoformat(),
            'duration': str(datetime.now() - start_time),
            'results': results
        }
        
        report_path = self.output_dir / 'training_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f'\nReporte guardado en {report_path}')


def main():
    parser = argparse.ArgumentParser(
        description='Pipeline de entrenamiento para predicción de extensión de agua'
    )
    
    parser.add_argument(
        '--samples', type=int, default=1000,
        help='Número de muestras (default: 1000)'
    )
    parser.add_argument(
        '--epochs', type=int, default=50,
        help='Número de épocas (default: 50)'
    )
    parser.add_argument(
        '--batch', type=int, default=8,
        help='Tamaño de batch (default: 8)'
    )
    parser.add_argument(
        '--horizons', type=str, default='7,14,30',
        help='Horizontes de predicción (default: 7,14,30)'
    )
    parser.add_argument(
        '--use-real', action='store_true',
        help='Usar datos reales de GEE (requiere configuración)'
    )
    parser.add_argument(
        '--evaluate-only', action='store_true',
        help='Solo evaluar modelo existente'
    )
    parser.add_argument(
        '--model-name', type=str, default='water_extension_model',
        help='Nombre del modelo a evaluar'
    )
    
    args = parser.parse_args()
    
    horizons = [int(h) for h in args.horizons.split(',')]
    
    pipeline = TrainingPipeline()
    
    if args.evaluate_only:
        print(f'Evaluando modelo: {args.model_name}')
        
        model = WaterExtensionModel(model_path='../../data/models')
        model.load_model(args.model_name)
        
        data = model.dataset_generator.generate_synthetic_dataset(n_samples=200)
        X_test, y_test = model.prepare_sequences(data, horizon=7)
        X_train, y_train, X_val, y_val, X_test, y_test = \
            model.split_dataset(X_test, y_test)
        
        metrics = model.evaluate(X_test, y_test)
        
        print('\nMétricas finales:')
        for key, value in metrics.items():
            print(f'  {key}: {value}')
    else:
        results = pipeline.run_full_pipeline(
            n_samples=args.samples,
            horizons=horizons,
            epochs=args.epochs,
            batch_size=args.batch,
            use_synthetic=not args.use_real
        )


if __name__ == '__main__':
    main()
