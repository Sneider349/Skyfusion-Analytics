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

  async saveMorphologicalYearlyResult(data) {
    const session = this.getSession();
    const query = `
      MERGE (c:Catchment {id: $catchmentId})
      MERGE (y:Year {year: $year})
      MERGE (m:MorphologicalIndex {
        id: randomUUID(),
        type: $type,
        year: $year
      })
      SET m.mean = $mean,
          m.min = $min,
          m.max = $max,
          m.stdDev = $stdDev,
          m.coverage = $coverage,
          m.source = $source,
          m.processingDate = datetime(),
          m.validatedAt = CASE WHEN $validatedAt IS NOT NULL THEN datetime($validatedAt) ELSE NULL END,
          m.observations = $observations,
          m.trend = $trend,
          m.notes = $notes
      MERGE (m)-[:ANALYZED_IN]->(y)
      MERGE (m)-[:COMPUTED_FOR]->(c)
      RETURN m, y
    `;

    try {
      const result = await session.run(query, {
        catchmentId: data.catchmentId,
        year: data.year,
        type: data.type,
        mean: data.mean,
        min: data.min,
        max: data.max,
        stdDev: data.stdDev,
        coverage: data.coverage,
        source: data.source || 'GEE',
        validatedAt: data.validatedAt || null,
        observations: data.observations || null,
        trend: data.trend || null,
        notes: data.notes || null
      });

      console.log(`[Neo4jService] Morphological index ${data.type} for year ${data.year} saved`);
      return {
        morphological: result.records[0]?.get('m')?.properties,
        year: result.records[0]?.get('y')?.properties
      };
    } finally {
      await session.close();
    }
  }

  async getMorphologicalTrendByYear(catchmentId, startYear, endYear) {
    const session = this.getSession();
    const query = `
      MATCH (m:MorphologicalIndex)-[:ANALYZED_IN]->(y:Year),
            (m)-[:COMPUTED_FOR]->(c:Catchment {id: $catchmentId})
      WHERE y.year >= $startYear AND y.year <= $endYear
      RETURN m.type, y.year, m.mean, m.stdDev, m.trend
      ORDER BY m.type, y.year
    `;

    try {
      const result = await session.run(query, {
        catchmentId,
        startYear,
        endYear
      });

      return result.records.map(r => ({
        type: r.get('m.type'),
        year: r.get('y.year'),
        mean: r.get('m.mean'),
        stdDev: r.get('m.stdDev'),
        trend: r.get('m.trend')
      }));
    } finally {
      await session.close();
    }
  }

  async getMorphologicalIndexByType(catchmentId, indexType, year = null) {
    const session = this.getSession();
    const yearCondition = year ? 'AND y.year = $year' : '';
    const query = `
      MATCH (m:MorphologicalIndex)-[:ANALYZED_IN]->(y:Year),
            (m)-[:COMPUTED_FOR]->(c:Catchment {id: $catchmentId})
      WHERE m.type = $indexType ${yearCondition}
      RETURN m, y
      ORDER BY y.year DESC
    `;

    try {
      const result = await session.run(query, {
        catchmentId,
        indexType,
        ...(year && { year })
      });

      return result.records.map(r => ({
        ...r.get('m').properties,
        year: r.get('y').properties.year
      }));
    } finally {
      await session.close();
    }
  }

  async initializeMorphologicalIndexes() {
    const session = this.getSession();
    const constraints = [
      'CREATE INDEX morphological_year IF NOT EXISTS FOR (m:MorphologicalIndex) ON (m.year)',
      'CREATE INDEX morphological_type IF NOT EXISTS FOR (m:MorphologicalIndex) ON (m.type)',
      'CREATE INDEX year_value IF NOT EXISTS FOR (y:Year) ON (y.year)'
    ];

    try {
      for (const constraint of constraints) {
        await session.run(constraint);
      }
      console.log('[Neo4jService] Morphological indexes initialized');
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
