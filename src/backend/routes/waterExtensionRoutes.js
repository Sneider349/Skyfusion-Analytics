/**
 * Rutas de Predicción de Extensión de Agua
 * Skyfusion Analytics - API Endpoints
 */

const express = require('express');
const router = express.Router();
const waterPredictionService = require('../services/waterPredictionService');

router.get('/water-extension/:catchmentId', async (req, res) => {
    try {
        const { catchmentId } = req.params;
        const { horizon = 7 } = req.query;
        
        const prediction = await waterPredictionService.predictWaterExtension(
            catchmentId,
            { horizon: parseInt(horizon) }
        );
        
        res.json({
            success: true,
            data: prediction
        });
    } catch (error) {
        console.error('Error en predicción:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

router.get('/water-extension/:catchmentId/all-horizons', async (req, res) => {
    try {
        const { catchmentId } = req.params;
        
        const predictions = await waterPredictionService.predictAllHorizons(catchmentId);
        
        res.json({
            success: true,
            data: predictions
        });
    } catch (error) {
        console.error('Error en predicción multi-horizonte:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

router.get('/water-extension/model-status', (req, res) => {
    const status = waterPredictionService.getModelStatus();
    
    res.json({
        success: true,
        data: status
    });
});

router.post('/water-extension/predict', async (req, res) => {
    try {
        const { 
            catchment_id,
            satellite_sequence,
            climate_sequence,
            static_features,
            horizon = 7
        } = req.body;
        
        if (!satellite_sequence || !climate_sequence) {
            return res.status(400).json({
                success: false,
                error: 'Se requieren satellite_sequence y climate_sequence'
            });
        }
        
        const prediction = await waterPredictionService.runInference(
            satellite_sequence,
            climate_sequence,
            static_features || [1500, 15, 0.3, 32, 32],
            horizon
        );
        
        res.json({
            success: true,
            data: {
                catchment_id,
                horizon,
                prediction
            }
        });
    } catch (error) {
        console.error('Error en predicción custom:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

module.exports = router;
