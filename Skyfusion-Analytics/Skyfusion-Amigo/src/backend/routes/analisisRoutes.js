/**
 * Rutas de Análisis Dinámico
 * Integración GEE + IA para análisis en tiempo real
 */

const express = require('express');
const router = express.Router();
const aiService = require('../services/aiService');
const timeSeriesService = require('../services/timeSeriesService');
const { logger } = require('../config/logger');

router.post('/coordenadas', async (req, res, next) => {
    try {
        const { lat, lng, meses = 12 } = req.body;

        if (!lat || !lng) {
            return res.status(400).json({ 
                error: 'Coordenadas requeridas',
                message: 'lat y lng son obligatorios'
            });
        }

        logger.info(`Análisis solicitado para: ${lat}, ${lng}`);

        const datosGEE = await timeSeriesService.obtenerDatosPunto(lat, lng);
        
        const serieTemporal = await timeSeriesService.getTimeSeriesData(lat, lng, meses);
        
        const analisisIA = await aiService.analizarDatosAmbientales(datosGEE);

        res.json({
            success: true,
            coordenadas: { lat, lng },
            datos_satelitales: datosGEE,
            serie_temporal: serieTemporal,
            analisis_ia: analisisIA,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        logger.error('Error en análisis de coordenadas:', error);
        next(error);
    }
});

router.get('/serie-temporal', async (req, res, next) => {
    try {
        const { lat, lng, meses = 12 } = req.query;

        if (!lat || !lng) {
            return res.status(400).json({ 
                error: 'Coordenadas requeridas',
                message: 'lat y lng son obligatorios'
            });
        }

        const serieTemporal = await timeSeriesService.getTimeSeriesData(
            parseFloat(lat), 
            parseFloat(lng), 
            parseInt(meses)
        );

        res.json({
            success: true,
            serie_temporal: serieTemporal
        });
    } catch (error) {
        logger.error('Error obteniendo serie temporal:', error);
        next(error);
    }
});

router.post('/analisis-rapido', async (req, res, next) => {
    try {
        const { lat, lng } = req.body;

        const datosGEE = await timeSeriesService.obtenerDatosPunto(lat, lng);
        const analisisIA = await aiService.analizarDatosAmbientales(datosGEE);

        res.json({
            success: true,
            datos: datosGEE,
            analisis: analisisIA
        });
    } catch (error) {
        logger.error('Error en análisis rápido:', error);
        next(error);
    }
});

router.post('/proyecciones', async (req, res, next) => {
    try {
        const { datosHistoricos } = req.body;

        const proyecciones = await aiService.predecirProyecciones(datosHistoricos || {
            tendencia: 'decreciente',
            promedio: 3.5,
            meses: 6
        });

        res.json({
            success: true,
            proyecciones
        });
    } catch (error) {
        logger.error('Error generando proyecciones:', error);
        next(error);
    }
});

router.post('/narrativa-proyecto', async (req, res, next) => {
    try {
        const { proyecto, metricas } = req.body;

        const narrativa = await aiService.generarNarrativaProyecto(
            proyecto || { nombre: 'Proyecto demo', progreso: 50, estado: 'en_proceso' },
            metricas || { ndvi: 0.65, alertas: 2 }
        );

        res.json({
            success: true,
            narrativa
        });
    } catch (error) {
        logger.error('Error generando narrativa:', error);
        next(error);
    }
});

router.get('/test-ai', async (req, res, next) => {
    try {
        const resultado = await aiService.analizarDatosAmbientales({
            latitud: 4.548,
            longitud: -75.321,
            ndvi: { valor: 0.65 },
            ndwi: { valor: 0.42 },
            temperatura: { valor: 24 }
        });

        res.json({
            success: true,
            test: 'AI Service working',
            resultado
        });
    } catch (error) {
        logger.error('Error testing AI:', error);
        next(error);
    }
});

module.exports = router;
