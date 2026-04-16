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

## Licencia

MIT
