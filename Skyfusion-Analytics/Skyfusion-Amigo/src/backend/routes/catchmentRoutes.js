/**
 * Rutas de Cuencas
 */

const express = require('express');
const router = express.Router();
const { getDriver, queries } = require('../config/neo4j');

router.get('/', async (req, res, next) => {
    try {
        const driver = getDriver();
        const session = driver.session({ database: 'neo4j' });

        const result = await session.run(`
            MATCH (c:Catchment)
            RETURN c.id as id, c.name as name, c.area_km2 as area_km2, 
                   c.population as population, c.location.latitude as lat,
                   c.location.longitude as lon
        `);

        await session.close();

        const catchments = result.records.map(record => ({
            id: record.get('id'),
            name: record.get('name'),
            area_km2: record.get('area_km2'),
            population: record.get('population'),
            location: {
                lat: record.get('lat'),
                lon: record.get('lon')
            }
        }));

        res.json({ catchments });
    } catch (error) {
        next(error);
    }
});

router.get('/:id', async (req, res, next) => {
    try {
        const { id } = req.params;
        const driver = getDriver();
        const session = driver.session({ database: 'neo4j' });

        const result = await session.run(`
            MATCH (c:Catchment {id: $id})
            OPTIONAL MATCH (s:Station)-[:MEASURES]->(c)
            RETURN c.id as id, c.name as name, c.area_km2 as area_km2,
                   c.population as population, c.location.latitude as lat,
                   c.location.longitude as lon,
                   collect(DISTINCT {id: s.id, name: s.name, type: s.type}) as stations
        `, { id });

        await session.close();

        if (result.records.length === 0) {
            return res.status(404).json({ error: 'Cuenca no encontrada' });
        }

        const record = result.records[0];
        res.json({
            catchment: {
                id: record.get('id'),
                name: record.get('name'),
                area_km2: record.get('area_km2'),
                population: record.get('population'),
                location: {
                    lat: record.get('lat'),
                    lon: record.get('lon')
                },
                stations: record.get('stations').filter(s => s.id !== null)
            }
        });
    } catch (error) {
        next(error);
    }
});

router.get('/:id/metrics', async (req, res, next) => {
    try {
        const { id } = req.params;
        const since = req.query.since || new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();

        const driver = getDriver();
        const session = driver.session({ database: 'neo4j' });

        const result = await session.run(`
            MATCH (c:Catchment {id: $catchmentId})
            OPTIONAL MATCH (s:Station)-[:MEASURES]->(c)
            OPTIONAL MATCH (sensor:Sensor)-[:LOCATED_AT]->(s)
            OPTIONAL MATCH (reading:Reading)-[:CAPTURED_BY]->(sensor)
            WHERE reading.timestamp > datetime($since)
            WITH c, sensor, reading
            ORDER BY reading.timestamp DESC
            RETURN sensor.id as sensor_id, sensor.type as sensor_type,
                   sensor.variable as variable, sensor.unit as unit,
                   collect(DISTINCT {timestamp: reading.timestamp, 
                                     value: reading.value})[-10..] as readings
        `, { catchmentId: id, since });

        await session.close();

        const metrics = result.records.map(record => ({
            sensor_id: record.get('sensor_id'),
            sensor_type: record.get('sensor_type'),
            variable: record.get('variable'),
            unit: record.get('unit'),
            readings: record.get('readings').filter(r => r.timestamp !== null)
        })).filter(m => m.sensor_id !== null);

        res.json({ catchment_id: id, since, metrics });
    } catch (error) {
        next(error);
    }
});

router.get('/:id/history', async (req, res, next) => {
    try {
        const { id } = req.params;
        const { start, end, interval = 'daily' } = req.query;

        const driver = getDriver();
        const session = driver.session({ database: 'neo4j' });

        const result = await session.run(`
            MATCH (c:Catchment {id: $catchmentId})
            OPTIONAL MATCH (p:Prediction)-[:FOR_CATCHMENT]->(c)
            WHERE p.timestamp >= datetime($start) AND p.timestamp <= datetime($end)
            RETURN p.variable as variable, p.horizon_days as horizon,
                   collect(DISTINCT {timestamp: p.timestamp, value: p.value}) as predictions
        `, { catchmentId: id, start, end });

        await session.close();

        const history = result.records.map(record => ({
            variable: record.get('variable'),
            horizon: record.get('horizon'),
            predictions: record.get('predictions').filter(p => p.timestamp !== null)
        }));

        res.json({ catchment_id: id, start, end, interval, history });
    } catch (error) {
        next(error);
    }
});

module.exports = router;
