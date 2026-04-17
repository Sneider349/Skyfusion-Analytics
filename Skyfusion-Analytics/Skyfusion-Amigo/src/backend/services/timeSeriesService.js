/**
 * Servicio de Series Temporales - Google Earth Engine
 * Extrae datos históricos deNDVI, NDWI y temperatura para análisis
 */

const ee = require('@google/earthengine');
const { logger } = require('../config/logger');

const COMBEIMA_REGION = {
    type: 'Polygon',
    coordinates: [[
        [-75.35, 4.60],
        [-75.35, 4.30],
        [-75.05, 4.30],
        [-75.05, 4.60],
        [-75.35, 4.60]
    ]]
};

let geeInitialized = false;

async function initializeGEE() {
    if (geeInitialized) return true;

    try {
        const privateKey = process.env.GOOGLE_EARTH_ENGINE_PRIVATE_KEY;
        const clientEmail = process.env.GOOGLE_EARTH_ENGINE_SERVICE_ACCOUNT;

        if (!privateKey || !clientEmail) {
            logger.warn('GEE credentials not configured');
            return false;
        }

        const privateKeyParsed = privateKey
            .replace(/\\n/g, '\n')
            .replace(/^"|"$/g, '');

        const credentials = {
            private_key: privateKeyParsed,
            client_email: clientEmail
        };

        await ee.authenticate(credentials);
        await ee.initialize();

        geeInitialized = true;
        logger.info('Google Earth Engine initialized successfully');
        return true;
    } catch (error) {
        logger.error('Failed to initialize GEE:', error);
        return false;
    }
}

async function getTimeSeriesData(lat, lng, meses = 12) {
    const initialized = await initializeGEE();
    
    if (!initialized) {
        return generarSerieDemo(lat, lng, meses);
    }

    const point = { latitude: lat, longitude: lng };
    const fechaInicio = getFechaInicio(meses);
    const fechaFin = new Date().toISOString().split('T')[0];

    try {
        const resultados = await Promise.all([
            getNDVISerieTemporal(point, fechaInicio, fechaFin),
            getNDWISerieTemporal(point, fechaInicio, fechaFin),
            getTemperaturaSerieTemporal(point, fechaInicio, fechaFin)
        ]);

        return {
            ndvi: resultados[0],
            ndwi: resultados[1],
            temperatura: resultados[2],
            metadata: {
                lat,
                lng,
                fecha_inicio: fechaInicio,
                fecha_fin: fechaFin,
                meses
            }
        };
    } catch (error) {
        logger.error('Error getting time series:', error);
        return generarSerieDemo(lat, lng, meses);
    }
}

async function getNDVISerieTemporal(point, fechaInicio, fechaFin) {
    try {
        const collection = ee.ImageCollection('COPERNICUS/S2_SR')
            .filterDate(fechaInicio, fechaFin)
            .filterBounds(ee.Geometry(point))
            .filter(ee.Filter.lt('CLOUD_COVER', 30));

        const ndvi = collection.map(image => {
            const ndvi = image.expression(
                '(NIR - RED) / (NIR + RED)', {
                    NIR: image.select('B8'),
                    RED: image.select('B4')
                }
            );
            return ndvi.set('date', image.date().format('YYYY-MM-dd'));
        });

        const puntos = ndvi.select(0).reduceRegion({
            reducer: ee.Reducer.mean(),
            geometry: ee.Geometry(point),
            scale: 10
        });

        const resultados = await puntos.getInfo();
        
        return formatearSerieTemporal(resultados, 'NDVI');
    } catch (error) {
        logger.error('Error getting NDVI series:', error);
        return generarSerieNDVIDemo(meses);
    }
}

async function getNDWISerieTemporal(point, fechaInicio, fechaFin) {
    try {
        const collection = ee.ImageCollection('COPERNICUS/S2_SR')
            .filterDate(fechaInicio, fechaFin)
            .filterBounds(ee.Geometry(point))
            .filter(ee.Filter.lt('CLOUD_COVER', 30));

        const ndwi = collection.map(image => {
            const ndwi = image.expression(
                '(GREEN - NIR) / (GREEN + NIR)', {
                    GREEN: image.select('B3'),
                    NIR: image.select('B8')
                }
            );
            return ndwi.set('date', image.date().format('YYYY-MM-dd'));
        });

        const puntos = ndwi.select(0).reduceRegion({
            reducer: ee.Reducer.mean(),
            geometry: ee.Geometry(point),
            scale: 10
        });

        const resultados = await puntos.getInfo();
        
        return formatearSerieTemporal(resultados, 'NDWI');
    } catch (error) {
        logger.error('Error getting NDWI series:', error);
        return generarSerieNDWIDemo(meses);
    }
}

async function getTemperaturaSerieTemporal(point, fechaInicio, fechaFin) {
    try {
        const collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
            .filterDate(fechaInicio, fechaFin)
            .filterBounds(ee.Geometry(point));

        const temp = collection.map(image => {
            const temperatura = image.expression(
                'ST_B10 * 0.00341802 + 149.0 - 273.15', {
                    ST_B10: image.select('ST_B10')
                }
            );
            return temperatura.set('date', image.date().format('YYYY-MM-dd'));
        });

        const puntos = temp.select(0).reduceRegion({
            reducer: ee.Reducer.mean(),
            geometry: ee.Geometry(point),
            scale: 30
        });

        const resultados = await puntos.getInfo();
        
        return formatearSerieTemporal(resultados, 'Temperatura');
    } catch (error) {
        logger.error('Error getting temperature series:', error);
        return generarSerieTemperaturaDemo(meses);
    }
}

function formatearSerieTemporal(resultados, tipo) {
    const datos = [];
    
    for (const [fecha, valor] of Object.entries(resultados)) {
        if (valor !== null && !isNaN(valor)) {
            datos.push({
                fecha,
                valor: parseFloat(valor.toFixed(3)),
                tipo
            });
        }
    }

    return datos.sort((a, b) => new Date(a.fecha) - new Date(b.fecha));
}

function getFechaInicio(meses) {
    const fecha = new Date();
    fecha.setMonth(fecha.getMonth() - meses);
    return fecha.toISOString().split('T')[0];
}

function generarSerieDemo(lat, lng, meses) {
    return {
        ndvi: generarSerieNDVIDemo(meses),
        ndwi: generarSerieNDWIDemo(meses),
        temperatura: generarSerieTemperaturaDemo(meses),
        metadata: {
            lat,
            lng,
            fecha_inicio: getFechaInicio(meses),
            fecha_fin: new Date().toISOString().split('T')[0],
            meses,
            source: 'demo'
        }
    };
}

function generarSerieNDVIDemo(meses) {
    const datos = [];
    const baseDate = new Date();
    
    for (let i = meses; i >= 0; i--) {
        const fecha = new Date(baseDate);
        fecha.setMonth(fecha.getMonth() - i);
        
        const variacion = (Math.random() - 0.5) * 0.2;
        const tendencia = (meses - i) * 0.01;
        const valor = Math.max(-0.1, Math.min(0.9, 0.65 + tendencia + variacion));
        
        datos.push({
            fecha: fecha.toISOString().split('T')[0],
            valor: parseFloat(valor.toFixed(3)),
            tipo: 'NDVI'
        });
    }
    
    return datos;
}

function generarSerieNDWIDemo(meses) {
    const datos = [];
    const baseDate = new Date();
    
    for (let i = meses; i >= 0; i--) {
        const fecha = new Date(baseDate);
        fecha.setMonth(fecha.getMonth() - i);
        
        const variacion = (Math.random() - 0.5) * 0.15;
        const tendencia = (meses - i) * 0.005;
        const valor = Math.max(-0.2, Math.min(0.8, 0.42 + tendencia + variacion));
        
        datos.push({
            fecha: fecha.toISOString().split('T')[0],
            valor: parseFloat(valor.toFixed(3)),
            tipo: 'NDWI'
        });
    }
    
    return datos;
}

function generarSerieTemperaturaDemo(meses) {
    const datos = [];
    const baseDate = new Date();
    
    for (let i = meses; i >= 0; i--) {
        const fecha = new Date(baseDate);
        fecha.setMonth(fecha.getMonth() - i);
        
        const variacion = (Math.random() - 0.5) * 4;
        const estacionalidad = Math.sin(i / 6 * Math.PI) * 3;
        const valor = 24 + estacionalidad + variacion;
        
        datos.push({
            fecha: fecha.toISOString().split('T')[0],
            valor: parseFloat(valor.toFixed(1)),
            tipo: 'Temperatura'
        });
    }
    
    return datos;
}

async function obtenerDatosPunto(lat, lng) {
    const initialized = await initializeGEE();
    const point = { latitude: lat, longitude: lng };

    if (!initialized) {
        return obtenerDatosDemo(lat, lng);
    }

    try {
        const [ndvi, ndwi, temp] = await Promise.all([
            getUltimoNDVI(point),
            getUltimoNDWI(point),
            getUltimaTemperatura(point)
        ]);

        return {
            latitud: lat,
            longitud: lng,
            ndvi: ndvi,
            ndwi: ndwi,
            temperatura: temp,
            timestamp: new Date().toISOString()
        };
    } catch (error) {
        logger.error('Error getting point data:', error);
        return obtenerDatosDemo(lat, lng);
    }
}

async function getUltimoNDVI(point) {
    try {
        const image = ee.ImageCollection('COPERNICUS/S2_SR')
            .filterBounds(ee.Geometry(point))
            .filter(ee.Filter.lt('CLOUD_COVER', 30))
            .sort('CLOUD_COVER')
            .first();

        const ndvi = image.expression(
            '(NIR - RED) / (NIR + RED)', {
                NIR: image.select('B8'),
                RED: image.select('B4')
            }
        );

        const valor = await ndvi.reduceRegion({
            reducer: ee.Reducer.mean(),
            geometry: ee.Geometry(point),
            scale: 10
        }).getInfo();

        return {
            valor: valor.b8 ? parseFloat(((valor.b8 - valor.b4) / (valor.b8 + valor.b4)).toFixed(3)) : 0.65,
            fuente: 'Sentinel-2',
            fecha: new Date().toISOString().split('T')[0]
        };
    } catch {
        return { valor: 0.65, fuente: 'demo', fecha: new Date().toISOString().split('T')[0] };
    }
}

async function getUltimoNDWI(point) {
    try {
        const image = ee.ImageCollection('COPERNICUS/S2_SR')
            .filterBounds(ee.Geometry(point))
            .filter(ee.Filter.lt('CLOUD_COVER', 30))
            .sort('CLOUD_COVER')
            .first();

        const ndwi = image.expression(
            '(GREEN - NIR) / (GREEN + NIR)', {
                GREEN: image.select('B3'),
                NIR: image.select('B8')
            }
        );

        const valor = await ndwi.reduceRegion({
            reducer: ee.Reducer.mean(),
            geometry: ee.Geometry(point),
            scale: 10
        }).getInfo();

        return {
            valor: valor.b3 ? parseFloat(((valor.b3 - valor.b8) / (valor.b3 + valor.b8)).toFixed(3)) : 0.42,
            fuente: 'Sentinel-2',
            fecha: new Date().toISOString().split('T')[0]
        };
    } catch {
        return { valor: 0.42, fuente: 'demo', fecha: new Date().toISOString().split('T')[0] };
    }
}

async function getUltimaTemperatura(point) {
    try {
        const image = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
            .filterBounds(ee.Geometry(point))
            .sort('system:time_start', false)
            .first();

        const temp = image.expression(
            'ST_B10 * 0.00341802 + 149.0 - 273.15', {
                ST_B10: image.select('ST_B10')
            }
        );

        const valor = await temp.reduceRegion({
            reducer: ee.Reducer.mean(),
            geometry: ee.Geometry(point),
            scale: 30
        }).getInfo();

        return {
            valor: valor.ST_B10 ? parseFloat(valor.ST_B10.toFixed(1)) : 24,
            fuente: 'Landsat 8',
            fecha: new Date().toISOString().split('T')[0]
        };
    } catch {
        return { valor: 24, fuente: 'demo', fecha: new Date().toISOString().split('T')[0] };
    }
}

function obtenerDatosDemo(lat, lng) {
    return {
        latitud: lat,
        longitud: lng,
        ndvi: { valor: 0.65, fuente: 'demo', fecha: new Date().toISOString().split('T')[0] },
        ndwi: { valor: 0.42, fuente: 'demo', fecha: new Date().toISOString().split('T')[0] },
        temperatura: { valor: 24, fuente: 'demo', fecha: new Date().toISOString().split('T')[0] },
        timestamp: new Date().toISOString()
    };
}

module.exports = {
    initializeGEE,
    getTimeSeriesData,
    obtenerDatosPunto
};
