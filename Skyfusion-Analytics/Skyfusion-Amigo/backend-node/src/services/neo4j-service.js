'use strict';

const neo4j = require('neo4j-driver');

class Neo4jService {
  constructor() {
    this.driver = null;
    this.isConnected = false;
    this.config = {
      uri: process.env.NEO4J_URI || 'bolt://localhost:7687',
      user: process.env.NEO4J_USER || 'neo4j',
      password: process.env.NEO4J_PASSWORD || 'password',
      database: process.env.NEO4J_DATABASE || 'neo4j'
    };
  }

  async connect() {
    if (this.isConnected) return;

    try {
      this.driver = neo4j.driver(
        this.config.uri,
        neo4j.auth.basic(this.config.user, this.config.password),
        { maxConnectionPoolSize: 50 }
      );

      await this.driver.verifyConnectivity();
      this.isConnected = true;
      console.log('[Neo4jService] Connected successfully');
    } catch (error) {
      console.error('[Neo4jService] Connection failed:', error.message);
      throw error;
    }
  }

  async disconnect() {
    if (this.driver) {
      await this.driver.close();
      this.isConnected = false;
      console.log('[Neo4jService] Disconnected');
    }
  }

  getSession() {
    if (!this.isConnected) {
      throw new Error('Not connected to Neo4j. Call connect() first.');
    }
    return this.driver.session({ database: this.config.database });
  }

  async saveAnalysisResult(metadata) {
    const session = this.getSession();
    const query = `
      MATCH (s:StudyArea {id: $studyAreaId})
      MERGE (a:AnalysisResult {
        id: randomUUID(),
        type: $type,
        timestamp: datetime($timestamp),
        indexValue: $indexValue,
        mean: $mean,
        stdDev: $stdDev,
        coverage: $coverage
      })
      MERGE (a)-[:BELONGS_TO]->(s)
      RETURN a
    `;

    try {
      const result = await session.run(query, {
        studyAreaId: metadata.studyAreaId,
        type: metadata.type,
        timestamp: metadata.timestamp,
        indexValue: metadata.metrics?.indexValue || null,
        mean: metadata.metrics?.mean || null,
        stdDev: metadata.metrics?.stdDev || null,
        coverage: metadata.metrics?.coverage || null
      });

      console.log('[Neo4jService] Analysis result saved');
      return result.records[0]?.get('a')?.properties;
    } finally {
      await session.close();
    }
  }

  async savePrediction(prediction) {
    const session = this.getSession();
    const query = `
      MATCH (s:StudyArea {id: $studyAreaId})
      MERGE (p:Prediction {
        id: randomUUID(),
        modelName: $modelName,
        timestamp: datetime($timestamp),
        alertLevel: $alertLevel
      })
      MERGE (p)-[:PREDICTS_FOR]->(s)
      WITH p, prediction
      UNWIND prediction.predictions AS pred
      CREATE (dp:DataPoint {
        value: pred,
        timestamp: datetime()
      })
      CREATE (p)-[:CONTAINS]->(dp)
      RETURN p
    `;

    try {
      const result = await session.run(query, {
        studyAreaId: prediction.studyAreaId,
        modelName: prediction.modelName,
        timestamp: prediction.timestamp,
        alertLevel: prediction.alertLevel,
        prediction: prediction
      });

      console.log('[Neo4jService] Prediction saved');
      return result.records[0]?.get('p')?.properties;
    } finally {
      await session.close();
    }
  }

  async saveReport(report) {
    const session = this.getSession();
    const query = `
      MATCH (s:StudyArea {id: $studyAreaId})
      MERGE (r:Report {
        id: $id,
        type: $type,
        timestamp: datetime($timestamp),
        narrative: $narrative,
        metadata: $metadata
      })
      MERGE (r)-[:ABOUT]->(s)
      RETURN r
    `;

    try {
      const result = await session.run(query, {
        studyAreaId: report.studyAreaId,
        id: report.id,
        type: report.type,
        timestamp: report.timestamp,
        narrative: report.narrative,
        metadata: JSON.stringify(report.metadata)
      });

      console.log('[Neo4jService] Report saved');
      return result.records[0]?.get('r')?.properties;
    } finally {
      await session.close();
    }
  }

  async getAnalysisResults(studyAreaId) {
    const session = this.getSession();
    const query = `
      MATCH (a:AnalysisResult)-[:BELONGS_TO]->(s:StudyArea {id: $studyAreaId})
      RETURN a
      ORDER BY a.timestamp DESC
      LIMIT 10
    `;

    try {
      const result = await session.run(query, { studyAreaId });
      return result.records.map(r => r.get('a').properties);
    } finally {
      await session.close();
    }
  }

  async getLatestPredictions(studyAreaId) {
    const session = this.getSession();
    const query = `
      MATCH (p:Prediction)-[:PREDICTS_FOR]->(s:StudyArea {id: $studyAreaId})
      OPTIONAL MATCH (p)-[:CONTAINS]->(dp:DataPoint)
      RETURN p, collect(dp.value) as predictions
      ORDER BY p.timestamp DESC
      LIMIT 1
    `;

    try {
      const result = await session.run(query, { studyAreaId });
      if (result.records.length > 0) {
        const record = result.records[0];
        return {
          ...record.get('p').properties,
          predictions: record.get('predictions')
        };
      }
      return null;
    } finally {
      await session.close();
    }
  }

  async getHistoricalData(studyAreaId) {
    const session = this.getSession();
    const query = `
      MATCH (a:AnalysisResult)-[:BELONGS_TO]->(s:StudyArea {id: $studyAreaId})
      RETURN a
      ORDER BY a.timestamp DESC
      LIMIT 100
    `;

    try {
      const result = await session.run(query, { studyAreaId });
      return result.records.map(r => r.get('a').properties);
    } finally {
      await session.close();
    }
  }

  async createStudyAreaNode(studyArea) {
    const session = this.getSession();
    const query = `
      MERGE (s:StudyArea {id: $id})
      SET s.name = $name,
          s.type = $type,
          s.coordinates = $coordinates,
          s.river = $river,
          s.municipality = $municipality,
          s.department = $department,
          s.country = $country,
          s.createdAt = datetime()
      RETURN s
    `;

    try {
      const result = await session.run(query, {
        id: studyArea.id,
        name: studyArea.name,
        type: studyArea.type,
        coordinates: JSON.stringify(studyArea.coordinates),
        river: studyArea.river,
        municipality: studyArea.municipality,
        department: studyArea.department,
        country: studyArea.country
      });

      console.log('[Neo4jService] Study area node created/updated');
      return result.records[0]?.get('s').properties;
    } finally {
      await session.close();
    }
  }

  async executeQuery(query, params = {}) {
    const session = this.getSession();
    try {
      const result = await session.run(query, params);
      return result.records;
    } finally {
      await session.close();
    }
  }
}

module.exports = new Neo4jService();
