# Skyfusion Analytics

Plataforma SaaS de análisis multitemporal para monitoreo y predicción ambiental en cuencas hidrográficas.

---

## Quick Start

### Requisitos
- Node.js >= 18
- npm >= 8

### Instalación

```bash
# Instalar dependencias
npm install
cd src/frontend && npm install && cd ../..

# Iniciar backend (modo demo)
npm start

# En otra terminal, iniciar frontend
cd src/frontend && npm start
```

### Acceso
- Frontend: http://localhost:3000
- Backend API: http://localhost:3001/api/v1
- Health Check: http://localhost:3001/health

---

## Sistema de Agentes

Sistema de orquestación basado en eventos para análisis geoespacial e inteligencia artificial.

### Estructura

```
agents/
├── analysis-agent.js      # Análisis NDVI/NDWI con OpenCV
├── prediction-agent.js    # Predicción de caudal con TensorFlow
├── reporting-agent.js     # Generación de reportes con LLM
├── orchestrator.js        # Orquestador de agentes
└── package.json
```

### Uso

```bash
cd agents && npm install
node orchestrator.js
```

### Pipeline de Eventos

```
DATA_INGESTED → AnalysisAgent → PredictionAgent → ReportingAgent → REPORT_READY
```

### Configuración

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
OPENAI_API_KEY=sk-...
```

---

## Modo Demo (Sin Neo4j)

Por defecto la app corre en modo demo con datos simulados:

```bash
DEMO_MODE=true npm start
```

---

## Docker

```bash
# Iniciar todos los servicios
docker-compose up --build

# Solo backend y frontend (sin Neo4j)
docker-compose up backend frontend
```

---

## API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/demo/metrics/:catchmentId` | Métricas actuales |
| GET | `/api/v1/demo/alerts/:catchmentId` | Alertas activas |
| GET | `/api/v1/demo/predictions/:catchmentId` | Predicciones |
| GET | `/api/v1/demo/narrative/:catchmentId` | Análisis IA |
| GET | `/api/v1/demo/catchments` | Lista de cuencas |
| GET | `/api/v1/demo/stations` | Estaciones de monitoreo |

---

## Tecnologías

| Capa | Tecnología |
|------|------------|
| Frontend | React, Tailwind CSS, Leaflet, Chart.js |
| Backend | Node.js, Express, Socket.io |
| Agentes | EventEmitter, child_process |
| DB | Neo4j |
| ML | TensorFlow |
| Visión | OpenCV |
| IA | OpenAI/Anthropic/LLM |

---

---

## Procesamiento de Métricas Morfométricas Georreferenciadas

Sistema de transformación de proyecciones espaciales (CRS) para calcular métricas morfométricas en metros reales sobre el terreno.

### Módulos

```
src/python/processing/
├── crs_transformer.py          # Transformación de proyecciones CRS
├── geo_metrics_calculator.py   # Cálculo de métricas en metros reales
├── morphological_processor.py  # Procesamiento morfológico de imágenes
├── indices_processor.py        # Procesamiento de índices (NDVI, NDWI)
└── classification_processor.py # Clasificación de cobertura
```

### Instalación de Dependencias Python

```bash
pip install numpy opencv-python scipy pyproj
```

### Uso Básico

```python
from crs_transformer import CRSTransformer, BoundingBox, CRSTransformConfig
from geo_metrics_calculator import GeoMorphologicalCalculator

# Configurar transformador CRS
config = CRSTransformConfig(
    source_crs="EPSG:4326",
    target_crs="EPSG:32618"
)
transformer = CRSTransformer(config=config)

# Definir área de estudio
bbox = BoundingBox(
    min_lon=-75.5, min_lat=4.0,
    max_lon=-74.8, max_lat=5.0
)

# Seleccionar CRS óptimo (UTM para la zona)
optimal_crs = transformer.select_optimal_crs(bbox)

# Para áreas extensas, dividir en sub-zonas
sub_zones = transformer.split_area_into_sub_zones(bbox, max_width_deg=6.0)

# Calcular métricas morfométricas en metros
calculator = GeoMorphologicalCalculator()
calculator.setup_crs(bbox)

# Calcular desde máscara binaria
metrics = calculator.calculate_metrics_from_binary_mask(mask, optimal_crs)
print(f"Área: {metrics.area_km2:.4f} km²")
print(f"Perímetro: {metrics.perimeter_m:.2f} m")
print(f"CRS usado: {metrics.crs_used}")
```

### Funcionalidades Principales

| Funcionalidad | Descripción | Estado |
|---------------|-------------|--------|
| Detección de CRS | Identifica tipo de proyección (geográfica, UTM, igual área) | ✅ Completado |
| Selección automática UTM | Calcula zona UTM óptima para ubicación | ✅ Completado |
| División de áreas extensas | Particiona en sub-zonas con CRS individual | ✅ Completado |
| Cálculo factores de escala | Convierte píxeles a metros con precisión | ✅ Completado |
| Métricas morfométricas | Área, perímetro, compactitud, elongación | ✅ Completado |

### Ejecución de Tests

```bash
cd Skyfusion-Amigo
python -m pytest tests/ -v
```

**Resultados:** 78 tests pasan (30 CRS + 48 morfológicos)

---

## Licencia

MIT
