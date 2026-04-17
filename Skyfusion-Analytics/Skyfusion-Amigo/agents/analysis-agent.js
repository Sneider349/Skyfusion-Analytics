'use strict';

const { EventEmitter } = require('events');
const { spawn } = require('child_process');
const path = require('path');
const neo4jService = require('../backend-node/src/services/neo4j-service');

const PYTHON_SCRIPTS = {
  NDVI: path.join(__dirname, '../skills/vision_tools/ndvi_analysis.py'),
  NDWI: path.join(__dirname, '../skills/vision_tools/ndwi_analysis.py'),
  MORPHOLOGICAL: path.join(__dirname, '../skills/vision_tools/morphological_analysis.py')
};

const DEFAULT_CONFIG = {
  maxConcurrent: 3,
  timeout: 30000,
  maxRetries: 3,
  retryDelay: 5000
};

class AnalysisAgent extends EventEmitter {
  constructor() {
    super();
    this.status = 'idle';
    this.activeTasks = 0;
    this.taskQueue = [];
    this.config = { ...DEFAULT_CONFIG };
  }

  async initialize(config = {}) {
    this.config = { ...this.config, ...config };
    this.status = 'ready';
    await neo4jService.connect();
    console.log('[AnalysisAgent] Initialized with config:', this.config);
  }

  async analyze(data, analysisType, studyArea) {
    if (this.status === 'idle') {
      throw new Error('Agent not initialized. Call initialize() first.');
    }

    return new Promise((resolve, reject) => {
      const task = {
        data,
        analysisType,
        studyArea,
        resolve,
        reject,
        retries: 0
      };

      if (this.activeTasks >= this.config.maxConcurrent) {
        this.taskQueue.push(task);
        return;
      }

      this._executeTask(task);
    });
  }

  async _executeTask(task) {
    this.activeTasks++;
    this.status = 'processing';
    this.emit('analysis:started', { analysisType: task.analysisType, studyArea: task.studyArea });

    const scriptPath = PYTHON_SCRIPTS[task.analysisType];

    if (!scriptPath) {
      const error = new Error(`Unsupported analysis type: ${task.analysisType}`);
      this._handleTaskError(task, error);
      return;
    }

    try {
      const result = await this._runPythonScript(scriptPath, {
        data: task.data,
        studyArea: task.studyArea
      });

      await this._saveAnalysisMetadata(task.analysisType, result, task.studyArea);

      this.emit('analysis:completed', { analysisType: task.analysisType, success: true });
      task.resolve(result);
    } catch (error) {
      this._handleTaskError(task, error);
    } finally {
      this.activeTasks--;
      this._processNextTask();
      if (this.activeTasks === 0) {
        this.status = 'ready';
      }
    }
  }

  async _runPythonScript(scriptPath, input) {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error(`Script timeout after ${this.config.timeout}ms`));
      }, this.config.timeout);

      const pythonProcess = spawn('python', [scriptPath], {
        stdio: ['pipe', 'pipe', 'pipe']
      });

      pythonProcess.stdin.write(JSON.stringify(input));
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
          reject(new Error(`Python script failed: ${stderr || `Exit code ${code}`}`));
        }
      });

      pythonProcess.on('error', (err) => {
        clearTimeout(timeout);
        reject(err);
      });
    });
  }

  async _handleTaskError(task, error) {
    console.error(`[AnalysisAgent] Task failed: ${error.message}`);

    if (task.retries < this.config.maxRetries) {
      task.retries++;
      console.log(`[AnalysisAgent] Retrying task (${task.retries}/${this.config.maxRetries})...`);
      setTimeout(() => this._executeTask(task), this.config.retryDelay);
    } else {
      this.emit('analysis:completed', { analysisType: task.analysisType, success: false, error: error.message });
      task.reject(error);
    }
  }

  _processNextTask() {
    if (this.taskQueue.length > 0 && this.activeTasks < this.config.maxConcurrent) {
      const nextTask = this.taskQueue.shift();
      this._executeTask(nextTask);
    }
  }

  async _saveAnalysisMetadata(analysisType, result, studyArea) {
    const metadata = {
      type: analysisType,
      timestamp: new Date().toISOString(),
      studyAreaId: studyArea.id,
      metrics: {
        indexValue: result.indexValue || result.ndvi || result.ndwi,
        mean: result.mean,
        stdDev: result.stdDev,
        coverage: result.coverage
      },
      processingDetails: {
        algorithm: result.algorithm || analysisType,
        resolution: result.resolution,
        bands: result.bands
      }
    };

    await neo4jService.saveAnalysisResult(metadata);
  }

  updateStudyArea(newStudyArea) {
    this.studyArea = {
      type: newStudyArea.type || 'polygon',
      coordinates: newStudyArea.coordinates,
      bounds: newStudyArea.bounds
    };
    console.log('[AnalysisAgent] Study area updated:', this.studyArea);
  }

  getStatus() {
    return {
      status: this.status,
      activeTasks: this.activeTasks,
      queuedTasks: this.taskQueue.length,
      config: this.config,
      studyArea: this.studyArea
    };
  }

  async shutdown() {
    this.status = 'idle';
    await neo4jService.disconnect();
    console.log('[AnalysisAgent] Shutdown complete');
  }
}

module.exports = new AnalysisAgent();
