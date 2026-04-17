# Estructura de Agentes - Skyfusion Analytics

## Índice

1. [Visión General](#visión-general)
2. [Arquitectura de Agentes](#arquitectura-de-agentes)
3. [Agente de Ingesta de Datos](#agente-de-ingesta-de-datos)
4. [Agente de Análisis](#agente-de-análisis)
5. [Agente de Predicción](#agente-de-predicción)
6. [Agente de Reportes](#agente-de-reportes)
7. [Orquestador](#orquestador)
8. [Comunicación entre Agentes](#comunicación-entre-agentes)

---

## Visión General

Los agentes son componentes autónomos que manejan responsabilidades específicas dentro de Skyfusion Analytics. Cada agente:

- Extiende `EventEmitter` para comunicación basada en eventos
- Utiliza un sistema de logging centralizado
- Implementa un ciclo de vida con estados (`idle`, `ready`, `processing`)
- Provee métodos de `initialize()`, operaciones específicas y `getStatus()`
- Maneja reintentos automáticos para operaciones fallidas
- Soporta actualización dinámica del área de estudio

---

## Arquitectura de Agentes

```
┌─────────────────────────────────────────────────────────┐
│                    Orchestrator                         │
│  ├── studyArea: Dynamic (coords/polygons)               │
│  └── eventHistory: Event[]                              │
└─────────────────────────────────────────────────────────┘
                           ▲
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
┌───────────────────┐┌─────────────────────┐┌──────────────────────┐
│  ReportingAgent   ││   PredictionAgent   ││    AnalysisAgent     │
│  ├── LLM Service  ││  ├── TensorFlow     ││  ├── OpenCV Scripts │
│  └── Report Cache ││  └── Model Cache    ││  └── Task Queue     │
└───────────────────┘└─────────────────────┘└──────────────────────┘
         ▲                 ▲                 ▲
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                   ┌───────┴───────┐
                   │  Neo4jService │
                   └───────────────┘
```

---

## Agente de Análisis

**Archivo:** `agents/analysis-agent.js`

### Clase: `AnalysisAgent`

```javascript
const analysisAgent = require('./analysis-agent');
```

#### Constructor
```javascript
constructor() {
  super();
  this.status = 'idle';
  this.activeTasks = 0;
  this.taskQueue = [];
}
```

#### Configuración por Defecto
| Parámetro | Tipo | Valor |
|-----------|------|-------|
| `maxConcurrent` | number | 3 |
| `timeout` | number | 30000 |
| `maxRetries` | number | 3 |
| `retryDelay` | number | 5000 |

#### Métodos

##### `initialize(config)`
Inicializa el agente con configuración personalizada.

```javascript
await agent.initialize({ maxConcurrent: 5, timeout: 60000 });
```

##### `analyze(data, analysisType, studyArea)`
Ejecuta un tipo específico de análisis.

```javascript
const result = await agent.analyze(data, 'NDVI', studyArea);
```

##### `updateStudyArea(newStudyArea)`
Actualiza dinámicamente el área de estudio.

```javascript
agent.updateStudyArea({
  type: 'polygon',
  coordinates: [[-75.1, 4.4], [-75.0, 4.5], ...],
  river: 'Río Combeima'
});
```

##### `getStatus()`
Retorna el estado actual del agente.

#### Tipos de Análisis Soportados
| Tipo | Script Python | Descripción |
|------|---------------|--------------|
| `NDVI` | `ndvi_analysis.py` | Índice de Vegetación |
| `NDWI` | `ndwi_analysis.py` | Índice de Agua |
| `MORPHOLOGICAL` | `morphological_analysis.py` | Análisis morfológico |

#### Eventos Emitidos
| Evento | Payload | Descripción |
|--------|---------|-------------|
| `analysis:started` | `{ analysisType, studyArea }` | Análisis iniciado |
| `analysis:completed` | `{ analysisType, success, error? }` | Análisis completado |

---

## Agente de Predicción

**Archivo:** `agents/prediction-agent.js`

### Clase: `PredictionAgent`

```javascript
const predictionAgent = require('./prediction-agent');
```

#### Constructor
```javascript
constructor() {
  super();
  this.status = 'idle';
  this.loadedModels = new Map();
}
```

#### Configuración por Defecto
| Parámetro | Tipo | Valor |
|-----------|------|-------|
| `predictionHorizon` | number | 24 |
| `confidenceLevel` | number | 0.95 |
| `timeout` | number | 60000 |
| `maxRetries` | number | 3 |

#### Métodos

##### `initialize(config)`
Inicializa el agente con configuración personalizada.

```javascript
await agent.initialize({ predictionHorizon: 48, confidenceLevel: 0.99 });
```

##### `loadModel(modelName)`
Carga un modelo de predicción en memoria.

```javascript
await agent.loadModel('LSTM_FORECAST');
```

##### `predict(inputData, modelName, studyArea)`
Genera predicciones usando el modelo especificado.

```javascript
const result = await agent.predict(data, 'FLOW_PREDICTION', studyArea);
// Returns: { success, predictions, confidenceInterval, alertLevel, metrics }
```

##### `updateStudyArea(newStudyArea)`
Actualiza dinámicamente el área de estudio.

```javascript
predictionAgent.updateStudyArea({
  id: 'combeima_001',
  type: 'polygon',
  coordinates: [...]
});
```

##### `getStatus()`
Retorna el estado actual del agente incluyendo modelos cargados.

#### Modelos Disponibles
| Modelo | Script Python | Descripción |
|--------|---------------|--------------|
| `FLOW_PREDICTION` | `flow_prediction.py` | Predicción de caudal |
| `VARIABILITY_ANALYSIS` | `variability_analysis.py` | Análisis de variabilidad |
| `LSTM_FORECAST` | `lstm_forecast.py` | Forecast LSTM |

#### Niveles de Alerta
| Nivel | Variabilidad | Color |
|-------|--------------|-------|
| `CRITICAL` | > 50 | 🔴 |
| `HIGH` | > 30 | 🟠 |
| `MEDIUM` | > 15 | 🟡 |
| `LOW` | ≤ 15 | 🟢 |

#### Eventos Emitidos
| Evento | Payload | Descripción |
|--------|---------|-------------|
| `prediction:requested` | `{ modelName, studyArea }` | Predicción solicitada |
| `prediction:completed` | `{ modelName, success, error? }` | Predicción completada |
| `model:loaded` | `{ modelName }` | Modelo cargado |

---

## Agente de Reportes

**Archivo:** `agents/reporting-agent.js`

### Clase: `ReportingAgent`

```javascript
const reportingAgent = require('./reporting-agent');
```

#### Constructor
```javascript
constructor() {
  super();
  this.status = 'idle';
  this.reportCache = new Map();
}
```

#### Configuración por Defecto
| Parámetro | Tipo | Valor |
|-----------|------|-------|
| `llmProvider` | string | 'openai' |
| `modelName` | string | 'gpt-4' |
| `temperature` | number | 0.3 |
| `maxTokens` | number | 2000 |
| `includeHistoricalContext` | boolean | true |
| `maxRetries` | number | 3 |

#### Métodos

##### `initialize(config)`
Inicializa el agente con configuración personalizada.

```javascript
await agent.initialize({
  llmProvider: 'anthropic',
  modelName: 'claude-3-sonnet',
  temperature: 0.2
});
```

##### `generateReport(reportType, studyArea)`
Genera un informe basado en los datos de Neo4j.

```javascript
const report = await agent.generateReport('comprehensive', studyArea);
// Returns: { id, type, narrative, alerts, recommendations, metadata }
```

##### `updateConfig(newConfig)`
Actualiza la configuración del agente.

```javascript
reportingAgent.updateConfig({ modelName: 'gpt-4-turbo' });
```

##### `getStatus()`
Retorna el estado actual del agente.

#### Tipos de Reporte
| Tipo | Descripción |
|------|-------------|
| `climate_narrative` | Narrativa de condiciones climáticas |
| `flood_alert` | Alerta de inundación detallada |
| `drought_assessment` | Evaluación de sequía |
| `comprehensive` | Informe técnico integral |

#### Estructura del Reporte
```javascript
{
  id: "report_1713000000000",
  type: "comprehensive",
  timestamp: "2024-04-13T12:00:00.000Z",
  studyArea: { id, name, coordinates },
  narrative: "# Informe Técnico...\n\n...",
  alerts: [
    { level: "HIGH", message: "...", priority: 3 }
  ],
  recommendations: [
    { category: "URGENTE", items: [...] }
  ],
  metadata: { dataPoints, analysisPeriod, confidence }
}
```

#### Eventos Emitidos
| Evento | Payload | Descripción |
|--------|---------|-------------|
| `report:generation:started` | `{ reportType, studyArea }` | Generación iniciada |
| `report:generation:completed` | `{ reportId, success, error? }` | Generación completada |
| `REPORT_READY` | `{ reportId, type }` | Reporte listo para consumo |

---

## Orquestador

**Archivo:** `agents/orchestrator.js`

### Clase: `AgentOrchestrator`

```javascript
const { orchestrator } = require('./orchestrator');
```

#### Constructor
```javascript
constructor() {
  this.studyArea = DEFAULT_STUDY_AREA;
  this.isInitialized = false;
  this.eventHistory = [];
}
```

#### Métodos

##### `initialize(config)`
Inicializa todos los agentes.

```javascript
await orchestrator.initialize({
  analysis: { maxConcurrent: 3 },
  prediction: { predictionHorizon: 24 },
  reporting: { modelName: 'gpt-4' }
});
```

##### `processDataPipeline(data)`
Ejecuta el pipeline completo: análisis → predicción → reporte.

```javascript
const result = await orchestrator.processDataPipeline(data);
```

##### `runAnalysisOnly(data, analysisTypes)`
Ejecuta solo análisis sin predicción.

```javascript
const result = await orchestrator.runAnalysisOnly(data, ['NDVI', 'NDWI']);
```

##### `runPredictionWithHistory(historicalData)`
Ejecuta predicción con datos históricos.

```javascript
const result = await orchestrator.runPredictionWithHistory(historicalData);
```

##### `generateReport(reportType)`
Genera un reporte usando datos existentes.

```javascript
const report = await orchestrator.generateReport('comprehensive');
```

##### `updateStudyArea(newStudyArea)`
Actualiza el área de estudio para todos los agentes.

```javascript
orchestrator.updateStudyArea({
  id: 'new_basin',
  type: 'polygon',
  coordinates: [[-75.2, 4.3], ...],
  name: 'Nueva Cuenca'
});
```

##### `getSystemStatus()`
Retorna el estado completo del sistema.

##### `shutdown()`
Finaliza todos los agentes.

```javascript
await orchestrator.shutdown();
```

---

## Comunicación entre Agentes

### Flujo de Eventos

```
[DATA_INGESTED]
       │
       ▼
[AnalysisAgent]
       │
       ▼ (ANALYSIS_COMPLETED)
[PredictionAgent]
       │
       ▼ (PREDICTION_COMPLETED)
[ReportingAgent]
       │
       ▼ (REPORT_READY)
```

### Suscripción a Eventos

```javascript
// Ejemplo de suscripción
analysisAgent.on('analysis:completed', (payload) => {
  console.log(`Análisis ${payload.analysisType} completado`);
});

predictionAgent.on('prediction:completed', (payload) => {
  console.log(`Predicción: ${payload.alertLevel}`);
});

reportingAgent.on('REPORT_READY', (payload) => {
  console.log(`Reporte ${payload.reportId} generado`);
});
```

### Ciclo de Vida de Estados

```
     ┌──────────┐
     │  'idle'  │ ◄── Estado inicial
     └────┬─────┘
          │ initialize()
          ▼
     ┌──────────┐
     │ 'ready'  │ ◄── Listo para procesar
     └────┬─────┘
          │ Método de operación
          ▼
     ┌─────────────┐
     │ 'processing'│ ◄── Procesando
     └──────┬───────┘
            │ Completado/Error
            ▼
        'ready'
```

---

## Servicios Backend

### Neo4jService

```javascript
const neo4jService = require('../backend-node/src/services/neo4j-service');

// Métodos principales
await neo4jService.connect();
await neo4jService.saveAnalysisResult(metadata);
await neo4jService.savePrediction(prediction);
await neo4jService.getAnalysisResults(studyAreaId);
await neo4jService.getLatestPredictions(studyAreaId);
```

### LLMService

```javascript
const llmService = require('../backend-node/src/services/llm-service');

// Inicialización
await llmService.initialize('openai'); // openai, anthropic, local

// Generación
const response = await llmService.generate({
  prompt: '...',
  model: 'gpt-4',
  temperature: 0.3,
  max_tokens: 2000
});
```

---

## Variables de Entorno

```env
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j

# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
LOCAL_LLM_URL=http://localhost:11434/api/generate
```

---

## Ejemplo de Uso

```javascript
const { orchestrator } = require('./orchestrator');

async function main() {
  await orchestrator.initialize();
  
  // Ejecutar pipeline completo
  const sampleData = [
    { lat: 4.45, lon: -75.15, nir: 0.65, red: 0.3, green: 0.4 },
    { lat: 4.46, lon: -75.14, nir: 0.58, red: 0.28, green: 0.38 }
  ];
  
  const result = await orchestrator.processDataPipeline(sampleData);
  
  console.log('Prediction Alert:', result.prediction.alertLevel);
  console.log('Report:', result.report.narrative);
  
  await orchestrator.shutdown();
}

main();
```
