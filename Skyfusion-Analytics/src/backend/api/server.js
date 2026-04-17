/**
 * Skyfusion Analytics - Backend Server
 * API REST para monitoreo y predicción ambiental
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const compression = require('compression');
const http = require('http');
const { Server } = require('socket.io');
const cron = require('node-cron');

require('dotenv').config();

const routes = require('../routes');
const { errorHandler } = require('../middleware/errorHandler');
const { logger } = require('../config/logger');
const { connectNeo4j } = require('../config/neo4j');
const { startPredictionJob } = require('../services/predictionService');
const { checkAlerts } = require('../services/alertService');

const app = express();
const server = http.createServer(app);

const allowedOrigins = [
    'http://localhost:3000',
    'http://localhost:3001',
    'http://localhost:3002',
    'http://localhost:3003',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:3001',
    'http://127.0.0.1:3002',
    'http://127.0.0.1:3003'
];

const io = new Server(server, {
    cors: {
        origin: allowedOrigins,
        methods: ['GET', 'POST']
    }
});

app.use(helmet());
app.use(cors({
    origin: function(origin, callback) {
        if (!origin) return callback(null, true);
        if (allowedOrigins.indexOf(origin) !== -1) {
            return callback(null, true);
        }
        callback(null, true);
    },
    credentials: true
}));
app.use(compression());
app.use(morgan('combined', { stream: { write: message => logger.info(message) } }));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

app.use('/api/v1', routes);
app.use('/api', routes);

app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: process.env.APP_VERSION || '1.0.0'
    });
});

app.get('/api/v1/status', async (req, res) => {
    try {
        const neo4jStatus = await require('../config/neo4j').checkConnection();
        
        res.json({
            api: 'online',
            database: neo4jStatus ? 'connected' : 'disconnected',
            websocket: io.sockets.sockets.size > 0 ? 'active' : 'idle',
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        res.status(503).json({
            api: 'online',
            database: 'error',
            error: error.message
        });
    }
});

app.use(errorHandler);

io.on('connection', (socket) => {
    logger.info(`Client connected: ${socket.id}`);

    socket.on('subscribe', (catchmentId) => {
        socket.join(`catchment:${catchmentId}`);
        logger.info(`Client ${socket.id} subscribed to catchment: ${catchmentId}`);
    });

    socket.on('disconnect', () => {
        logger.info(`Client disconnected: ${socket.id}`);
    });
});

app.set('io', io);

const PORT = process.env.PORT || 3001;

async function startServer() {
    try {
        await connectNeo4j();
        logger.info('Connected to Neo4j');

        cron.schedule('*/15 * * * *', async () => {
            logger.info('Running scheduled prediction job');
            await startPredictionJob(io);
        });

        cron.schedule('*/5 * * * *', async () => {
            logger.info('Checking alerts');
            await checkAlerts(io);
        });

        server.listen(PORT, () => {
            logger.info(`Server running on port ${PORT}`);
            console.log(`🚀 Skyfusion Analytics API running on http://localhost:${PORT}`);
        });
    } catch (error) {
        logger.error('Failed to start server:', error);
        process.exit(1);
    }
}

process.on('SIGTERM', async () => {
    logger.info('SIGTERM received, closing server...');
    server.close(() => {
        logger.info('Server closed');
        process.exit(0);
    });
});

process.on('unhandledRejection', (reason, promise) => {
    logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

startServer();

module.exports = { app, io };
