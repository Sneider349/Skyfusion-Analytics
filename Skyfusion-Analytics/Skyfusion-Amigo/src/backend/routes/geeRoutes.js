/**
 * Rutas de Google Earth Engine
 */

const express = require('express');
const router = express.Router();
const geeService = require('../services/geeService');

router.get('/initialize', async (req, res, next) => {
    try {
        const result = await geeService.initializeGEE();
        res.json({ initialized: result });
    } catch (error) {
        next(error);
    }
});

router.get('/ndvi', async (req, res, next) => {
    try {
        const { date } = req.query;
        const result = await geeService.getNDVI(date);
        res.json(result);
    } catch (error) {
        next(error);
    }
});

router.get('/ndwi', async (req, res, next) => {
    try {
        const { date } = req.query;
        const result = await geeService.getNDWI(date);
        res.json(result);
    } catch (error) {
        next(error);
    }
});

router.get('/temperature', async (req, res, next) => {
    try {
        const { date } = req.query;
        const result = await geeService.getTemperature(date);
        res.json(result);
    } catch (error) {
        next(error);
    }
});

router.get('/indices', async (req, res, next) => {
    try {
        const { date } = req.query;
        const result = await geeService.getAllIndices(date);
        res.json(result);
    } catch (error) {
        next(error);
    }
});

router.get('/image', async (req, res, next) => {
    try {
        const { date } = req.query;
        const result = await geeService.getSatelliteImage(date);
        res.json(result);
    } catch (error) {
        next(error);
    }
});

module.exports = router;
