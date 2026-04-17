/**
 * Rutas de Sensores
 */

const express = require('express');
const router = express.Router();
const { getDriver, queries } = require('../config/neo4j');

router.get('/', async (req, res, next) => {
    try {
        const driver = getDriver();
        const session = driver.session({ database: 'neo4j' });

        const result = await session.run(`
            MATCH (s:Sensor)
            RETURN s.id as id, s.type as type, s.variable as variable,
                   s.unit as unit, s.status as status
        `);

        await session.close();

        const sensors = result.records.map(record => ({
            id: record.get('id'),
            type: record.get('type'),
            variable: record.get('variable'),
            unit: record.get('unit'),
            status: record.get('status')
        }));

        res.json({ sensors });
    } catch (error) {
        next(error);
    }
});

router.get('/:id/readings', async (req, res, next) => {
    try {
        const { id } = req.params;
        const { since, until } = req.query;

        const sinceDate = since || new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
        const untilDate = until || new Date().toISOString();

        const driver = getDriver();
        const session = driver.session({ database: 'neo4j' });

        const result = await session.run(`
            MATCH (sensor:Sensor {id: $sensorId})
            MATCH (reading:Reading)-[:CAPTURED_BY]->(sensor)
            WHERE reading.timestamp >= datetime($since) AND reading.timestamp <= datetime($until)
            RETURN reading.timestamp as timestamp, reading.value as value, reading.quality as quality
            ORDER BY timestamp DESC
            LIMIT 1000
        `, { sensorId: id, since: sinceDate, until: untilDate });

        await session.close();

        const readings = result.records.map(record => ({
            timestamp: record.get('timestamp'),
            value: record.get('value'),
            quality: record.get('quality')
        }));

        res.json({ sensor_id: id, since: sinceDate, until: untilDate, readings });
    } catch (error) {
        next(error);
    }
});

module.exports = router;
