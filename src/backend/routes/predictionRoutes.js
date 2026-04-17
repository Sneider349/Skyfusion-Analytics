/**
 * Rutas de Predicciones
 */

const express = require('express');
const router = express.Router();
const waterPredictionService = require('../services/waterPredictionService');
const predictionService = require('../services/predictionService');
const { authenticateToken, blockGuests, requirePermission, optionalAuth } = require('../middleware/authMiddleware');

router.get('/:catchment', optionalAuth, async (req, res, next) => {
    try {
        const { catchment } = req.params;
        const { horizon = 7 } = req.query;

        let waterExtension;
        try {
            waterExtension = await waterPredictionService.predictWaterExtension(catchment, {
                horizon: parseInt(horizon)
            });
        } catch (e) {
            waterExtension = null;
        }

        const predictions = {
            catchment_id: catchment,
            horizon_days: parseInt(horizon),
            generated_at: new Date().toISOString(),
            predictions: [],
            water_extension: waterExtension,
            is_guest_access: req.user?.role === 'guest'
        };

        for (let i = 1; i <= parseInt(horizon); i++) {
            predictions.predictions.push({
                day: i,
                caudal: parseFloat((4.2 - i * 0.1).toFixed(2)),
                flood_probability: parseFloat((Math.random() * 0.3).toFixed(2)),
                drought_probability: parseFloat((0.3 + i * 0.05).toFixed(2)),
                alert_level: i > 5 ? 1 : 0
            });
        }

        res.json(predictions);
    } catch (error) {
        next(error);
    }
});

router.get('/:catchment/water-extension', authenticateToken, async (req, res, next) => {
    try {
        const { catchment } = req.params;
        const { horizon = 7 } = req.query;

        const prediction = await waterPredictionService.predictWaterExtension(catchment, {
            horizon: parseInt(horizon)
        });

        res.json({
            success: true,
            data: prediction,
            is_guest_access: req.user?.role === 'guest'
        });
    } catch (error) {
        next(error);
    }
});

router.get('/:catchment/water-extension/all-horizons', authenticateToken, async (req, res, next) => {
    try {
        const { catchment } = req.params;

        const predictions = await waterPredictionService.predictAllHorizons(catchment);

        res.json({
            success: true,
            data: predictions,
            is_guest_access: req.user?.role === 'guest'
        });
    } catch (error) {
        next(error);
    }
});

router.post('/trigger', authenticateToken, blockGuests, requirePermission('canViewPredictions'), async (req, res, next) => {
    try {
        const { catchment_id } = req.body;

        res.json({
            status: 'triggered',
            catchment_id,
            message: 'Predicción iniciada',
            estimated_completion: new Date(Date.now() + 60000).toISOString()
        });
    } catch (error) {
        next(error);
    }
});

router.get('/:catchment/history', optionalAuth, async (req, res, next) => {
    try {
        const { catchment } = req.params;
        const { 
            startDate, 
            endDate, 
            modelType, 
            horizon, 
            limit = 100 
        } = req.query;

        const catchmentMetadata = await predictionService.getCatchmentMetadata(catchment);
        
        if (!catchmentMetadata) {
            return res.status(404).json({
                success: false,
                error: 'Cuenca no encontrada',
                errorCode: 'CATCHMENT_NOT_FOUND'
            });
        }

        const predictions = await predictionService.getPredictions(catchment, {
            startDate: startDate || null,
            endDate: endDate || null,
            modelType: modelType || null,
            horizon: horizon ? parseInt(horizon) : null,
            limit: parseInt(limit)
        });

        res.json({
            success: true,
            predictions: predictions,
            metadata: {
                catchmentId: catchment,
                catchmentName: catchmentMetadata.name,
                catchmentLocation: catchmentMetadata.location,
                modelUsed: predictions.length > 0 ? predictions[0].model_type : 'default',
                generatedAt: new Date().toISOString(),
                dataPoints: predictions.length,
                filters: {
                    startDate: startDate || null,
                    endDate: endDate || null,
                    modelType: modelType || null,
                    horizon: horizon ? parseInt(horizon) : null
                }
            },
            is_guest_access: req.user?.role === 'guest'
        });
    } catch (error) {
        if (error.message.includes('Connection')) {
            return res.status(503).json({
                success: false,
                error: 'Servicio de base de datos no disponible',
                errorCode: 'DB_UNAVAILABLE'
            });
        }
        next(error);
    }
});

module.exports = router;
