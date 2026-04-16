'use strict';

const { EventEmitter } = require('events');
const neo4jService = require('../backend-node/src/services/neo4j-service');
const llmService = require('../backend-node/src/services/llm-service');

const REPORT_TYPES = {
  CLIMATE_NARRATIVE: 'climate_narrative',
  FLOOD_ALERT: 'flood_alert',
  DROUGHT_ASSESSMENT: 'drought_assessment',
  COMPREHENSIVE: 'comprehensive'
};

const ALERT_LEVELS = {
  CRITICAL: { priority: 4, color: '#FF0000', icon: '🚨' },
  HIGH: { priority: 3, color: '#FF6600', icon: '⚠️' },
  MEDIUM: { priority: 2, color: '#FFCC00', icon: '⚡' },
  LOW: { priority: 1, color: '#00CC00', icon: 'ℹ️' }
};

const DEFAULT_CONFIG = {
  llmProvider: 'openai',
  modelName: 'gpt-4',
  temperature: 0.3,
  maxTokens: 2000,
  includeHistoricalContext: true,
  fallbackLanguage: 'es',
  maxRetries: 3,
  retryDelay: 3000
};

class ReportingAgent extends EventEmitter {
  constructor() {
    super();
    this.status = 'idle';
    this.config = { ...DEFAULT_CONFIG };
    this.reportCache = new Map();
    this.cacheTTL = 300000;
  }

  async initialize(config = {}) {
    this.config = { ...this.config, ...config };
    this.status = 'ready';
    await neo4jService.connect();
    await llmService.initialize(this.config.llmProvider);
    console.log('[ReportingAgent] Initialized with config:', this.config);
  }

  async generateReport(reportType = REPORT_TYPES.COMPREHENSIVE, studyArea = null) {
    if (this.status === 'idle') {
      throw new Error('Agent not initialized. Call initialize() first.');
    }

    const cacheKey = this._generateCacheKey(reportType, studyArea);
    const cached = this._getFromCache(cacheKey);
    if (cached) {
      console.log('[ReportingAgent] Returning cached report');
      return cached;
    }

    this.emit('report:generation:started', { reportType, studyArea });

    try {
      const data = await this._gatherReportData(reportType, studyArea);
      const narrative = await this._generateNarrative(reportType, data);

      const report = {
        id: `report_${Date.now()}`,
        type: reportType,
        timestamp: new Date().toISOString(),
        studyArea: studyArea || data.studyArea,
        narrative,
        alerts: this._extractAlerts(data),
        recommendations: this._generateRecommendations(data),
        metadata: {
          dataPoints: data.pointCount,
          analysisPeriod: data.period,
          confidence: data.confidence
        }
      };

      await this._saveReportToNeo4j(report);
      this._addToCache(cacheKey, report);

      this.emit('REPORT_READY', { reportId: report.id, type: reportType });
      this.emit('report:generation:completed', { reportId: report.id, success: true });

      return report;
    } catch (error) {
      this.emit('report:generation:completed', { reportType, success: false, error: error.message });
      throw error;
    }
  }

  async _gatherReportData(reportType, studyArea) {
    const [analysisResults, predictions, historicalData] = await Promise.all([
      neo4jService.getAnalysisResults(studyArea?.id),
      neo4jService.getLatestPredictions(studyArea?.id),
      this.config.includeHistoricalContext
        ? neo4jService.getHistoricalData(studyArea?.id)
        : Promise.resolve(null)
    ]);

    return {
      studyArea: studyArea || { id: 'default', name: 'Cuenca del Río Combeima' },
      analysis: analysisResults || {},
      predictions: predictions || {},
      historical: historicalData || {},
      pointCount: (analysisResults?.metrics?.pointCount) || 0,
      period: this._calculatePeriod(analysisResults),
      confidence: this._calculateConfidence(analysisResults, predictions)
    };
  }

  async _generateNarrative(reportType, data) {
    const prompt = this._buildPrompt(reportType, data);

    return this._generateWithRetry(prompt);
  }

  _buildPrompt(reportType, data) {
    const baseContext = this._buildContext(data);

    const prompts = {
      [REPORT_TYPES.CLIMATE_NARRATIVE]: `
Contexto del Área de Estudio:
${baseContext}

Genera un informe narrativo sobre las condiciones climáticas actuales y proyectadas
para la cuenca del río Combeima. Incluye:
- Estado actual de la vegetación (NDVI)
- Condiciones de cuerpos de agua (NDWI)
- Proyecciones de caudal
- Tendencias identificadas

El informe debe ser en español y tener un tono profesional científico.
`,

      [REPORT_TYPES.FLOOD_ALERT]: `
Contexto del Área de Estudio:
${baseContext}

Genera una alerta de inundación detallada para la cuenca del río Combeima.
Incluye:
- Nivel de riesgo actual
- Áreas más vulnerables
- Tiempo estimado de impacto
- Acciones recomendadas

Prioriza información crítica y actionable.
`,

      [REPORT_TYPES.DROUGHT_ASSESSMENT]: `
Contexto del Área de Estudio:
${baseContext}

Evalúa las condiciones de sequía para la cuenca del río Combeima.
Incluye:
- Índice de estrés hídrico
- Comparación con períodos históricos
- Prognosis a corto plazo
- Recomendaciones de mitigación
`,

      [REPORT_TYPES.COMPREHENSIVE]: `
Contexto del Área de Estudio:
${baseContext}

Genera un informe técnico integral para la cuenca del río Combeima que incluya:
1. RESUMEN EJECUTIVO (3-4 oraciones)
2. ANÁLISIS MORFOLÓGICO
   - Estado de la cobertura vegetal (NDVI)
   - Análisis de cuerpos de agua (NDWI)
3. PROYECCIONES DE CAUDAL
   - Predicción de variabilidad
   - Niveles de confianza
4. ALERTAS Y RIESGOS
5. RECOMENDACIONES TÉCNICAS

Formato: Markdown con encabezados claros.
Idioma: Español.
`
    };

    return prompts[reportType] || prompts[REPORT_TYPES.COMPREHENSIVE];
  }

  _buildContext(data) {
    const parts = [];

    if (data.analysis?.ndvi) {
      parts.push(`📊 NDVI Actual: ${data.analysis.ndvi.value?.toFixed(3) || 'N/A'}`);
    }
    if (data.analysis?.ndwi) {
      parts.push(`💧 NDWI Actual: ${data.analysis.ndwi.value?.toFixed(3) || 'N/A'}`);
    }
    if (data.predictions?.predictions) {
      const latestPred = data.predictions.predictions[data.predictions.predictions.length - 1];
      parts.push(`📈 Predicción de Caudal: ${latestPred?.toFixed(2) || 'N/A'} m³/s`);
    }
    if (data.predictions?.alertLevel) {
      parts.push(`⚠️ Nivel de Alerta: ${data.predictions.alertLevel}`);
    }

    parts.push(`📍 Ubicación: ${data.studyArea?.name || 'Cuenca del Río Combeima'}`);
    parts.push(`📅 Período de Análisis: ${data.period}`);
    parts.push(`🎯 Confianza del Análisis: ${(data.confidence * 100).toFixed(1)}%`);

    return parts.join('\n');
  }

  async _generateWithRetry(prompt, retryCount = 0) {
    try {
      const response = await llmService.generate({
        prompt,
        model: this.config.modelName,
        temperature: this.config.temperature,
        max_tokens: this.config.maxTokens
      });

      return response.text || response.content || response;
    } catch (error) {
      console.error(`[ReportingAgent] LLM generation failed (attempt ${retryCount + 1}):`, error.message);

      if (retryCount < this.config.maxRetries) {
        await this._delay(this.config.retryDelay * (retryCount + 1));
        return this._generateWithRetry(prompt, retryCount + 1);
      }

      return this._generateFallbackReport(prompt);
    }
  }

  _generateFallbackReport(prompt) {
    return `
# Informe Técnico - Cuenca del Río Combeima

⚠️ **Nota**: El servicio de generación de lenguaje natural experimentó dificultades técnicas.
Se proporciona un resumen basado en datos numéricos.

---

## Resumen de Datos

${prompt.includes('FLOOD') ? '## Análisis de Inundación\nNivel de riesgo: Consultar panel de control.\n' : ''}
${prompt.includes('DROUGHT') ? '## Evaluación de Sequía\nÍndice de estrés: Consultar métricas.\n' : ''}

---

*Informe generado: ${new Date().toISOString()}*
*Es necesario procesamiento adicional para narrativa completa.*
`;
  }

  _extractAlerts(data) {
    const alerts = [];

    if (data.predictions?.alertLevel) {
      const level = ALERT_LEVELS[data.predictions.alertLevel] || ALERT_LEVELS.LOW;
      alerts.push({
        level: data.predictions.alertLevel,
        message: `Nivel de alerta ${data.predictions.alertLevel} para variabilidad de caudal`,
        priority: level.priority
      });
    }

    if (data.analysis?.ndvi?.value < 0.3) {
      alerts.push({
        level: 'HIGH',
        message: 'Bajo índice de vegetación detectado - posible estrés hídrico',
        priority: 3
      });
    }

    if (data.analysis?.ndwi?.value > 0.5) {
      alerts.push({
        level: 'CRITICAL',
        message: 'Alta presencia de agua detectada - riesgo de inundación',
        priority: 4
      });
    }

    return alerts.sort((a, b) => b.priority - a.priority);
  }

  _generateRecommendations(data) {
    const recommendations = [];

    if (data.predictions?.alertLevel === 'CRITICAL' || data.predictions?.alertLevel === 'HIGH') {
      recommendations.push({
        category: 'URGENTE',
        items: [
          'Activar protocolo de emergencia por inundación',
          'Notificar a autoridades locales de gestión de riesgos',
          'Preparar evacuación de zonas ribereñas'
        ]
      });
    }

    if (data.analysis?.ndvi?.value < 0.4) {
      recommendations.push({
        category: 'MONITOREO AMBIENTAL',
        items: [
          'Incrementar frecuencia de monitoreo NDVI',
          'Evaluar causas de degradación de cobertura vegetal',
          'Considerar programas de reforestación'
        ]
      });
    }

    recommendations.push({
      category: 'CONTINUO',
      items: [
        'Mantener análisis morfológicos semanales',
        'Actualizar modelos predictivos con nuevos datos',
        'Documentar eventos climáticos significativos'
      ]
    });

    return recommendations;
  }

  _calculatePeriod(analysisResults) {
    if (analysisResults?.timestamp) {
      return `${analysisResults.timestamp} - ${new Date().toISOString()}`;
    }
    return `Últimas 24 horas (${new Date().toISOString().split('T')[0]})`;
  }

  _calculateConfidence(analysisResults, predictions) {
    let confidence = 0.5;

    if (analysisResults?.metrics?.stdDev) {
      confidence += 0.25 * (1 - Math.min(analysisResults.metrics.stdDev, 1));
    }

    if (predictions?.metrics?.r2) {
      confidence += 0.25 * predictions.metrics.r2;
    }

    return Math.min(Math.max(confidence, 0), 1);
  }

  async _saveReportToNeo4j(report) {
    const reportRecord = {
      id: report.id,
      type: report.type,
      timestamp: report.timestamp,
      studyAreaId: report.studyArea?.id || 'default',
      narrative: report.narrative,
      alerts: report.alerts,
      recommendations: report.recommendations,
      metadata: report.metadata
    };

    await neo4jService.saveReport(reportRecord);
  }

  _generateCacheKey(reportType, studyArea) {
    return `${reportType}_${studyArea?.id || 'default'}_${Date.now() - (Date.now() % this.cacheTTL)}`;
  }

  _getFromCache(key) {
    const cached = this.reportCache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTTL) {
      return cached.report;
    }
    this.reportCache.delete(key);
    return null;
  }

  _addToCache(key, report) {
    this.reportCache.set(key, { report, timestamp: Date.now() });

    if (this.reportCache.size > 100) {
      const oldestKey = this.reportCache.keys().next().value;
      this.reportCache.delete(oldestKey);
    }
  }

  _delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  updateConfig(newConfig) {
    this.config = { ...this.config, ...newConfig };
    console.log('[ReportingAgent] Configuration updated:', this.config);
  }

  getStatus() {
    return {
      status: this.status,
      config: this.config,
      cacheSize: this.reportCache.size,
      supportedReportTypes: Object.keys(REPORT_TYPES)
    };
  }

  async shutdown() {
    this.status = 'idle';
    this.reportCache.clear();
    await neo4jService.disconnect();
    console.log('[ReportingAgent] Shutdown complete');
  }
}

module.exports = new ReportingAgent();
module.exports.REPORT_TYPES = REPORT_TYPES;
module.exports.ALERT_LEVELS = ALERT_LEVELS;
