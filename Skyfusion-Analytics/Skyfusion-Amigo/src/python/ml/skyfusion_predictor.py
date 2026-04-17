"""
Modelo Predictivo Skyfusion Analytics
Red neuronal LSTM con atención para predicción de caudales y alertas
"""

import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, List, Optional
from datetime import datetime, timedelta

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import tensorflow as tf
from tensorflow.keras import layers, models, optimizers, callbacks
from tensorflow.keras.preprocessing.sequence import TimeseriesGenerator
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.model_selection import TimeSeriesSplit


class EnvironmentalDataPreprocessor:
    """Preprocesador de datos ambientales"""
    
    def __init__(self):
        self.scalers: Dict[str, MinMaxScaler] = {}
        self.feature_scaler = StandardScaler()
        
    def fit(self, data: pd.DataFrame, features: List[str]):
        for feature in features:
            scaler = MinMaxScaler()
            scaler.fit(data[feature].values.reshape(-1, 1))
            self.scalers[feature] = scaler
            
        self.feature_scaler.fit(data[features].values)
        
    def transform(self, data: pd.DataFrame, features: List[str]) -> np.ndarray:
        scaled = self.feature_scaler.transform(data[features].values)
        return scaled
    
    def inverse_transform(self, scaled_data: np.ndarray, feature: str) -> np.ndarray:
        return self.scalers[feature].inverse_transform(scaled_data)


class SkyfusionPredictor:
    """
    Modelo predictivo para alertas de inundación y sequía
    """
    
    def __init__(self, input_features: int = 5, sequence_length: int = 7,
                 output_features: int = 4, model_path: str = "../../data/models"):
        self.input_features = input_features
        self.sequence_length = sequence_length
        self.output_features = output_features
        self.model_path = Path(model_path)
        self.model_path.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.preprocessor = EnvironmentalDataPreprocessor()
        
    def build_model(self) -> models.Model:
        """
        Construye la arquitectura de la red neuronal
        
        Returns:
            Modelo Keras compilado
        """
        inputs = layers.Input(shape=(self.sequence_length, self.input_features))
        
        x = layers.Dense(256, activation='relu')(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        
        x = layers.Dense(128, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        
        x = layers.Dense(64, activation='relu')(x)
        
        x = layers.LSTM(64, return_sequences=True)(x)
        
        attention = layers.MultiHeadAttention(
            num_heads=4, key_dim=64, dropout=0.2
        )(x, x)
        
        x = layers.Add()([x, attention])
        x = layers.GlobalAveragePooling1D()(x)
        
        outputs = layers.Dense(self.output_features, activation='linear')(x)
        
        model = models.Model(inputs=inputs, outputs=outputs, name='SkyfusionPredictor')
        
        model.compile(
            optimizer=optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae', 'mse']
        )
        
        self.model = model
        return model
    
    def prepare_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepara secuencias para entrenamiento
        
        Args:
            data: Array de features escaladas
            
        Returns:
            Tuple de (X, y)
        """
        X, y = [], []
        
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:i + self.sequence_length])
            y.append(data[i + self.sequence_length])
            
        return np.array(X), np.array(y)
    
    def train(self, data: pd.DataFrame, features: List[str],
              epochs: int = 100, batch_size: int = 32,
              validation_split: float = 0.2) -> Dict:
        """
        Entrena el modelo
        
        Args:
            data: DataFrame con datos históricos
            features: Lista de features a usar
            epochs: Número de épocas
            batch_size: Tamaño de batch
            validation_split: Proporción de validación
            
        Returns:
            Historia del entrenamiento
        """
        self.preprocessor.fit(data, features)
        
        scaled_data = self.preprocessor.transform(data, features)
        
        X, y = self.prepare_sequences(scaled_data)
        
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        if self.model is None:
            self.build_model()
            
        early_stop = callbacks.EarlyStopping(
            monitor='val_loss',
            patience=15,
            restore_best_weights=True
        )
        
        reduce_lr = callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=0.0001
        )
        
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stop, reduce_lr],
            verbose=1
        )
        
        return history.history
    
    def predict(self, input_sequence: np.ndarray) -> Dict[str, float]:
        """
        Realiza predicción
        
        Args:
            input_sequence: Secuencia de entrada
            
        Returns:
            Diccionario con predicciones
        """
        if self.model is None:
            raise ValueError("El modelo no ha sido entrenado")
            
        prediction = self.model.predict(input_sequence, verbose=0)[0]
        
        output_names = ['caudal_predicted', 'flood_probability', 
                       'drought_probability', 'alert_level']
        
        results = {}
        for i, name in enumerate(output_names):
            if name == 'alert_level':
                results[name] = int(np.clip(prediction[i] * 3, 0, 3))
            else:
                results[name] = float(prediction[i])
                
        return results
    
    def predict_streamflow(self, data: pd.DataFrame, features: List[str],
                           horizon_days: int = 7) -> pd.DataFrame:
        """
        Predice caudales para múltiples días
        
        Args:
            data: Datos históricos
            features: Features a usar
            horizon_days: Días a predecir
            
        Returns:
            DataFrame con predicciones
        """
        if self.model is None:
            raise ValueError("El modelo no ha sido entrenado")
            
        scaled_data = self.preprocessor.transform(data, features)
        
        predictions = []
        current_sequence = scaled_data[-self.sequence_length:].reshape(1, self.sequence_length, -1)
        
        for day in range(horizon_days):
            pred = self.model.predict(current_sequence, verbose=0)[0]
            
            predictions.append({
                'day': day + 1,
                'caudal': pred[0],
                'flood_prob': pred[1],
                'drought_prob': pred[2],
                'alert': int(np.clip(pred[3] * 3, 0, 3))
            })
            
            new_row = pred.reshape(1, -1)
            current_sequence = np.concatenate([
                current_sequence[:, 1:, :],
                new_row.reshape(1, 1, -1)
            ], axis=1)
            
        return pd.DataFrame(predictions)
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """
        Evalúa el modelo
        
        Args:
            X_test: Datos de prueba
            y_test: Labels de prueba
            
        Returns:
            Métricas de evaluación
        """
        if self.model is None:
            raise ValueError("El modelo no ha sido entrenado")
            
        results = self.model.evaluate(X_test, y_test, verbose=0)
        
        return {
            'loss': float(results[0]),
            'mae': float(results[1]),
            'mse': float(results[2])
        }
    
    def save_model(self, filename: str = "skyfusion_model"):
        """
        Guarda el modelo
        
        Args:
            filename: Nombre del archivo
        """
        if self.model is None:
            raise ValueError("No hay modelo para guardar")
            
        model_file = self.model_path / f"{filename}.h5"
        self.model.save(model_file)
        
        config = {
            'input_features': self.input_features,
            'sequence_length': self.sequence_length,
            'output_features': self.output_features,
            'saved_at': datetime.now().isoformat()
        }
        
        config_file = self.model_path / f"{filename}_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
            
    def load_model(self, filename: str = "skyfusion_model"):
        """
        Carga un modelo guardado
        
        Args:
            filename: Nombre del archivo
        """
        model_file = self.model_path / f"{filename}.h5"
        config_file = self.model_path / f"{filename}_config.json"
        
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        self.input_features = config['input_features']
        self.sequence_length = config['sequence_length']
        self.output_features = config['output_features']
        
        self.model = models.load_model(model_file)


def generate_sample_data(n_days: int = 365 * 3) -> pd.DataFrame:
    """
    Genera datos de ejemplo para pruebas
    
    Args:
        n_days: Número de días
        
    Returns:
        DataFrame con datos sintéticos
    """
    np.random.seed(42)
    
    dates = pd.date_range(start='2020-01-01', periods=n_days, freq='D')
    
    base_caudal = 4.5
    seasonal = 1.5 * np.sin(2 * np.pi * np.arange(n_days) / 365)
    trend = np.linspace(0, 0.5, n_days)
    noise = np.random.normal(0, 0.3, n_days)
    
    caudal = base_caudal + seasonal + trend + noise
    caudal = np.clip(caudal, 0.5, 10)
    
    precipitation = np.random.exponential(5, n_days)
    precipitation = np.clip(precipitation, 0, 50)
    
    temperature = 22 + 5 * np.sin(2 * np.pi * np.arange(n_days) / 365) + np.random.normal(0, 2, n_days)
    
    humidity = 70 + 15 * np.sin(2 * np.pi * np.arange(n_days) / 365 + np.pi) + np.random.normal(0, 5, n_days)
    humidity = np.clip(humidity, 30, 100)
    
    ndvi = 0.5 + 0.2 * np.sin(2 * np.pi * np.arange(n_days) / 365) + np.random.normal(0, 0.1, n_days)
    ndvi = np.clip(ndvi, 0, 1)
    
    return pd.DataFrame({
        'date': dates,
        'caudal': caudal,
        'precipitation': precipitation,
        'temperature': temperature,
        'humidity': humidity,
        'ndvi': ndvi
    })


if __name__ == "__main__":
    print("Generando datos de ejemplo...")
    data = generate_sample_data()
    
    print("Inicializando modelo...")
    model = SkyfusionPredictor()
    
    features = ['caudal', 'precipitation', 'temperature', 'humidity', 'ndvi']
    
    print("Entrenando modelo...")
    history = model.train(data, features, epochs=50, batch_size=32)
    
    print("\nGuardando modelo...")
    model.save_model()
    
    print("\nPredicción de ejemplo:")
    scaled_data = model.preprocessor.transform(data, features)
    X_sample = scaled_data[-7:].reshape(1, 7, -1)
    prediction = model.predict(X_sample)
    print(json.dumps(prediction, indent=2))
    
    print("\nModelo entrenado exitosamente")
