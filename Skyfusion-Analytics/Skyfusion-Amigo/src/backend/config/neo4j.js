/**
 * Configuración de Neo4j
 */

const neo4j = require('neo4j-driver');
const { logger } = require('./logger');

let driver = null;

const NEO4J_URI = process.env.NEO4J_URI || 'bolt://127.0.0.1:7687';
const NEO4J_USER = process.env.NEO4J_USER || 'neo4j';
const NEO4J_PASSWORD = process.env.NEO4J_PASSWORD || 'password123';

async function connectNeo4j() {
    try {
        driver = neo4j.driver(
            NEO4J_URI,
            neo4j.auth.basic(NEO4J_USER, NEO4J_PASSWORD),
            {
                encrypted: 'ENCRYPTION_OFF',
                trust: 'TRUST_ALL_CERTIFICATES',
                maxConnectionLifetime: 3 * 60 * 60 * 1000,
                maxConnectionPoolSize: 50,
                connectionAcquisitionTimeout: 60 * 1000
            }
        );

        await driver.verifyConnectivity();
        logger.info('Neo4j connectivity verified');

        await initializeConstraints();

        return driver;
    } catch (error) {
        logger.error('Failed to connect to Neo4j:', error);
        throw error;
    }
}

async function initializeConstraints() {
    const session = driver.session({ database: 'neo4j' });

    try {
        await session.run(`
            CREATE CONSTRAINT IF NOT EXISTS FOR (c:Catchment) 
            REQUIRE c.id IS UNIQUE
        `);

        await session.run(`
            CREATE CONSTRAINT IF NOT EXISTS FOR (s:Station) 
            REQUIRE s.id IS UNIQUE
        `);

        await session.run(`
            CREATE CONSTRAINT IF NOT EXISTS FOR (sensor:Sensor) 
            REQUIRE sensor.id IS UNIQUE
        `);

        logger.info('Neo4j constraints initialized');
    } finally {
        await session.close();
    }
}

function getDriver() {
    if (!driver) {
        throw new Error('Neo4j driver not initialized');
    }
    return driver;
}

async function checkConnection() {
    try {
        const session = driver.session({ database: 'neo4j' });
        await session.run('RETURN 1');
        await session.close();
        return true;
    } catch (error) {
        logger.error('Neo4j connection check failed:', error);
        return false;
    }
}

async function close() {
    if (driver) {
        await driver.close();
        driver = null;
        logger.info('Neo4j connection closed');
    }
}

const queries = {
    createCatchment: `
        CREATE (c:Catchment {
            id: $id,
            name: $name,
            area_km2: $area_km2,
            population: $population,
            location: point({latitude: $lat, longitude: $lon}),
            created_at: datetime()
        })
        RETURN c
    `,

    createStation: `
        CREATE (s:Station {
            id: $id,
            name: $name,
            type: $type,
            lat: $lat,
            lon: $lon,
            status: 'active',
            created_at: datetime()
        })
        RETURN s
    `,

    createSensor: `
        CREATE (sensor:Sensor {
            id: $id,
            type: $type,
            variable: $variable,
            unit: $unit,
            status: 'active',
            created_at: datetime()
        })
        RETURN sensor
    `,

    stationMeasuresCatchment: `
        MATCH (s:Station {id: $stationId})
        MATCH (c:Catchment {id: $catchmentId})
        MERGE (s)-[:MEASURES {since: datetime()}]->(c)
    `,

    sensorAtStation: `
        MATCH (sensor:Sensor {id: $sensorId})
        MATCH (s:Station {id: $stationId})
        MERGE (sensor)-[:LOCATED_AT {since: datetime()}]->(s)
    `,

    createReading: `
        MATCH (sensor:Sensor {id: $sensorId})
        CREATE (r:Reading {
            timestamp: datetime($timestamp),
            value: $value,
            quality: $quality
        })
        CREATE (r)-[:CAPTURED_BY]->(sensor)
        RETURN r
    `,

    createPrediction: `
        MATCH (c:Catchment {id: $catchmentId})
        CREATE (p:Prediction {
            timestamp: datetime($timestamp),
            horizon_days: $horizon_days,
            variable: $variable,
            value: $value,
            confidence: $confidence
        })
        CREATE (p)-[:FOR_CATCHMENT]->(c)
        RETURN p
    `,

    getCatchmentMetrics: `
        MATCH (c:Catchment {id: $catchmentId})
        OPTIONAL MATCH (s:Station)-[:MEASURES]->(c)
        OPTIONAL MATCH (sensor:Sensor)-[:LOCATED_AT]->(s)
        OPTIONAL MATCH (reading:Reading)-[:CAPTURED_BY]->(sensor)
        WHERE reading.timestamp > datetime($since)
        RETURN c, collect(DISTINCT s) as stations, collect(DISTINCT {sensor: sensor, readings: reading}) as sensors
    `,

    getActiveAlerts: `
        MATCH (a:Alert)
        WHERE a.status = 'active'
        RETURN a
        ORDER BY a.severity DESC
        LIMIT 50
    `
};

module.exports = {
    connectNeo4j,
    getDriver,
    checkConnection,
    close,
    queries
};
