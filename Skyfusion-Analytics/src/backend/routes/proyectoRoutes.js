/**
 * Rutas de Proyectos
 * CRUD completo para gestión de proyectos
 */

const express = require('express');
const router = express.Router();
const proyectoService = require('../services/proyectoService');
const { logger } = require('../config/logger');

router.get('/', async (req, res, next) => {
    try {
        const { estado } = req.query;
        const proyectos = await proyectoService.getAllProyectos(estado ? { estado } : {});
        res.json({ success: true, proyectos, total: proyectos.length });
    } catch (error) {
        logger.error('Error listing proyectos:', error);
        next(error);
    }
});

router.get('/resumen', async (req, res, next) => {
    try {
        const resumen = await proyectoService.getProyectosPorEstado();
        res.json({ success: true, ...resumen });
    } catch (error) {
        logger.error('Error getting resumen:', error);
        next(error);
    }
});

router.get('/:id', async (req, res, next) => {
    try {
        const { id } = req.params;
        const proyecto = await proyectoService.getProyectoById(id);
        
        if (!proyecto) {
            return res.status(404).json({ success: false, error: 'Proyecto no encontrado' });
        }
        
        res.json({ success: true, proyecto });
    } catch (error) {
        logger.error('Error getting proyecto:', error);
        next(error);
    }
});

router.post('/', async (req, res, next) => {
    try {
        const proyecto = await proyectoService.createProyecto(req.body);
        res.status(201).json({ success: true, proyecto });
    } catch (error) {
        logger.error('Error creating proyecto:', error);
        next(error);
    }
});

router.put('/:id', async (req, res, next) => {
    try {
        const { id } = req.params;
        const proyecto = await proyectoService.updateProyecto(id, req.body);
        res.json({ success: true, proyecto });
    } catch (error) {
        logger.error('Error updating proyecto:', error);
        next(error);
    }
});

router.patch('/:id/progreso', async (req, res, next) => {
    try {
        const { id } = req.params;
        const { progreso } = req.body;
        
        const proyecto = await proyectoService.updateProyecto(id, { progreso });
        res.json({ success: true, proyecto });
    } catch (error) {
        logger.error('Error updating progreso:', error);
        next(error);
    }
});

router.patch('/:id/estado', async (req, res, next) => {
    try {
        const { id } = req.params;
        const { estado } = req.body;
        
        const proyecto = await proyectoService.updateProyecto(id, { estado });
        res.json({ success: true, proyecto });
    } catch (error) {
        logger.error('Error updating estado:', error);
        next(error);
    }
});

router.delete('/:id', async (req, res, next) => {
    try {
        const { id } = req.params;
        await proyectoService.deleteProyecto(id);
        res.json({ success: true, message: 'Proyecto eliminado' });
    } catch (error) {
        logger.error('Error deleting proyecto:', error);
        next(error);
    }
});

module.exports = router;
