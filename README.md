# Skyfusion Analytics

Plataforma SaaS de análisis multitemporal para monitoreo y predicción ambiental en cuencas hidrográficas.

---

## Requisitos del Sistema

### Versiones Fijadas (Consistencia entre Entornos)

| Componente | Versión | Propósito |
|------------|---------|-----------|
| Python | 3.10 | Largo soporte hasta 2026 |
| GDAL | 3.6.2 | Sistema de coordenadas/proyecciones |
| Rasterio | 1.3.8 | Lectura/escritura datos raster |
| Node.js | 18+ | Backend y frontend |

> **Importante:** Para garantizar versiones consistentes, usar el contenedor de desarrollo (ver sección Codespaces).

---

## Quick Start

### Opción 1: GitHub Codespaces (Recomendado)

1. Fork del repositorio
2. Click en "Code" → "Create codespace"
3. El contenedor se configura automáticamente con:
   - GDAL 3.6.2
   - Rasterio 1.3.8
   - Todas las dependencias de Python
   - Node.js 18+

```bash
# Verificar versiones instaladas
gdal-config --version    # GDAL: 3.6.2
python -c "import rasterio; print(rasterio.__version__)"  # 1.3.8
```

### Opción 2: Desarrollo Local

#### Python (con soporte geoespacial)

```bash
# Clonar repositorio
git clone https://github.com/[user]/Skyfusion-Analytics.git
cd Skyfusion-Analytics

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar GDAL del sistema (requerido por rasterio)
# Ubuntu/Debian:
sudo apt-get install gdal-bin libgdal-dev

# macOS:
brew install gdal

# Windows:
# Usar OSGeo4W o conda

# Instalar dependencias (rasterio se instala desde wheel)
pip install GDAL==3.6.2
pip install -r requirements.txt
```

#### Node.js

```bash
# Instalar dependencias
npm install
cd src/frontend && npm install && cd ../..
```

#### Iniciar servicios

```bash
# Backend
npm start

# Frontend (en otra terminal)
cd src/frontend && npm start
```

---

## Desarrollo con Dev Container

### Estructura del Contenedor

```
.devcontainer/
├── Dockerfile              # Imagen con GDAL 3.6.2 + Rasterio 1.3.8
├── devcontainer.json      # Configuración de Codespaces
├── pre-init.sh            # Scripts de inicialización
├── post-create.sh         # Post-creación
├── post-attach.sh         # Al reconectar
└── on-open.sh            # Al abrir el proyecto
```

### Reconstruir Contenedor

Si hay cambios en dependencias:

1. Modificar `requirements.txt` o `Dockerfile`
2. En Codespaces: `F1` → "Dev Containers: Rebuild Container"
3. O localmente con VS Code + Docker

### Verificar Instalación

```bash
# Verificar GDAL
gdal-config --version  # 3.6.2

# Verificar Rasterio
python -c "import rasterio; print(rasterio.__version__)"  # 1.3.8

# Verificar GDAL linked con Rasterio
python -c "import rasterio; print(rasterio.__gdal_version__)"  # 3.6.2
```

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

### Pipeline de Eventos

```
DATA_INGESTED → AnalysisAgent → PredictionAgent → ReportingAgent → REPORT_READY
```

---

## Pipeline de Datos Satelitales

### Preprocessor (src/python/processing/)

```bash
# Inicializar estructura de datos
python src/python/processing/setup_raw_directory.py --init

# Ejecutar preprocessor GEE
python src/python/processing/preprocessor.py
```

### Colecciones Procesadas

| Satélite | Período | Resolución |
|----------|---------|------------|
| Landsat MSS | 1972-1983 | 60m |
| Landsat TM | 1984-2012 | 30m |
| Landsat OLI | 2013-2023 | 30m |
| Sentinel-2 | 2015-2023 | 10m |

### Estructura de Datos

```
data/
└── raw/satelite/
    ├── landsat/
    │   ├── mss/
    │   ├── tm/
    │   └── oli/
    ├── sentinel2/
    │   ├── L1C/
    │   └── L2A/
    └── metadata/
        ├── catalog.csv
        ├── logs/
        └── checksums/
```

---

## Configuración

### Variables de Entorno

```env
# Backend
NODE_ENV=development
PORT=3001
DEMO_MODE=true

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Google Earth Engine
GEE_PROJECT_ID=skyfusion-analytics
GEE_SERVICE_ACCOUNT_KEY=./config/gee-service-account.json

# Event Bus
EVENT_BUS_TYPE=rabbitmq
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# Preprocessor
CLOUD_COVER_THRESHOLD=15
DOWNLOAD_RAW=false
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
| Geoespacial | GDAL 3.6.2, Rasterio 1.3.8, GeoPandas |
| Visión | OpenCV |
| IA | OpenAI/Anthropic/LLM |

---

## Licencia

MIT
