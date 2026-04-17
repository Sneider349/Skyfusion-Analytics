/**
 * Middleware de Manejo de Errores
 */

const { logger } = require('../config/logger');

function errorHandler(err, req, res, next) {
    logger.error('Error:', {
        message: err.message,
        stack: err.stack,
        path: req.path,
        method: req.method
    });

    if (err.name === 'ValidationError') {
        return res.status(400).json({
            error: 'Validation Error',
            message: err.message,
            details: err.details
        });
    }

    if (err.name === 'UnauthorizedError') {
        return res.status(401).json({
            error: 'Unauthorized',
            message: 'Invalid or missing authentication token'
        });
    }

    if (err.code === 'Neo4jError') {
        return res.status(503).json({
            error: 'Database Error',
            message: 'Unable to connect to database'
        });
    }

    res.status(err.status || 500).json({
        error: err.name || 'Internal Server Error',
        message: process.env.NODE_ENV === 'production' 
            ? 'An unexpected error occurred' 
            : err.message
    });
}

module.exports = { errorHandler };
