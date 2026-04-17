'use strict';

const analysisAgent = require('./analysis-agent');
const predictionAgent = require('./prediction-agent');
const reportingAgent = require('./reporting-agent');

const AGENT_EVENTS = {
  DATA_INGESTED: 'DATA_INGESTED',
  ANALYSIS_COMPLETED: 'ANALYSIS_COMPLETED',
  REPORT_READY: 'REPORT_READY'
};

const DEFAULT_STUDY_AREA = {
  id: 'combeima_basin_01',
  name: 'Cuenca del Río Combeima',
  type: 'polygon',
  coordinates: [
    [-75.1847, 4.4378],
    [-75.1247, 4.4378],
    [-75.1247, 4.4978],
    [-75.1847, 4.4978],
    [-75.1847, 4.4378]
  ],
  river: 'Río Combeima',
  municipality: 'Ibagué',
  department: 'Tolima',
  country: 'Colombia'
};

class AgentOrchestrator {
  constructor() {
    this.studyArea = { ...DEFAULT_STUDY_AREA };
    this.isInitialized = false;
    this.eventHistory = [];
  }

  async initialize(config = {}) {
    console.log('[Orchestrator] Initializing agents...');

    await Promise.all([
      analysisAgent.initialize(config.analysis),
      predictionAgent.initialize(config.prediction),
      reportingAgent.initialize(config.reporting)
    ]);

    this._setupEventHandlers();
    this._setupStudyArea();

    this.isInitialized = true;
    console.log('[Orchestrator] All agents initialized successfully');
  }

  _setupEventHandlers() {
    analysisAgent.on('analysis:completed', (payload) => {
      console.log(`[Orchestrator] Analysis ${payload.analysisType} completed:`, payload.success);
      this._logEvent('ANALYSIS_COMPLETED', payload);
    });

    predictionAgent.on('prediction:completed', (payload) => {
      console.log(`[Orchestrator] Prediction ${payload.modelName} completed:`, payload.success);
      this._logEvent('PREDICTION_COMPLETED', payload);
    });

    reportingAgent.on('REPORT_READY', (payload) => {
      console.log('[Orchestrator] Report ready:', payload.reportId);
      this._logEvent('REPORT_READY', payload);
    });

    reportingAgent.on('report:generation:completed', (payload) => {
      if (!payload.success) {
        console.error('[Orchestrator] Report generation failed:', payload.error);
      }
    });
  }

  _setupStudyArea() {
    const { coordinates, ...rest } = this.studyArea;
    analysisAgent.updateStudyArea(this.studyArea);
    predictionAgent.updateStudyArea(this.studyArea);
  }

  async processDataPipeline(data) {
    if (!this.isInitialized) {
      throw new Error('Orchestrator not initialized. Call initialize() first.');
    }

    console.log('[Orchestrator] Starting data processing pipeline...');
    this._logEvent('DATA_INGESTED', { dataSize: data.length });

    try {
      const ndviResult = await analysisAgent.analyze(data, 'NDVI', this.studyArea);
      console.log('[Orchestrator] NDVI analysis completed');

      const ndwiResult = await analysisAgent.analyze(data, 'NDWI', this.studyArea);
      console.log('[Orchestrator] NDWI analysis completed');

      const morphResult = await analysisAgent.analyze(data, 'MORPHOLOGICAL', this.studyArea);
      console.log('[Orchestrator] Morphological analysis completed');

      const combinedData = {
        ndvi: ndviResult,
        ndwi: ndwiResult,
        morphological: morphResult,
        rawData: data
      };

      const predictionResult = await predictionAgent.predict(combinedData, 'FLOW_PREDICTION', this.studyArea);
      console.log('[Orchestrator] Flow prediction completed');

      const report = await reportingAgent.generateReport('comprehensive', this.studyArea);
      console.log('[Orchestrator] Report generation completed');

      return {
        success: true,
        analysis: combinedData,
        prediction: predictionResult,
        report: report,
        studyArea: this.studyArea
      };
    } catch (error) {
      console.error('[Orchestrator] Pipeline failed:', error);
      throw error;
    }
  }

  async runAnalysisOnly(data, analysisTypes = ['NDVI', 'NDWI']) {
    console.log('[Orchestrator] Running analysis-only pipeline...');
    this._logEvent('DATA_INGESTED', { dataSize: data.length });

    const results = {};
    for (const type of analysisTypes) {
      results[type] = await analysisAgent.analyze(data, type, this.studyArea);
    }

    return {
      success: true,
      analysis: results,
      studyArea: this.studyArea
    };
  }

  async runPredictionWithHistory(historicalData) {
    console.log('[Orchestrator] Running prediction with historical data...');

    const predictionResult = await predictionAgent.predict(historicalData, 'LSTM_FORECAST', this.studyArea);

    return {
      success: true,
      prediction: predictionResult,
      studyArea: this.studyArea
    };
  }

  async generateReport(reportType = 'comprehensive') {
    console.log(`[Orchestrator] Generating ${reportType} report...`);

    const report = await reportingAgent.generateReport(reportType, this.studyArea);

    return report;
  }

  updateStudyArea(newStudyArea) {
    this.studyArea = {
      ...this.studyArea,
      ...newStudyArea,
      coordinates: newStudyArea.coordinates || this.studyArea.coordinates
    };

    analysisAgent.updateStudyArea(this.studyArea);
    predictionAgent.updateStudyArea(this.studyArea);

    console.log('[Orchestrator] Study area updated:', this.studyArea.name);
  }

  _logEvent(eventType, payload) {
    const event = {
      type: eventType,
      timestamp: new Date().toISOString(),
      payload
    };
    this.eventHistory.push(event);

    if (this.eventHistory.length > 1000) {
      this.eventHistory.shift();
    }
  }

  getEventHistory(eventType = null) {
    if (eventType) {
      return this.eventHistory.filter(e => e.type === eventType);
    }
    return this.eventHistory;
  }

  getSystemStatus() {
    return {
      initialized: this.isInitialized,
      studyArea: this.studyArea,
      agents: {
        analysis: analysisAgent.getStatus(),
        prediction: predictionAgent.getStatus(),
        reporting: reportingAgent.getStatus()
      },
      eventHistory: {
        total: this.eventHistory.length,
        lastEvent: this.eventHistory[this.eventHistory.length - 1]
      }
    };
  }

  async shutdown() {
    console.log('[Orchestrator] Shutting down...');
    await Promise.all([
      analysisAgent.shutdown(),
      predictionAgent.shutdown(),
      reportingAgent.shutdown()
    ]);
    this.isInitialized = false;
    console.log('[Orchestrator] Shutdown complete');
  }
}

const orchestrator = new AgentOrchestrator();

if (require.main === module) {
  (async () => {
    try {
      await orchestrator.initialize({
        analysis: { maxConcurrent: 3, timeout: 30000 },
        prediction: { predictionHorizon: 24, confidenceLevel: 0.95 },
        reporting: { modelName: 'gpt-4', temperature: 0.3 }
      });

      const sampleData = [
        { lat: 4.45, lon: -75.15, ndvi: 0.65, ndwi: 0.12, elevation: 1200 },
        { lat: 4.46, lon: -75.14, ndvi: 0.58, ndwi: 0.18, elevation: 1350 }
      ];

      const result = await orchestrator.processDataPipeline(sampleData);
      console.log('\n[Orchestrator] Pipeline completed successfully');
      console.log('Prediction alert level:', result.prediction.alertLevel);

      const status = orchestrator.getSystemStatus();
      console.log('\n[Orchestrator] System Status:', JSON.stringify(status, null, 2));

      await orchestrator.shutdown();
    } catch (error) {
      console.error('[Orchestrator] Fatal error:', error);
      process.exit(1);
    }
  })();
}

module.exports = {
  orchestrator,
  AgentOrchestrator,
  AGENT_EVENTS,
  DEFAULT_STUDY_AREA
};
