"""
Caudal Predictor - Skyfusion Analytics
======================================

Script de entrenamiento para predicción de caudales utilizando redes LSTM.
Procesa datos históricos de caudal, precipitación y anchura del río.

Entrada:
- caudal_histórico (CSV)
- precipitación (CSV)
- anchura del río desde Vision Agent (CSV)

Arquitectura:
- LSTM (Long Short-Term Memory) con capas recurrentes
- Preprocesamiento con MinMaxScaler
- Validación temporal (sin shuffle)

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
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')

import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import (
    LSTM, Dense, Dropout, Input, Bidirectional,
    BatchNormalization, Attention, MultiHeadAttention,
    Flatten, Concatenate, GRU
)
from tensorflow.keras.callbacks import (
    EarlyStopping, ReduceLROnPlateau, ModelCheckpoint,
    TensorBoard, CSVLogger
)
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.regularizers import l2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Preprocesador de datos para el modelo LSTM"""
    
    def __init__(self):
        self.scalers: Dict[str, MinMaxScaler] = {}
        self.feature_columns: List[str] = []
        self.target_column: str = 'caudal'
        self.scaler_fitted: bool = False
    
    def load_data(
        self,
        caudal_path: str,
        precipitacion_path: Optional[str] = None,
        ancho_rio_path: Optional[str] = None,
        start_date: str = '1969-01-01',
        end_date: str = '2023-12-31'
    ) -> pd.DataFrame:
        """
        Carga y fusiona datos de múltiples fuentes.
        
        Args:
            caudal_path: Ruta al CSV de caudal histórico
            precipitacion_path: Ruta al CSV de precipitación (opcional)
            ancho_rio_path: Ruta al CSV de anchura del río (opcional)
            start_date: Fecha de inicio del análisis
            end_date: Fecha de fin del análisis
            
        Returns:
            DataFrame con datos fusionados
        """
        logger.info("Cargando datos históricos...")
        
        df_caudal = pd.read_csv(caudal_path, parse_dates=['date'])
        df_caudal = df_caudal.sort_values('date').reset_index(drop=True)
        
        if precipitacion_path and os.path.exists(precipitacion_path):
            df_precip = pd.read_csv(precipitacion_path, parse_dates=['date'])
            df_caudal = df_caudal.merge(df_precip, on='date', how='left')
            logger.info(f"  Precipitación fusionada: {len(df_precip)} registros")
        
        if ancho_rio_path and os.path.exists(ancho_rio_path):
            df_ancho = pd.read_csv(ancho_rio_path, parse_dates=['date'])
            df_caudal = df_caudal.merge(df_ancho, on='date', how='left')
            logger.info(f"  Anchura del río fusionada: {len(df_ancho)} registros")
        
        df_caudal = df_caudal[
            (df_caudal['date'] >= start_date) &
            (df_caudal['date'] <= end_date)
        ].copy()
        
        df_caudal = df_caudal.set_index('date')
        df_caudal = df_caudal.asfreq('D')
        df_caudal = df_caudal.ffill().bfill()
        df_caudal = df_caudal.reset_index()
        
        logger.info(f"Datos cargados: {len(df_caudal)} registros")
        logger.info(f"Rango temporal: {df_caudal['date'].min()} - {df_caudal['date'].max()}")
        
        return df_caudal
    
    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Maneja valores faltantes en el DataFrame"""
        logger.info("Manejando valores faltantes...")
        
        for col in df.columns:
            if col == 'date':
                continue
                
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                if missing_count / len(df) > 0.5:
                    logger.warning(f"  {col}: {missing_count} valores faltantes (>50%), eliminando columna")
                    df = df.drop(columns=[col])
                else:
                    df[col] = df[col].interpolate(method='linear')
                    df[col] = df[col].fillna(df[col].mean())
                    logger.info(f"  {col}: {missing_count} valores faltantes interpolados")
        
        return df
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Crea características temporales adicionales"""
        logger.info("Creando características temporales...")
        
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day'] = df['date'].dt.day
        df['day_of_year'] = df['date'].dt.dayofyear
        df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)
        df['quarter'] = df['date'].dt.quarter
        
        df['sin_month'] = np.sin(2 * np.pi * df['month'] / 12)
        df['cos_month'] = np.cos(2 * np.pi * df['month'] / 12)
        df['sin_day'] = np.sin(2 * np.pi * df['day_of_year'] / 365)
        df['cos_day'] = np.cos(2 * np.pi * df['day_of_year'] / 365)
        
        logger.info(f"  Features creadas: {len(df.columns) - 1}")
        
        return df
    
    def fit_scaler(self, data: np.ndarray):
        """Ajusta el escalador solo con datos de entrenamiento"""
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.scaler.fit(data)
        self.scaler_fitted = True
        logger.info("Escalador MinMaxScaler ajustado")
    
    def transform(self, data: np.ndarray) -> np.ndarray:
        """Transforma datos usando el escalador ajustado"""
        if not self.scaler_fitted:
            raise ValueError("El escalador no ha sido ajustado. Llamar a fit_scaler primero.")
        return self.scaler.transform(data)
    
    def inverse_transform(self, data: np.ndarray) -> np.ndarray:
        """Invierte la transformación de los datos"""
        if not self.scaler_fitted:
            raise ValueError("El escalador no ha sido ajustado.")
        return self.scaler.inverse_transform(data)
    
    def save_scaler(self, path: str):
        """Guarda el escalador para uso posterior"""
        import joblib
        joblib.dump(self.scaler, path)
        logger.info(f"Escalador guardado en: {path}")
    
    def load_scaler(self, path: str):
        """Carga un escalador previamente guardado"""
        import joblib
        self.scaler = joblib.load(path)
        self.scaler_fitted = True
        logger.info(f"Escalador cargado desde: {path}")


class LSTMModel:
    """Modelo LSTM para predicción de caudales"""
    
    def __init__(
        self,
        sequence_length: int = 30,
        n_features: int = 3,
        lstm_units: List[int] = [64, 64],
        dropout_rate: float = 0.2,
        learning_rate: float = 0.001,
        model_dir: str = '../../data/models/caudal_predictor'
    ):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.model: Optional[Sequential] = None
        self.history = None
    
    def build_model(self, architecture: str = 'stacked') -> Sequential:
        """
        Construye la arquitectura del modelo LSTM.
        
        Args:
            architecture: Tipo de arquitectura ('stacked', 'bidirectional', 'attention')
            
        Returns:
            Modelo Keras compilado
        """
        logger.info(f"Construyendo modelo LSTM ({architecture})...")
        
        if architecture == 'stacked':
            self.model = self._build_stacked_lstm()
        elif architecture == 'bidirectional':
            self.model = self._build_bidirectional_lstm()
        elif architecture == 'attention':
            self.model = self._build_lstm_with_attention()
        elif architecture == 'gru':
            self.model = self._build_gru_model()
        else:
            raise ValueError(f"Arquitectura desconocida: {architecture}")
        
        self.model.compile(
            optimizer=Adam(learning_rate=self.learning_rate),
            loss='mse',
            metrics=['mae', tf.keras.metrics.RootMeanSquaredError(name='rmse')]
        )
        
        logger.info(f"Modelo compilado: {self.model.summary()}")
        
        return self.model
    
    def _build_stacked_lstm(self) -> Sequential:
        """Arquitectura LSTM apilada (recomendada para datos de río)"""
        model = Sequential(name='LSTM_Stacked')
        
        model.add(Input(shape=(self.sequence_length, self.n_features)))
        
        for i, units in enumerate(self.lstm_units):
            return_seq = i < len(self.lstm_units) - 1
            model.add(LSTM(
                units,
                return_sequences=return_seq,
                kernel_regularizer=l2(0.001),
                recurrent_regularizer=l2(0.001),
                name=f'lstm_layer_{i+1}'
            ))
            model.add(BatchNormalization(name=f'bn_{i+1}'))
            model.add(Dropout(self.dropout_rate, name=f'dropout_{i+1}'))
        
        model.add(Dense(32, activation='relu', name='dense_1'))
        model.add(Dense(16, activation='relu', name='dense_2'))
        model.add(Dense(1, activation='linear', name='output'))
        
        return model
    
    def _build_bidirectional_lstm(self) -> Sequential:
        """Arquitectura LSTM Bidireccional"""
        model = Sequential(name='LSTM_Bidirectional')
        
        model.add(Input(shape=(self.sequence_length, self.n_features)))
        
        model.add(Bidirectional(
            LSTM(self.lstm_units[0], return_sequences=True),
            name='bidirectional_1'
        ))
        model.add(BatchNormalization(name='bn_1'))
        
        model.add(Bidirectional(
            LSTM(self.lstm_units[1] if len(self.lstm_units) > 1 else self.lstm_units[0]),
            return_sequences=False
        ))
        model.add(BatchNormalization(name='bn_2'))
        model.add(Dropout(self.dropout_rate))
        
        model.add(Dense(32, activation='relu'))
        model.add(Dense(1, activation='linear'))
        
        return model
    
    def _build_lstm_with_attention(self) -> Sequential:
        """Arquitectura LSTM con mecanismo de atención"""
        inputs = Input(shape=(self.sequence_length, self.n_features), name='input')
        
        lstm_out = LSTM(self.lstm_units[0], return_sequences=True)(inputs)
        lstm_out = BatchNormalization()(lstm_out)
        
        attention = MultiHeadAttention(
            num_heads=4,
            key_dim=self.lstm_units[0] // 4,
            name='multi_head_attention'
        )(lstm_out, lstm_out)
        
        attention_out = tf.keras.layers.Add()([lstm_out, attention])
        attention_out = tf.keras.layers.LayerNormalization()(attention_out)
        
        context = tf.keras.layers.GlobalAveragePooling1D()(attention_out)
        
        dense = Dense(64, activation='relu')(context)
        dense = Dropout(self.dropout_rate)(dense)
        dense = Dense(32, activation='relu')(dense)
        
        output = Dense(1, activation='linear', name='output')(dense)
        
        model = Model(inputs=inputs, outputs=output, name='LSTM_Attention')
        
        return model
    
    def _build_gru_model(self) -> Sequential:
        """Arquitectura alternativa con GRU (más rápido)"""
        model = Sequential(name='GRU_Model')
        
        model.add(Input(shape=(self.sequence_length, self.n_features)))
        
        model.add(GRU(64, return_sequences=True))
        model.add(GRU(32))
        model.add(BatchNormalization())
        model.add(Dropout(self.dropout_rate))
        
        model.add(Dense(32, activation='relu'))
        model.add(Dense(1, activation='linear'))
        
        return model
    
    def get_callbacks(self, monitor: str = 'val_loss') -> List:
        """Obtiene callbacks para el entrenamiento"""
        callbacks = [
            EarlyStopping(
                monitor=monitor,
                patience=15,
                restore_best_weights=True,
                verbose=1
            ),
            ReduceLROnPlateau(
                monitor=monitor,
                factor=0.5,
                patience=5,
                min_lr=1e-6,
                verbose=1
            ),
            ModelCheckpoint(
                filepath=str(self.model_dir / 'best_model.keras'),
                monitor=monitor,
                save_best_only=True,
                verbose=1
            ),
            CSVLogger(
                filename=str(self.model_dir / 'training_log.csv'),
                separator=',',
                append=False
            )
        ]
        
        return callbacks
    
    def create_sequences(
        self,
        data: np.ndarray,
        seq_length: Optional[int] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Crea secuencias para entrenamiento/predicción.
        
        Args:
            data: Datos normalizados
            seq_length: Longitud de secuencia (usa self.sequence_length si es None)
            
        Returns:
            Tuple de (X, y) donde X tiene forma (samples, seq_length, features)
            e y tiene forma (samples,) para predicción de caudal
        """
        seq_length = seq_length or self.sequence_length
        
        X, y = [], []
        
        for i in range(seq_length, len(data)):
            X.append(data[i - seq_length:i])
            y.append(data[i, 0])
        
        return np.array(X), np.array(y)
    
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        epochs: int = 100,
        batch_size: int = 32,
        validation_split: float = 0.0,
        monitor: str = 'val_loss'
    ) -> tf.keras.callbacks.History:
        """
        Entrena el modelo.
        
        Args:
            X_train: Datos de entrenamiento
            y_train: Labels de entrenamiento
            X_val: Datos de validación
            y_val: Labels de validación
            epochs: Número de épocas
            batch_size: Tamaño de batch
            validation_split: Proporción de datos para validación (alternativo a X_val)
            monitor: Métrica a monitorear
            
        Returns:
            Historia del entrenamiento
        """
        if self.model is None:
            self.build_model()
        
        logger.info(f"Iniciando entrenamiento...")
        logger.info(f"  Datos de entrenamiento: {X_train.shape}")
        logger.info(f"  Datos de validación: {X_val.shape}")
        logger.info(f"  Épocas: {epochs}")
        logger.info(f"  Batch size: {batch_size}")
        
        if tf.config.list_physical_devices('GPU'):
            logger.info("  Dispositivo: GPU")
        else:
            logger.info("  Dispositivo: CPU")
        
        callbacks = self.get_callbacks(monitor)
        
        validation_data = (X_val, y_val) if len(X_val) > 0 else None
        
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        logger.info("Entrenamiento completado")
        
        return self.history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Realiza predicciones"""
        if self.model is None:
            raise ValueError("El modelo no ha sido entrenado")
        return self.model.predict(X, verbose=0)
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Evalúa el modelo"""
        if self.model is None:
            raise ValueError("El modelo no ha sido entrenado")
        
        results = self.model.evaluate(X, y, verbose=0)
        
        return {
            'loss': float(results[0]),
            'mae': float(results[1]),
            'rmse': float(results[2]) if len(results) > 2 else float(np.sqrt(results[0]))
        }
    
    def save_model(self, filename: str = 'caudal_lstm_model.keras'):
        """Guarda el modelo"""
        if self.model is None:
            raise ValueError("No hay modelo para guardar")
        
        model_path = self.model_dir / filename
        self.model.save(model_path)
        
        config = {
            'sequence_length': self.sequence_length,
            'n_features': self.n_features,
            'lstm_units': self.lstm_units,
            'dropout_rate': self.dropout_rate,
            'learning_rate': self.learning_rate,
            'saved_at': datetime.now().isoformat()
        }
        
        config_path = self.model_dir / 'model_config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Modelo guardado en: {model_path}")
    
    def load_model(self, filename: str = 'caudal_lstm_model.keras'):
        """Carga un modelo guardado"""
        model_path = self.model_dir / filename
        config_path = self.model_dir / 'model_config.json'
        
        if not model_path.exists():
            raise FileNotFoundError(f"Modelo no encontrado: {model_path}")
        
        self.model = tf.keras.models.load_model(model_path)
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.sequence_length = config['sequence_length']
                self.n_features = config['n_features']
        
        logger.info(f"Modelo cargado desde: {model_path}")


class CaudalPredictorPipeline:
    """Pipeline completo para predicción de caudales"""
    
    def __init__(
        self,
        model_dir: str = '../../data/models/caudal_predictor',
        data_dir: str = '../../data/historical'
    ):
        self.model_dir = Path(model_dir)
        self.data_dir = Path(data_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.preprocessor = DataPreprocessor()
        self.model: Optional[LSTMModel] = None
        self.training_history = None
    
    def load_and_prepare_data(
        self,
        start_date: str = '1969-01-01',
        end_date: str = '2023-12-31'
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, MinMaxScaler]:
        """
        Carga y prepara los datos para entrenamiento.
        
        Returns:
            Tuple de (X_train, y_train, X_val, y_val, scaler)
        """
        logger.info("=" * 60)
        logger.info("FASE 1: CARGA Y PREPARACIÓN DE DATOS")
        logger.info("=" * 60)
        
        caudal_path = self.data_dir / 'streamflow.csv'
        precipitacion_path = self.data_dir / 'precipitation.csv'
        ancho_rio_path = self.data_dir / 'river_width.csv'
        
        if not caudal_path.exists():
            logger.warning(f"Archivo de caudal no encontrado: {caudal_path}")
            logger.info("Generando datos sintéticos para demostración...")
            df = self._generate_synthetic_data(start_date, end_date)
        else:
            df = self.preprocessor.load_data(
                str(caudal_path),
                str(precipitacion_path) if precipitacion_path.exists() else None,
                str(ancho_rio_path) if ancho_rio_path.exists() else None,
                start_date,
                end_date
            )
        
        df = self.preprocessor.handle_missing_values(df)
        df = self.preprocessor.create_features(df)
        
        feature_cols = ['caudal', 'precipitation', 'width', 
                       'sin_month', 'cos_month', 'sin_day', 'cos_day']
        feature_cols = [c for c in feature_cols if c in df.columns]
        
        logger.info(f"Features utilizadas: {feature_cols}")
        
        data = df[feature_cols].values
        
        train_end = int(len(data) * 0.7)
        val_end = int(len(data) * 0.85)
        
        train_data = data[:train_end]
        val_data = data[train_end:val_end]
        test_data = data[val_end:]
        
        logger.info(f"Datos de entrenamiento: {len(train_data)}")
        logger.info(f"Datos de validación: {len(val_data)}")
        logger.info(f"Datos de prueba: {len(test_data)}")
        
        self.preprocessor.fit_scaler(train_data)
        
        train_scaled = self.preprocessor.transform(train_data)
        val_scaled = self.preprocessor.transform(val_data)
        test_scaled = self.preprocessor.transform(test_data)
        
        X_train, y_train = self.preprocessor.create_sequences(train_scaled, 30)
        X_val, y_val = self.preprocessor.create_sequences(val_scaled, 30)
        X_test, y_test = self.preprocessor.create_sequences(test_scaled, 30)
        
        X_train = X_train.reshape((X_train.shape[0], 30, len(feature_cols)))
        X_val = X_val.reshape((X_val.shape[0], 30, len(feature_cols)))
        X_test = X_test.reshape((X_test.shape[0], 30, len(feature_cols)))
        
        logger.info(f"Formas finales:")
        logger.info(f"  X_train: {X_train.shape}")
        logger.info(f"  X_val: {X_val.shape}")
        logger.info(f"  X_test: {X_test.shape}")
        
        self.preprocessor.save_scaler(str(self.model_dir / 'scaler.save'))
        
        return X_train, y_train, X_val, y_val, X_test, y_test, feature_cols
    
    def _generate_synthetic_data(
        self,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """Genera datos sintéticos para demostración"""
        logger.info("Generando datos sintéticos...")
        
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        n = len(dates)
        
        np.random.seed(42)
        
        base_caudal = 50.0
        seasonal = 20.0 * np.sin(2 * np.pi * np.arange(n) / 365)
        trend = np.linspace(0, 5, n)
        noise = np.random.normal(0, 5, n)
        caudal = base_caudal + seasonal + trend + noise
        caudal = np.clip(caudal, 5, 150)
        
        precipitation = np.random.exponential(10, n)
        precipitation = np.clip(precipitation, 0, 100)
        
        river_width = 15.0 + 5.0 * np.sin(2 * np.pi * np.arange(n) / 365) + \
                     0.3 * (caudal - base_caudal) + np.random.normal(0, 2, n)
        river_width = np.clip(river_width, 5, 50)
        
        df = pd.DataFrame({
            'date': dates,
            'caudal': caudal,
            'precipitation': precipitation,
            'width': river_width
        })
        
        return df
    
    def train(
        self,
        architecture: str = 'stacked',
        sequence_length: int = 30,
        lstm_units: List[int] = [64, 64],
        epochs: int = 100,
        batch_size: int = 32
    ) -> Dict:
        """
        Ejecuta el pipeline de entrenamiento completo.
        
        Returns:
            Diccionario con resultados
        """
        logger.info("=" * 60)
        logger.info("PIPELINE DE ENTRENAMIENTO CAUDAL PREDICTOR")
        logger.info("=" * 60)
        
        X_train, y_train, X_val, y_val, X_test, y_test, feature_cols = \
            self.load_and_prepare_data()
        
        self.model = LSTMModel(
            sequence_length=sequence_length,
            n_features=len(feature_cols),
            lstm_units=lstm_units,
            model_dir=str(self.model_dir)
        )
        
        logger.info("=" * 60)
        logger.info("FASE 2: ENTRENAMIENTO DEL MODELO LSTM")
        logger.info("=" * 60)
        
        self.model.build_model(architecture)
        self.training_history = self.model.train(
            X_train, y_train,
            X_val, y_val,
            epochs=epochs,
            batch_size=batch_size
        )
        
        logger.info("=" * 60)
        logger.info("FASE 3: EVALUACIÓN")
        logger.info("=" * 60)
        
        train_metrics = self.model.evaluate(X_train, y_train)
        val_metrics = self.model.evaluate(X_val, y_val)
        test_metrics = self.model.evaluate(X_test, y_test)
        
        logger.info("\nMétricas de entrenamiento:")
        for key, value in train_metrics.items():
            logger.info(f"  {key}: {value:.4f}")
        
        logger.info("\nMétricas de validación:")
        for key, value in val_metrics.items():
            logger.info(f"  {key}: {value:.4f}")
        
        logger.info("\nMétricas de prueba:")
        for key, value in test_metrics.items():
            logger.info(f"  {key}: {value:.4f}")
        
        self.model.save_model()
        
        results = {
            'architecture': architecture,
            'sequence_length': sequence_length,
            'lstm_units': lstm_units,
            'train_metrics': train_metrics,
            'val_metrics': val_metrics,
            'test_metrics': test_metrics,
            'feature_columns': feature_cols,
            'training_history': self.training_history.history if self.training_history else None
        }
        
        self._save_results(results)
        
        logger.info("=" * 60)
        logger.info("ENTRENAMIENTO COMPLETADO")
        logger.info("=" * 60)
        
        return results
    
    def _save_results(self, results: Dict):
        """Guarda los resultados del entrenamiento"""
        results_to_save = {
            'architecture': results['architecture'],
            'sequence_length': results['sequence_length'],
            'lstm_units': results['lstm_units'],
            'train_metrics': results['train_metrics'],
            'val_metrics': results['val_metrics'],
            'test_metrics': results['test_metrics'],
            'feature_columns': results['feature_columns'],
            'timestamp': datetime.now().isoformat()
        }
        
        results_path = self.model_dir / 'training_results.json'
        with open(results_path, 'w') as f:
            json.dump(results_to_save, f, indent=2)
        
        logger.info(f"Resultados guardados en: {results_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Entrenamiento de modelo LSTM para predicción de caudales'
    )
    
    parser.add_argument(
        '--architecture', type=str, default='stacked',
        choices=['stacked', 'bidirectional', 'attention', 'gru'],
        help='Arquitectura del modelo LSTM'
    )
    parser.add_argument(
        '--sequence-length', type=int, default=30,
        help='Longitud de secuencia (días)'
    )
    parser.add_argument(
        '--lstm-units', type=str, default='64,64',
        help='Unidades LSTM (separadas por coma)'
    )
    parser.add_argument(
        '--epochs', type=int, default=100,
        help='Número de épocas'
    )
    parser.add_argument(
        '--batch-size', type=int, default=32,
        help='Tamaño de batch'
    )
    parser.add_argument(
        '--start-date', type=str, default='1969-01-01',
        help='Fecha de inicio'
    )
    parser.add_argument(
        '--end-date', type=str, default='2023-12-31',
        help='Fecha de fin'
    )
    parser.add_argument(
        '--model-dir', type=str, default='../../data/models/caudal_predictor',
        help='Directorio del modelo'
    )
    parser.add_argument(
        '--data-dir', type=str, default='../../data/historical',
        help='Directorio de datos'
    )
    
    args = parser.parse_args()
    
    lstm_units = [int(x) for x in args.lstm_units.split(',')]
    
    pipeline = CaudalPredictorPipeline(
        model_dir=args.model_dir,
        data_dir=args.data_dir
    )
    
    results = pipeline.train(
        architecture=args.architecture,
        sequence_length=args.sequence_length,
        lstm_units=lstm_units,
        epochs=args.epochs,
        batch_size=args.batch_size
    )
    
    print("\n" + "=" * 60)
    print("RESUMEN DEL ENTRENAMIENTO")
    print("=" * 60)
    print(f"Arquitectura: {results['architecture']}")
    print(f"Secuencia: {results['sequence_length']} días")
    print(f"Features: {results['feature_columns']}")
    print(f"\nMétricas de prueba:")
    print(f"  Loss (MSE): {results['test_metrics']['loss']:.4f}")
    print(f"  MAE: {results['test_metrics']['mae']:.4f}")
    print(f"  RMSE: {results['test_metrics']['rmse']:.4f}")


if __name__ == '__main__':
    main()
