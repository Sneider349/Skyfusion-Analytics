# Skyfusion Analytics - Deep Learning para Predicción de Extensión de Agua

## Resumen

Este módulo implementa una red neuronal **CNN-LSTM-Atención** para predecir la extensión de agua en cuencas hidrográficas, utilizando series temporales de índices satelitales y datos climáticos.

## Arquitectura del Modelo

```
Entrada Multi-Modal
├── Índices Satelitales: [Secuencia 10 días × Parche 64×64 × 4 features]
├── Variables Climáticas: [Secuencia 10 días × 3 features]
└── Características Estáticas: [5 features]

        ↓
        
Bloque CNN (2-3 capas)
├── Conv2D: 32 filtros, kernel 3×3, ReLU
├── Conv2D: 64 filtros, kernel 3×3, ReLU
├── Conv2D: 128 filtros, kernel 3×3, ReLU
└── GlobalAveragePooling2D

        ↓
        
Fusión Temporal
├── Concatenación CNN + Clima proyectado
└── LSTM: 64 unidades, return_sequences=True

        ↓
        
Mecanismo de Atención
├── Multi-Head Attention: 4 heads, key_dim=16
├── Add & LayerNorm
└── GlobalAveragePooling1D

        ↓
        
Decodificador Espacial
├── Dense: 256 → 128 (ReLU, Dropout 0.3)
├── Embedding de Horizonte
├── Conv2DTranspose: Upsampling a 64×64
└── Salida: Sigmoide (Probabilidad de agua)

        ↓
        
Salida: [batch, 64, 64, 1] - Mapa de probabilidad de agua
```

## Estructura de Archivos

```
src/python/ml/
├── water_extension_model.py   # Definición de la arquitectura CNN-LSTM-Attention
├── data_generator.py          # Generador de dataset con parches espaciales
├── train_pipeline.py          # Pipeline completo de entrenamiento
├── run_inference.py           # Script de inferencia
└── skyfusion_predictor.py    # Modelo LSTM existente (caudal)
```

## Uso

### 1. Generación de Dataset

```python
from data_generator import WaterDatasetGenerator, DatasetConfig

generator = WaterDatasetGenerator()

# Datos sintéticos (para pruebas)
data = generator.generate_synthetic_dataset(n_samples=1000)

# Guardar dataset
generator.save_dataset(data, 'water_extension_dataset')
```

### 2. Entrenamiento del Modelo

```bash
# Pipeline completo
python train_pipeline.py --samples 1000 --epochs 50 --horizons 7,14,30

# Solo evaluación
python train_pipeline.py --evaluate-only --model-name water_extension_model
```

### 3. Inferencia

```python
from water_extension_model import WaterExtensionModel
import numpy as np

model = WaterExtensionModel()
model.load_model('water_extension_model')

X = {
    'satellite_input': np.random.randn(1, 10, 64, 64, 4),
    'climate_input': np.random.randn(1, 10, 3),
    'static_input': np.random.randn(1, 5),
    'horizon_input': np.array([[0]])
}

prediction = model.predict(X, threshold=0.5)
```

## API de Endpoints

```
GET  /api/v1/predictions/:catchment                 # Predicciones + extensión de agua
GET  /api/v1/predictions/:catchment/water-extension # Solo extensión de agua
GET  /api/v1/predictions/:catchment/water-extension/all-horizons
GET  /api/v1/water-extension/:catchment
GET  /api/v1/water-extension/:catchment/all-horizons
```

## Configuración

### Hiperparámetros

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| sequence_length | 10 | Timesteps de secuencia de entrada |
| patch_size | 64 | Tamaño del parche espacial |
| cnn_filters | [32, 64, 128] | Filtros por capa CNN |
| lstm_units | 64 | Unidades LSTM |
| attention_heads | 4 | Heads de atención |
| dropout_rate | 0.3 | Tasa de dropout |
| batch_size | 8 | Tamaño de batch |
| learning_rate | 0.001 | Tasa de aprendizaje |

### Horizontes de Predicción

- **7 días**: Predicción a corto plazo
- **14 días**: Predicción a mediano plazo
- **30 días**: Predicción a largo plazo

## Métricas de Evaluación

| Métrica | Descripción |
|---------|-------------|
| IoU (Mean) | Intersección sobre Unión promediada |
| Precision | Precisión de predicción de agua |
| Recall | Sensibilidad (agua detectada / agua total) |
| AUC | Área bajo la curva ROC |
| Water IoU | IoU específico para la clase agua |

## Dependencias

```
tensorflow>=2.12.0
numpy>=1.21.0
pandas>=1.3.0
scikit-learn>=1.0.0
earthengine-api>=0.1.0
opencv-python>=4.5.0
tqdm>=4.62.0
```

## Próximos Pasos

1. **Reentrenamiento con datos reales**: Configurar credenciales de GEE y extraer datos históricos de la cuenca Combeima (2020-2025)

2. **Transfer learning**: Entrenar modelo base con múltiples cuencas y hacer fine-tuning para Combeima

3. **Monte Carlo Dropout**: Implementar incertidumbre con múltiples forward passes

4. **Integración IoT**: Sincronizar datos de sensores in-situ para mejorar precisión

5. **Dashboard**: Integrar `WaterExtensionPanel` en el dashboard principal

## Autores

Sistema Skyfusion Analytics - Universidad Minuto de Dios
