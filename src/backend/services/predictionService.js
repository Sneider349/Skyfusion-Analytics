/**
 * Servicio de Predicciones
 */

const { getDriver } = require('../config/neo4j');
const { logger } = require('../config/logger');

async function getPredictions(catchmentId, options = {}) {
    const {
        startDate = null,
        endDate = null,
        modelType = null,
        horizon = null,
        limit = 100
    } = options;

    const driver = getDriver();
    const session = driver.session({ database: 'neo4j' });

    try {
        let query = `
            MATCH (p:Prediction)-[:FOR_CATCHMENT]->(c:Catchment {id: $catchmentId})
            WHERE 1=1
        `;
        const params = { catchmentId, limit };

        if (startDate) {
            query += ` AND p.timestamp >= datetime($startDate)`;
            params.startDate = startDate;
        }
        if (endDate) {
            query += ` AND p.timestamp <= datetime($endDate)`;
            params.endDate = endDate;
        }
        if (horizon) {
            query += ` AND p.horizon_days = $horizon`;
            params.horizon = horizon;
        }
        if (modelType) {
            query += ` AND p.model_type = $modelType`;
            params.modelType = modelType;
        }

        query += ` RETURN p ORDER BY p.timestamp DESC LIMIT $limit`;

        const result = await session.run(query, params);

        const predictions = result.records.map(record => {
            const p = record.get('p');
            return {
                timestamp: p.properties.timestamp?.toString() || new Date().toISOString(),
                horizon_days: p.properties.horizon_days,
                variable: p.properties.variable || 'caudal',
                value: p.properties.value,
                confidence: p.properties.confidence || 0.85,
                model_type: p.properties.model_type || 'default'
            };
        });

        return predictions;
    } catch (error) {
        logger.error('Error getting predictions:', error);
        throw error;
    } finally {
        await session.close();
    }
}

async function getCatchmentMetadata(catchmentId) {
    const driver = getDriver();
    const session = driver.session({ database: 'neo4j' });

    try {
        const result = await session.run(`
            MATCH (c:Catchment {id: $catchmentId})
            RETURN c.id as id, c.name as name, c.location as location
        `, { catchmentId });

        if (result.records.length === 0) {
            return null;
        }

        const record = result.records[0];
        return {
            id: record.get('id'),
            name: record.get('name'),
            location: record.get('location')
        };
    } finally {
        await session.close();
    }
}

async function startPredictionJob(io) {
    try {
        logger.info('Starting prediction job');

        const catchments = await getCatchments();

        for (const catchment of catchments) {
            await generatePredictions(catchment.id, io);
        }

        logger.info('Prediction job completed');
    } catch (error) {
        logger.error('Prediction job failed:', error);
    }
}

async function getCatchments() {
    const driver = getDriver();
    const session = driver.session({ database: 'neo4j' });

    try {
        const result = await session.run(`
            MATCH (c:Catchment)
            RETURN c.id as id, c.name as name
        `);

        return result.records.map(record => ({
            id: record.get('id'),
            name: record.get('name')
        }));
    } finally {
        await session.close();
    }
}

async function generatePredictions(catchmentId, io) {
    const predictions = [];

    for (let day = 1; day <= 7; day++) {
        const prediction = {
            day,
            caudal: parseFloat((4.2 - day * 0.1 + Math.random() * 0.2).toFixed(2)),
            flood_probability: parseFloat((Math.random() * 0.2).toFixed(2)),
            drought_probability: parseFloat((0.2 + day * 0.08).toFixed(2)),
            alert_level: day > 5 ? 1 : 0
        };
        predictions.push(prediction);
    }

    const driver = getDriver();
    const session = driver.session({ database: 'neo4j' });

    try {
        for (const pred of predictions) {
            await session.run(`
                MATCH (c:Catchment {id: $catchmentId})
                CREATE (p:Prediction {
                    timestamp: datetime(),
                    horizon_days: $horizon,
                    variable: 'caudal',
                    value: $value,
                    confidence: 0.85
                })
                CREATE (p)-[:FOR_CATCHMENT]->(c)
            `, {
                catchmentId,
                horizon: pred.day,
                value: pred.caudal
            });
        }
    } finally {
        await session.close();
    }

    io.to(`catchment:${catchmentId}`).emit('prediction', {
        catchment_id: catchmentId,
        predictions,
        generated_at: new Date().toISOString()
    });

    return predictions;
}

module.exports = { startPredictionJob, generatePredictions, getPredictions, getCatchmentMetadata };
