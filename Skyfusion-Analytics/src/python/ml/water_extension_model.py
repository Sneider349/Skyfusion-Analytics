"""
Modelo CNN-LSTM-Attention para Predicción de Extensión de Agua
Skyfusion Analytics - Red Neuronal Espacial-Temporal

Arquitectura:
- Entrada multimodal: Índices satelitales + variables climáticas + características estáticas
- Bloque CNN: Extrae características espaciales por timestep
- LSTM: Modela dependencias temporales
- Attention: Pondera importancia de timesteps
- Salida: Probabilidad de agua por píxel
"""

import os
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import tensorflow as tf
from tensorflow.keras import layers, models, optimizers, callbacks
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from tensorflow.keras.metrics import MeanIoU, Precision, Recall, AUC
from tensorflow.keras.losses import BinaryCrossentropy
from sklearn.utils.class_weight import compute_class_weight


class WaterExtensionModel:
    """
    Modelo CNN-LSTM-Attention para predicción de extensión de agua.
    
    Args:
        sequence_length: Número de timesteps en la secuencia de entrada
        patch_size: Tamaño del parche espacial (ej. 64x64)
        n_satellite_features: Número de índices satelitales (default: 4)
        n_climate_features: Número de variables climáticas (default: 3)
        n_static_features: Número de características estáticas (default: 5)
        horizons: Lista de horizontes de predicción (default: [7, 14, 30])
        cnn_filters: Lista de filtros CNN [32, 64, 128]
        lstm_units: Unidades LSTM (default: 64)
        attention_heads: Número de heads en atención multi-head (default: 4)
        dropout_rate: Tasa de dropout (default: 0.3)
    """
    
    def __init__(
        self,
        sequence_length: int = 10,
        patch_size: int = 64,
        n_satellite_features: int = 4,
        n_climate_features: int = 3,
        n_static_features: int = 5,
        horizons: List[int] = None,
        cnn_filters: List[int] = None,
        lstm_units: int = 64,
        attention_heads: int = 4,
        dropout_rate: float = 0.3,
        model_path: str = '../../data/models'
    ):
        self.sequence_length = sequence_length
        self.patch_size = patch_size
        self.n_satellite_features = n_satellite_features
        self.n_climate_features = n_climate_features
        self.n_static_features = n_static_features
        self.horizons = horizons or [7, 14, 30]
        self.cnn_filters = cnn_filters or [32, 64, 128]
        self.lstm_units = lstm_units
        self.attention_heads = attention_heads
        self.dropout_rate = dropout_rate
        self.model_path = Path(model_path)
        self.model_path.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.history = None
        self.class_weights = None
        self._input_signature = None
    
    def _build_spatial_encoder(self, inputs: layers.Layer) -> layers.Layer:
        """
        Construye bloque CNN para extraer características espaciales.
        
        Args:
            inputs: Capa de entrada [batch, seq, h, w, channels]
            
        Returns:
            Características espaciales codificadas [batch, seq, features]
        """
        x = inputs
        
        for i, filters in enumerate(self.cnn_filters):
            x = layers.Conv2D(
                filters=filters,
                kernel_size=(3, 3),
                padding='same',
                activation='relu',
                name=f'cnn_block{i+1}_conv'
            )(x)
            x = layers.BatchNormalization(name=f'cnn_block{i+1}_bn')(x)
            x = layers.MaxPooling2D(pool_size=(2, 2), name=f'cnn_block{i+1}_pool')(x)
        
        x = layers.GlobalAveragePooling2D(name='cnn_global_pool')(x)
        
        return x
    
    def _create_spatial_encoder_layer(self) -> layers.Layer:
        """Crea el encoder espacial como una capa secuencial."""
        inputs = layers.Input(shape=(self.patch_size, self.patch_size, self.n_satellite_features))
        
        x = inputs
        for i, filters in enumerate(self.cnn_filters):
            x = layers.Conv2D(filters=filters, kernel_size=(3, 3), padding='same', activation='relu', name=f'cnn_block{i+1}_conv')(x)
            x = layers.BatchNormalization(name=f'cnn_block{i+1}_bn')(x)
            x = layers.MaxPooling2D(pool_size=(2, 2), name=f'cnn_block{i+1}_pool')(x)
        
        x = layers.GlobalAveragePooling2D(name='cnn_global_pool')(x)
        
        return models.Model(inputs=inputs, outputs=x, name='spatial_encoder')
    
    def _build_temporal_encoder(
        self,
        spatial_features: layers.Layer
    ) -> Tuple[layers.Layer, layers.Layer]:
        """
        Construye bloque LSTM para modelar dependencias temporales.
        
        Args:
            spatial_features: Características espaciales [batch, seq, features]
            
        Returns:
            Tupla de (features LSTM, hidden states)
        """
        x = layers.LSTM(
            self.lstm_units,
            return_sequences=True,
            return_state=True,
            name='temporal_lstm'
        )(spatial_features)
        
        lstm_output, state_h, state_c = x[0], x[1], x[2]
        
        return lstm_output, state_h
    
    def _build_attention(
        self,
        temporal_features: layers.Layer,
        static_features: layers.Layer
    ) -> layers.Layer:
        """
        Construye mecanismo de atención multi-head.
        
        Args:
            temporal_features: Features temporales [batch, seq, units]
            static_features: Features estáticos [batch, static_dim]
            
        Returns:
            Features con atención aplicada
        """
        attention_output = layers.MultiHeadAttention(
            num_heads=self.attention_heads,
            key_dim=self.lstm_units // self.attention_heads,
            dropout=self.dropout_rate,
            name='temporal_attention'
        )(temporal_features, temporal_features)
        
        x = layers.Add(name='attention_add')([
            temporal_features,
            attention_output
        ])
        x = layers.LayerNormalization(name='attention_norm')(x)
        
        static_expanded = layers.RepeatVector(
            self.sequence_length,
            name='static_repeat'
        )(static_features)
        
        x = layers.Concatenate(name='static_concat')([x, static_expanded])
        
        context = layers.GlobalAveragePooling1D(name='context_pool')(x)
        
        return context
    
    def _build_decoder(
        self,
        context: layers.Layer,
        horizon: layers.Layer
    ) -> layers.Layer:
        """
        Construye decodificador para predicción espacial.
        
        Args:
            context: Vector de contexto [batch, units]
            horizon: Código del horizonte [batch, 1]
            
        Returns:
            Máscara de probabilidad de agua [batch, h, w, 1]
        """
        horizon_emb = layers.Embedding(
            input_dim=len(self.horizons),
            output_dim=16,
            name='horizon_embedding'
        )(horizon)
        horizon_emb = layers.Flatten(name='horizon_flat')(horizon_emb)
        
        x = layers.Concatenate(name='decoder_concat')([context, horizon_emb])
        
        x = layers.Dense(256, activation='relu', name='decoder_dense1')(x)
        x = layers.BatchNormalization(name='decoder_bn1')(x)
        x = layers.Dense(128, activation='relu', name='decoder_dense2')(x)
        x = layers.BatchNormalization(name='decoder_bn2')(x)
        x = layers.Dropout(self.dropout_rate, name='decoder_drop2')(x)
        
        h = self.patch_size // 4
        x = layers.Dense(h * h * 64, activation='relu', name='decoder_reshape')(x)
        x = layers.Reshape((h, h, 64), name='decoder_reshape2')(x)
        
        output = layers.Conv2DTranspose(
            filters=32,
            kernel_size=(3, 3),
            strides=(2, 2),
            padding='same',
            activation='relu',
            name='decoder_upconv1'
        )(x)
        
        output = layers.Conv2DTranspose(
            filters=16,
            kernel_size=(3, 3),
            strides=(2, 2),
            padding='same',
            activation='relu',
            name='decoder_upconv2'
        )(output)
        
        output = layers.Conv2D(
            filters=1,
            kernel_size=(1, 1),
            activation='sigmoid',
            name='water_probability'
        )(output)
        
        return output
    
    def build_model(self) -> models.Model:
        """
        Construye el modelo completo.
        
        Returns:
            Modelo Keras compilado
        """
        satellite_input = layers.Input(
            shape=(self.sequence_length, self.patch_size, self.patch_size, self.n_satellite_features),
            name='satellite_input'
        )
        
        climate_input = layers.Input(
            shape=(self.sequence_length, self.n_climate_features),
            name='climate_input'
        )
        
        static_input = layers.Input(
            shape=(self.n_static_features,),
            name='static_input'
        )
        
        horizon_input = layers.Input(
            shape=(1,),
            name='horizon_input'
        )
        
        spatial_encoder = self._create_spatial_encoder_layer()
        cnn_features = layers.TimeDistributed(
            spatial_encoder,
            name='cnn_timedistributed'
        )(satellite_input)
        
        climate_processed = layers.Dense(
            self.lstm_units,
            activation='relu',
            name='climate_projection'
        )(climate_input)
        
        cnn_features_proj = layers.Dense(
            self.lstm_units,
            activation='relu',
            name='cnn_projection'
        )(cnn_features)
        
        temporal_features = layers.Add(name='temporal_fusion')([
            cnn_features_proj,
            climate_processed
        ])
        
        lstm_output, final_state = self._build_temporal_encoder(temporal_features)
        
        context = self._build_attention(lstm_output, static_input)
        
        output = self._build_decoder(context, horizon_input)
        
        model = models.Model(
            inputs={
                'satellite_input': satellite_input,
                'climate_input': climate_input,
                'static_input': static_input,
                'horizon_input': horizon_input
            },
            outputs=output,
            name='WaterExtensionPredictor'
        )
        
        model.compile(
            optimizer=optimizers.Adam(learning_rate=0.001),
            loss=BinaryCrossentropy(label_smoothing=0.01),
            metrics=[
                'binary_accuracy',
                MeanIoU(num_classes=2, name='iou'),
                Precision(name='precision'),
                Recall(name='recall'),
                AUC(name='auc')
            ]
        )
        
        self.model = model
        self._print_summary()
        
        return model
    
    def _print_summary(self):
        """Imprime resumen del modelo."""
        print('\n' + '='*60)
        print('ARQUITECTURA: WaterExtensionPredictor (CNN-LSTM-Attention)')
        print('='*60)
        print(f'Secuencia temporal: {self.sequence_length} timesteps')
        print(f'Tamaño de parche: {self.patch_size}x{self.patch_size}')
        print(f'Features satelitales: {self.n_satellite_features}')
        print(f'Features climáticas: {self.n_climate_features}')
        print(f'Features estáticos: {self.n_static_features}')
        print(f'Horizontes: {self.horizons}')
        print(f'Filtros CNN: {self.cnn_filters}')
        print(f'Unidades LSTM: {self.lstm_units}')
        print(f'Heads de atención: {self.attention_heads}')
        print(f'Dropout: {self.dropout_rate}')
        print('='*60 + '\n')
    
    def _expand_shape(self) -> Tuple[int, int, int]:
        """Retorna forma expandida para decodificador."""
        h = self.patch_size // 4
        return (h, h, 128)
    
    def _create_callbacks(
        self,
        model_name: str,
        monitor: str = 'val_loss',
        patience: int = 10
    ) -> List[callbacks.Callback]:
        """
        Crea callbacks para entrenamiento.
        
        Args:
            model_name: Nombre del modelo
            monitor: Métrica a monitorear
            patience: Paciencia para early stopping
            
        Returns:
            Lista de callbacks
        """
        checkpoint_path = self.model_path / f'{model_name}_best.h5'
        
        return [
            EarlyStopping(
                monitor=monitor,
                patience=patience,
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
                str(checkpoint_path),
                monitor=monitor,
                save_best_only=True,
                verbose=1
            )
        ]
    
    def compute_class_weights(
        self,
        y_train: np.ndarray
    ) -> Dict[float, float]:
        """
        Calcula pesos de clase para manejar desbalance.
        
        Args:
            y_train: Labels de entrenamiento
            y_train: Array binario [n_samples, h, w]
            
        Returns:
            Diccionario con pesos por clase
        """
        y_flat = y_train.flatten()
        
        weights = compute_class_weight(
            class_weight='balanced',
            classes=np.unique(y_flat),
            y=y_flat
        )
        
        self.class_weights = {i: w for i, w in enumerate(weights)}
        
        return self.class_weights
    
    def train(
        self,
        X_train: Dict[str, np.ndarray],
        y_train: np.ndarray,
        X_val: Dict[str, np.ndarray],
        y_val: np.ndarray,
        epochs: int = 50,
        batch_size: int = 8,
        model_name: str = 'water_extension_model',
        use_class_weights: bool = True,
        verbose: int = 1
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
            model_name: Nombre para guardar
            use_class_weights: Si usar pesos de clase
            verbose: Nivel de verbosidad
            
        Returns:
            Historia del entrenamiento
        """
        if self.model is None:
            self.build_model()
        
        callbacks_list = self._create_callbacks(model_name)
        
        y_train_expanded = np.expand_dims(y_train, axis=-1)
        y_val_expanded = np.expand_dims(y_val, axis=-1)
        
        self.history = self.model.fit(
            X_train,
            y_train_expanded,
            validation_data=(X_val, y_val_expanded),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks_list,
            verbose=verbose
        )
        
        self.save_model(model_name)
        
        return self.history
    
    def predict(
        self,
        X: Dict[str, np.ndarray],
        threshold: float = 0.5
    ) -> Dict[str, np.ndarray]:
        """
        Realiza predicción.
        
        Args:
            X: Datos de entrada
            threshold: Umbral para clasificación binaria
            
        Returns:
            Diccionario con predicciones
        """
        if self.model is None:
            raise ValueError('Modelo no cargado. Llama load_model() primero.')
        
        probabilities = self.model.predict(X, verbose=0)
        
        binary_predictions = (probabilities > threshold).astype(np.float32)
        
        water_area_ratio = np.mean(binary_predictions, axis=(1, 2, 3))
        
        confidence = np.where(
            probabilities > 0.5,
            probabilities,
            1 - probabilities
        )
        mean_confidence = np.mean(confidence, axis=(1, 2, 3))
        
        return {
            'probabilities': probabilities,
            'binary_mask': binary_predictions,
            'water_area_ratio': water_area_ratio,
            'confidence': mean_confidence
        }
    
    def predict_with_uncertainty(
        self,
        X: Dict[str, np.ndarray],
        n_samples: int = 10,
        threshold: float = 0.5
    ) -> Dict[str, np.ndarray]:
        """
        Predicción con incertidumbre usando Monte Carlo Dropout.
        
        Args:
            X: Datos de entrada
            n_samples: Número de muestras de dropout
            threshold: Umbral para clasificación
            
        Returns:
            Diccionario con predicciones e incertidumbre
        """
        if self.model is None:
            raise ValueError('Modelo no cargado')
        
        original_training = self.model.training
        
        self.model.trainable = False
        for layer in self.model.layers:
            if hasattr(layer, 'rate'):
                layer.rate = 0.1
        
        predictions = []
        for _ in range(n_samples):
            pred = self.model.predict(X, verbose=0)
            predictions.append(pred)
        
        predictions = np.array(predictions)
        
        mean_prob = np.mean(predictions, axis=0)
        std_prob = np.std(predictions, axis=0)
        
        for layer in self.model.layers:
            if hasattr(layer, 'rate'):
                layer.rate = self.dropout_rate
        
        self.model.trainable = original_training
        
        return {
            'mean_probability': mean_prob,
            'uncertainty': std_prob,
            'binary_mask': (mean_prob > threshold).astype(np.float32)
        }
    
    def evaluate(
        self,
        X_test: Dict[str, np.ndarray],
        y_test: np.ndarray,
        threshold: float = 0.5
    ) -> Dict[str, float]:
        """
        Evalúa el modelo en datos de prueba.
        
        Args:
            X_test: Datos de prueba
            y_test: Labels de prueba
            threshold: Umbral para clasificación
            
        Returns:
            Diccionario con métricas
        """
        if self.model is None:
            raise ValueError('Modelo no cargado')
        
        results = self.model.evaluate(X_test, y_test, verbose=0)
        
        metrics = dict(zip(self.model.metrics_names, results))
        
        predictions = self.predict(X_test, threshold)
        
        y_pred_flat = predictions['binary_mask'].flatten()
        y_true_flat = y_test.flatten()
        
        tp = np.sum((y_pred_flat == 1) & (y_true_flat == 1))
        tn = np.sum((y_pred_flat == 0) & (y_true_flat == 0))
        fp = np.sum((y_pred_flat == 1) & (y_true_flat == 0))
        fn = np.sum((y_pred_flat == 0) & (y_true_flat == 1))
        
        metrics['true_positives'] = float(tp)
        metrics['true_negatives'] = float(tn)
        metrics['false_positives'] = float(fp)
        metrics['false_negatives'] = float(fn)
        
        metrics['water_iou'] = float(tp / (tp + fp + fn)) if (tp + fp + fn) > 0 else 0.0
        
        metrics['mean_water_area_predicted'] = float(np.mean(predictions['water_area_ratio']))
        metrics['mean_water_area_actual'] = float(np.mean(y_test))
        
        return metrics
    
    def save_model(self, name: str = 'water_extension_model'):
        """
        Guarda el modelo y su configuración.
        
        Args:
            name: Nombre del modelo
        """
        if self.model is None:
            raise ValueError('No hay modelo para guardar')
        
        model_file = self.model_path / f'{name}.h5'
        self.model.save(model_file)
        
        config = {
            'sequence_length': self.sequence_length,
            'patch_size': self.patch_size,
            'n_satellite_features': self.n_satellite_features,
            'n_climate_features': self.n_climate_features,
            'n_static_features': self.n_static_features,
            'horizons': self.horizons,
            'cnn_filters': self.cnn_filters,
            'lstm_units': self.lstm_units,
            'attention_heads': self.attention_heads,
            'dropout_rate': self.dropout_rate,
            'saved_at': datetime.now().isoformat()
        }
        
        config_file = self.model_path / f'{name}_config.json'
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f'Modelo guardado en {model_file}')
    
    def load_model(self, name: str = 'water_extension_model') -> models.Model:
        """
        Carga un modelo guardado.
        
        Args:
            name: Nombre del modelo
            
        Returns:
            Modelo cargado
        """
        model_file = self.model_path / f'{name}.h5'
        config_file = self.model_path / f'{name}_config.json'
        
        if not config_file.exists():
            raise FileNotFoundError(f'Config no encontrada: {config_file}')
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        self.sequence_length = config['sequence_length']
        self.patch_size = config['patch_size']
        self.n_satellite_features = config['n_satellite_features']
        self.n_climate_features = config['n_climate_features']
        self.n_static_features = config['n_static_features']
        self.horizons = config['horizons']
        self.cnn_filters = config['cnn_filters']
        self.lstm_units = config['lstm_units']
        self.attention_heads = config['attention_heads']
        self.dropout_rate = config['dropout_rate']
        
        self.model = models.load_model(model_file)
        
        print(f'Modelo cargado desde {model_file}')
        
        return self.model
    
    def get_feature_importance(
        self,
        X_sample: Dict[str, np.ndarray],
        y_sample: np.ndarray
    ) -> Dict[str, float]:
        """
        Calcula importancia aproximada de features usando gradientes.
        
        Args:
            X_sample: Muestra de datos
            y_sample: Labels correspondientes
            
        Returns:
            Diccionario con importancia por tipo de feature
        """
        if self.model is None:
            raise ValueError('Modelo no cargado')
        
        satellite_gradients = []
        climate_gradients = []
        
        for i in range(min(10, len(X_sample['satellite_input']))):
            with tf.GradientTape() as tape:
                tape.watch(X_sample['satellite_input'][i:i+1])
                tape.watch(X_sample['climate_input'][i:i+1])
                
                pred = self.model({
                    'satellite_input': X_sample['satellite_input'][i:i+1],
                    'climate_input': X_sample['climate_input'][i:i+1],
                    'static_input': X_sample['static_input'][i:i+1],
                    'horizon_input': X_sample['horizon_input'][i:i+1]
                })
            
            sat_grad = tape.gradient(pred, X_sample['satellite_input'][i:i+1])
            clim_grad = tape.gradient(pred, X_sample['climate_input'][i:i+1])
            
            satellite_gradients.append(np.mean(np.abs(sat_grad.numpy())))
            climate_gradients.append(np.mean(np.abs(clim_grad.numpy())))
        
        return {
            'satellite_importance': float(np.mean(satellite_gradients)),
            'climate_importance': float(np.mean(climate_gradients)),
            'ratio': float(np.mean(satellite_gradients) / np.mean(climate_gradients))
        }


def create_model_registry() -> Dict[str, any]:
    """
    Crea registro de modelos disponibles para diferentes horizontes.
    
    Returns:
        Diccionario con modelos por horizonte
    """
    return {
        horizon: WaterExtensionModel() 
        for horizon in [7, 14, 30]
    }


if __name__ == '__main__':
    print('Probando construcción del modelo...')
    
    model = WaterExtensionModel(
        sequence_length=10,
        patch_size=64,
        horizons=[7, 14, 30]
    )
    
    model.build_model()
    
    print('\nGenerando datos de prueba...')
    batch_size = 4
    
    X_test = {
        'satellite_input': np.random.randn(
            batch_size, 10, 64, 64, 4
        ).astype(np.float32),
        'climate_input': np.random.randn(
            batch_size, 10, 3
        ).astype(np.float32),
        'static_input': np.random.randn(
            batch_size, 5
        ).astype(np.float32),
        'horizon_input': np.random.randint(0, 3, (batch_size, 1))
    }
    
    y_test = np.random.rand(batch_size, 64, 64, 1) > 0.8
    
    print('\nRealizando predicción de prueba...')
    pred = model.model.predict(X_test, verbose=0)
    print(f'Forma de salida: {pred.shape}')
    
    print('\nModelo creado exitosamente!')
