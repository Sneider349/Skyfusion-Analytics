'use strict';

const { EventEmitter } = require('events');
const { spawn } = require('child_process');
const path = require('path');
const neo4jService = require('../backend-node/src/services/neo4j-service');

const ML_MODELS = {
  FLOW_PREDICTION: path.join(__dirname, '../skills/ml_tools/flow_prediction.py'),
  VARIABILITY_ANALYSIS: path.join(__dirname, '../skills/ml_tools/variability_analysis.py'),
  LSTM_FORECAST: path.join(__dirname, '../skills/ml_tools/lstm_forecast.py')
};

const DEFAULT_CONFIG = {
  predictionHorizon: 24,
  confidenceLevel: 0.95,
  timeout: 60000,
  maxRetries: 3,
  retryDelay: 5000
};

class PredictionAgent extends EventEmitter {
  constructor() {
    super();
    this.status = 'idle';
    this.loadedModels = new Map();
    this.config = { ...DEFAULT_CONFIG };
    this.studyArea = null;
  }

  async initialize(config = {}) {
    this.config = { ...this.config, ...config };
    this.status = 'ready';
    await neo4jService.connect();
    console.log('[PredictionAgent] Initialized with config:', this.config);
  }

  async loadModel(modelName) {
    const modelPath = ML_MODELS[modelName];

    if (!modelPath) {
      throw new Error(`Unknown model: ${modelName}. Available: ${Object.keys(ML_MODELS).join(', ')}`);
    }

    try {
      console.log(`[PredictionAgent] Loading model: ${modelName}`);
      this.loadedModels.set(modelName, {
        path: modelPath,
        loadedAt: new Date(),
        status: 'ready'
      });
      this.emit('model:loaded', { modelName });
      return true;
    } catch (error) {
      console.error(`[PredictionAgent] Failed to load model ${modelName}:`, error);
      return false;
    }
  }

  async predict(inputData, modelName = 'FLOW_PREDICTION', studyArea = null) {
    if (this.status === 'idle') {
      throw new Error('Agent not initialized. Call initialize() first.');
    }

    const targetStudyArea = studyArea || this.studyArea;
    this.emit('prediction:requested', { modelName, studyArea: targetStudyArea });

    return this._executePredictionWithRetry(inputData, modelName, targetStudyArea, 0);
  }

  async _executePredictionWithRetry(inputData, modelName, studyArea, retryCount) {
    try {
      const result = await this._runPrediction(inputData, modelName, studyArea);

      await this._savePredictionToNeo4j(result, modelName, studyArea);

      this.emit('prediction:completed', { modelName, success: true });
      return this._formatPredictionResult(result);
    } catch (error) {
      console.error(`[PredictionAgent] Prediction failed (attempt ${retryCount + 1}):`, error.message);

      if (retryCount < this.config.maxRetries) {
        await this._delay(this.config.retryDelay * (retryCount + 1));
        return this._executePredictionWithRetry(inputData, modelName, studyArea, retryCount + 1);
      }

      this.emit('prediction:completed', { modelName, success: false, error: error.message });
      throw error;
    }
  }

  async _runPrediction(inputData, modelName, studyArea) {
    const modelPath = ML_MODELS[modelName];

    if (!modelPath) {
      throw new Error(`Model not found: ${modelName}`);
    }

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error(`Prediction timeout after ${this.config.timeout}ms`));
      }, this.config.timeout);

      const pythonProcess = spawn('python', [modelPath], {
        stdio: ['pipe', 'pipe', 'pipe']
      });

      const payload = {
        data: inputData,
        studyArea: studyArea,
        horizon: this.config.predictionHorizon,
        confidence: this.config.confidenceLevel
      };

      pythonProcess.stdin.write(JSON.stringify(payload));
      pythonProcess.stdin.end();

      let stdout = '';
      let stderr = '';

      pythonProcess.stdout.on('data', (chunk) => { stdout += chunk.toString(); });
      pythonProcess.stderr.on('data', (chunk) => { stderr += chunk.toString(); });

      pythonProcess.on('close', (code) => {
        clearTimeout(timeout);
        if (code === 0) {
          try {
            resolve(JSON.parse(stdout));
          } catch {
            resolve({ raw: stdout });
          }
        } else {
          reject(new Error(`Model execution failed: ${stderr || `Exit code ${code}`}`));
        }
      });

      pythonProcess.on('error', (err) => {
        clearTimeout(timeout);
        reject(err);
      });
    });
  }

  async _savePredictionToNeo4j(prediction, modelName, studyArea) {
    const predictionRecord = {
      modelName,
      timestamp: new Date().toISOString(),
      studyAreaId: studyArea?.id || 'default',
      predictions: prediction.predictions || [],
      actualValues: prediction.actualValues || [],
      confidenceInterval: {
        lower: prediction.confidenceInterval?.lower,
        upper: prediction.confidenceInterval?.upper
      },
      metrics: {
        rmse: prediction.metrics?.rmse,
        mae: prediction.metrics?.mae,
        r2: prediction.metrics?.r2
      },
      alertLevel: this._calculateAlertLevel(prediction),
      metadata: {
        horizon: this.config.predictionHorizon,
        confidence: this.config.confidenceLevel
      }
    };

    await neo4jService.savePrediction(predictionRecord);
  }

  _calculateAlertLevel(prediction) {
    const predictions = prediction.predictions || [];

    if (!predictions.length) return 'LOW';

    const maxPredicted = Math.max(...predictions);
    const minPredicted = Math.min(...predictions);
    const variability = maxPredicted - minPredicted;

    if (variability > 50) return 'CRITICAL';
    if (variability > 30) return 'HIGH';
    if (variability > 15) return 'MEDIUM';
    return 'LOW';
  }

  _formatPredictionResult(rawResult) {
    return {
      success: true,
      predictions: rawResult.predictions || [],
      confidenceInterval: rawResult.confidenceInterval || {},
      alertLevel: this._calculateAlertLevel(rawResult),
      metrics: rawResult.metrics || {},
      summary: this._generateSummary(rawResult)
    };
  }

  _generateSummary(prediction) {
    const preds = prediction.predictions || [];
    if (!preds.length) return 'No prediction data available.';

    const trend = preds[preds.length - 1] > preds[0] ? 'increasing' : 'decreasing';
    const avg = preds.reduce((a, b) => a + b, 0) / preds.length;

    return `Flow prediction indicates a ${trend} trend with average value ${avg.toFixed(2)} over ${this.config.predictionHorizon} hours.`;
  }

  _delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  updateStudyArea(newStudyArea) {
    this.studyArea = {
      id: newStudyArea.id,
      type: newStudyArea.type || 'polygon',
      coordinates: newStudyArea.coordinates,
      bounds: newStudyArea.bounds,
      river: newStudyArea.river || 'Combeima',
      municipality: newStudyArea.municipality || 'Ibagué'
    };
    console.log('[PredictionAgent] Study area updated:', this.studyArea);
  }

  getStatus() {
    return {
      status: this.status,
      loadedModels: Array.from(this.loadedModels.keys()),
      config: this.config,
      studyArea: this.studyArea
    };
  }

  async shutdown() {
    this.status = 'idle';
    this.loadedModels.clear();
    await neo4jService.disconnect();
    console.log('[PredictionAgent] Shutdown complete');
  }
}

module.exports = new PredictionAgent();
