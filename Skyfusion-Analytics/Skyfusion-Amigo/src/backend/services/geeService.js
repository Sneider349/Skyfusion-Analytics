/**
 * Servicio de Google Earth Engine
 * Procesa imágenes satelitales para extraer índices ambientales
 */

const ee = require('@google/earthengine');
const { logger } = require('../config/logger');

let initialized = false;

const COMBEIMA_GEOMETRY = {
    type: 'Polygon',
    coordinates: [[
        [-75.30, 4.55],
        [-75.30, 4.35],
        [-75.10, 4.35],
        [-75.10, 4.55],
        [-75.30, 4.55]
    ]]
};

async function initializeGEE() {
    if (initialized) return true;

    try {
        const privateKey = process.env.GOOGLE_EARTH_ENGINE_PRIVATE_KEY;
        const clientEmail = process.env.GOOGLE_EARTH_ENGINE_SERVICE_ACCOUNT;

        const privateKeyParsed = privateKey
            .replace(/\\n/g, '\n')
            .replace(/^"|"$/g, '');

        const credentials = {
            private_key: privateKeyParsed,
            client_email: clientEmail
        };

        await ee.authenticate(credentials);
        await ee.initialize();

        initialized = true;
        logger.info('Google Earth Engine initialized successfully');
        return true;
    } catch (error) {
        logger.error('Failed to initialize Google Earth Engine:', error);
        return false;
    }
}

async function getNDVI(date = null) {
    try {
        const initialized = await initializeGEE();
        if (!initialized) {
            return { error: 'GEE not initialized', value: null };
        }

        const startDate = date || '2024-01-01';
        const endDate = date || '2024-12-31';

        const collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
            .filterDate(startDate, endDate)
            .filterBounds(ee.Geometry(COMBEIMA_GEOMETRY))
            .filter(ee.Filter.lt('CLOUD_COVER', 30));

        const image = collection.median();

        const ndvi = image.expression(
            '(NIR - RED) / (NIR + RED)', {
                'NIR': image.select('SR_B5'),
                'RED': image.select('SR_B4')
            }
        );

        const ndviValue = ndvi.reduceRegion({
            geometry: ee.Geometry(COMBEIMA_GEOMETRY),
            reducer: ee.Reducer.mean(),
            scale: 30
        }).getInfo();

        return {
            index: 'NDVI',
            value: ndviValue.NIR ? (ndviValue.NIR - ndviValue.RED) / (ndviValue.NIR + ndviValue.RED) : null,
            date: endDate,
            source: 'Landsat 8'
        };
    } catch (error) {
        logger.error('Error getting NDVI:', error);
        return { error: error.message, value: null };
    }
}

async function getNDWI(date = null) {
    try {
        const initialized = await initializeGEE();
        if (!initialized) {
            return { error: 'GEE not initialized', value: null };
        }

        const startDate = date || '2024-01-01';
        const endDate = date || '2024-12-31';

        const collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
            .filterDate(startDate, endDate)
            .filterBounds(ee.Geometry(COMBEIMA_GEOMETRY))
            .filter(ee.Filter.lt('CLOUD_COVER', 30));

        const image = collection.median();

        const ndwi = image.expression(
            '(GREEN - NIR) / (GREEN + NIR)', {
                'GREEN': image.select('SR_B3'),
                'NIR': image.select('SR_B5')
            }
        );

        const ndwiValue = ndwi.reduceRegion({
            geometry: ee.Geometry(COMBEIMA_GEOMETRY),
            reducer: ee.Reducer.mean(),
            scale: 30
        }).getInfo();

        return {
            index: 'NDWI',
            value: ndwiValue.GREEN ? (ndwiValue.GREEN - ndwiValue.NIR) / (ndwiValue.GREEN + ndwiValue.NIR) : null,
            date: endDate,
            source: 'Landsat 8'
        };
    } catch (error) {
        logger.error('Error getting NDWI:', error);
        return { error: error.message, value: null };
    }
}

async function getTemperature(date = null) {
    try {
        const initialized = await initializeGEE();
        if (!initialized) {
            return { error: 'GEE not initialized', value: null };
        }

        const startDate = date || '2024-01-01';
        const endDate = date || '2024-12-31';

        const collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
            .filterDate(startDate, endDate)
            .filterBounds(ee.Geometry(COMBEIMA_GEOMETRY));

        const image = collection.median();

        const temp = image.expression(
            'ST_B10 * 0.00341802 + 149.0 - 273.15', {
                'ST_B10': image.select('ST_B10')
            }
        );

        const tempValue = temp.reduceRegion({
            geometry: ee.Geometry(COMBEIMA_GEOMETRY),
            reducer: ee.Reducer.mean(),
            scale: 30
        }).getInfo();

        return {
            index: 'Temperature',
            value: tempValue.ST_B10 || null,
            unit: '°C',
            date: endDate,
            source: 'Landsat 8'
        };
    } catch (error) {
        logger.error('Error getting Temperature:', error);
        return { error: error.message, value: null };
    }
}

async function getSatelliteImage(date = null) {
    try {
        const initialized = await initializeGEE();
        if (!initialized) {
            return { error: 'GEE not initialized', value: null };
        }

        const startDate = date || '2024-01-01';
        const endDate = date || '2024-12-31';

        const collection = ee.ImageCollection('SENTINEL-2')
            .filterDate(startDate, endDate)
            .filterBounds(ee.Geometry(COMBEIMA_GEOMETRY))
            .filter(ee.Filter.lt('CLOUD_COVER', 20));

        const image = collection.median();

        return {
            index: 'RGB',
            date: endDate,
            source: 'Sentinel-2',
            bands: ['B4', 'B3', 'B2'],
            resolution: 10
        };
    } catch (error) {
        logger.error('Error getting Satellite Image:', error);
        return { error: error.message, value: null };
    }
}

async function getAllIndices(date = null) {
    const [ndvi, ndwi, temperature] = await Promise.all([
        getNDVI(date),
        getNDWI(date),
        getTemperature(date)
    ]);

    return { ndvi, ndwi, temperature };
}

module.exports = {
    initializeGEE,
    getNDVI,
    getNDWI,
    getTemperature,
    getSatelliteImage,
    getAllIndices
};
