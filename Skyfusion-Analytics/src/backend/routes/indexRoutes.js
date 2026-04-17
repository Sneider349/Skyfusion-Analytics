/**
 * Rutas de Índices Ambientales
 */

const express = require('express');
const router = express.Router();

router.get('/ndvi', async (req, res, next) => {
    try {
        const { catchment, date, start, end } = req.query;

        res.json({
            index: 'ndvi',
            catchment,
            date: date || new Date().toISOString(),
            value: 0.65,
            trend: 'stable',
            statistics: {
                mean: 0.65,
                min: 0.3,
                max: 0.85,
                std: 0.15
            },
            image_url: '/api/v1/indices/ndvi/image'
        });
    } catch (error) {
        next(error);
    }
});

router.get('/ndwi', async (req, res, next) => {
    try {
        const { catchment, date, start, end } = req.query;

        res.json({
            index: 'ndwi',
            catchment,
            date: date || new Date().toISOString(),
            value: 0.42,
            trend: 'decreasing',
            statistics: {
                mean: 0.42,
                min: 0.1,
                max: 0.7,
                std: 0.18
            },
            image_url: '/api/v1/indices/ndwi/image'
        });
    } catch (error) {
        next(error);
    }
});

router.get('/ndvi/image', async (req, res, next) => {
    try {
        res.json({ message: 'NDVI image placeholder' });
    } catch (error) {
        next(error);
    }
});

router.get('/ndwi/image', async (req, res, next) => {
    try {
        res.json({ message: 'NDWI image placeholder' });
    } catch (error) {
        next(error);
    }
});

module.exports = router;
