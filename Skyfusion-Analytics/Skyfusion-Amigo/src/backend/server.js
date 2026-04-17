require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const compression = require('compression');
const http = require('http');
const { Server } = require('socket.io');
const path = require('path');
const { logger } = require('./config/logger');
const routes = require('./routes');
const errorHandler = require('./middleware/errorHandler');
const { connectNeo4j, checkConnection, close: closeNeo4j } = require('./config/neo4j');
const NotificationService = require('./services/NotificationService');
const jwt = require('jsonwebtoken');

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
    cors: {
        origin: process.env.CLIENT_URL || 'http://localhost:3000',
        methods: ['GET', 'POST']
    }
});

const PORT = process.env.PORT || 3001;
const DEMO_MODE = process.env.DEMO_MODE !== 'false';

app.use(helmet({
    contentSecurityPolicy: false,
    crossOriginEmbedderPolicy: false
}));
app.use(cors({
    origin: process.env.CLIENT_URL || 'http://localhost:3000',
    credentials: true
}));
app.use(compression());
app.use(morgan('combined', { stream: { write: (msg) => logger.info(msg.trim()) } }));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

app.use(express.static(path.join(__dirname, '../../src/frontend/public')));

app.use('/api/v1', routes);

app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        mode: DEMO_MODE ? 'demo' : 'production',
        services: {
            neo4j: DEMO_MODE ? 'disabled' : 'connected'
        }
    });
});

app.get('/api/v1/demo/metrics/:catchmentId', (req, res) => {
    const { catchmentId } = req.params;
    res.json({
        catchment_id: catchmentId,
        timestamp: new Date().toISOString(),
        metrics: {
            caudal: { value: 4.2, unit: 'm³/s', status: 'normal', trend: 'down' },
            precipitacion: { value: 12, unit: 'mm', status: 'normal', trend: 'up' },
            temperatura: { value: 24, unit: '°C', status: 'normal', trend: 'up' },
            humedad: { value: 78, unit: '%', status: 'normal', trend: 'stable' },
            ndvi: { value: 0.65, status: 'healthy', trend: 'stable' },
            ndwi: { value: 0.42, status: 'stable', trend: 'down' }
        }
    });
});

app.get('/api/v1/demo/stations/:riverId', (req, res) => {
    const { riverId } = req.params;
    
    const stations = [
        {
            id: 'ST-001',
            name: 'Juntas - Parte Alta',
            lat: 4.548,
            lng: -75.321,
            status: 'active',
            lastReading: 1.2
        },
        {
            id: 'ST-002',
            name: 'Villarestrepo',
            lat: 4.512,
            lng: -75.285,
            status: 'active',
            lastReading: 0.9
        }
    ];

    logger.info(`Consultando estaciones para: ${riverId}`);
    res.json(stations);
});

app.get('/api/v1/demo/alerts/:catchmentId', (req, res) => {
    const alerts = [
        {
            id: 'alert-001',
            catchment_id: 'COMBEIMA',
            severity: 'yellow',
            status: 'active',
            type: 'drought',
            message: 'Sequía leve detectada - Monitoreo recomendado',
            probability: 0.65,
            created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            recommendations: [
                'Activar protocolo de monitoreo intensificado',
                'Notificar a usuarios del sector agropecuario',
                'Revisar estado de reservas hídricas'
            ]
        },
        {
            id: 'alert-002',
            catchment_id: 'COMBEIMA',
            severity: 'orange',
            status: 'active',
            type: 'water_stress',
            message: 'Estrés hídrico moderado - Reducción de caudal: 35%',
            probability: 0.72,
            created_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
            recommendations: [
                'Activación de plan de contingencia',
                'Monitoreo diario de niveles',
                'Coordinar con empresa de agua'
            ]
        }
    ];
    res.json({ alerts, total: alerts.length });
});

app.get('/api/v1/demo/predictions/:catchmentId', (req, res) => {
    const { catchmentId } = req.params;
    const { horizon = 7 } = req.query;
    
    const predictions = [];
    let caudal = 4.2;
    
    for (let i = 1; i <= parseInt(horizon); i++) {
        caudal = caudal - (Math.random() * 0.15);
        predictions.push({
            day: i,
            date: new Date(Date.now() + i * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            caudal: parseFloat(Math.max(caudal, 1.5).toFixed(2)),
            caudal_unit: 'm³/s',
            flood_probability: parseFloat((Math.random() * 0.25).toFixed(2)),
            drought_probability: parseFloat((0.3 + i * 0.04).toFixed(2)),
            alert_level: caudal < 2 ? 'orange' : caudal < 3 ? 'yellow' : 'green',
            confidence: parseFloat((0.75 + Math.random() * 0.2).toFixed(2))
        });
    }
    
    res.json({
        catchment_id: catchmentId,
        horizon_days: parseInt(horizon),
        generated_at: new Date().toISOString(),
        model_version: '1.0.0',
        predictions
    });
});

app.get('/api/v1/demo/narrative/:catchmentId', (req, res) => {
    const { catchmentId } = req.params;
    
    res.json({
        catchment_id: catchmentId,
        generated_at: new Date().toISOString(),
        summary: `El índice NDVI promedio en la cuenca ${catchmentId} es 0.65, indicando vegetación saludable. El NDWI de 0.42 sugiere niveles hídricos estables en cuerpos de agua. El caudal actual de 4.2 m³/s se encuentra 15% por encima del promedio histórico para este período.`,
        forecast: `Para los próximos 7 días, se anticipa una disminución gradual del caudal debido a la reducción de lluvias previstas. Se recomienda monitorear activo los niveles en la zona baja de la cuenca. La probabilidad de condiciones de estrés hídrico es del 65%.`,
        alert: {
            level: 'yellow',
            title: 'Sequía Leve',
            description: 'Probabilidad de condiciones de estrés hídrico: 65%. Acciones recomendadas: Activar protocolo de monitoreo intensificado, Notificar a usuarios del sector agropecuario, Revisar estado de reservas hídricas.'
        },
        recommendations: [
            'Activar protocolo de monitoreo intensificado',
            'Notificar a usuarios del sector agropecuario',
            'Revisar estado de reservas hídricas',
            'Coordinar con CRQ para planificación hídrica'
        ]
    });
});

app.get('/api/v1/demo/catchments', (req, res) => {
    res.json({
        catchments: [
            {
                id: 'COMBEIMA',
                name: 'Cuenca Río Combeima',
                area_km2: 342,
                population: 250000,
                location: { lat: 4.4389, lon: -75.2094 },
                centroid: { lat: 4.45, lon: -75.20 }
            },
            {
                id: 'COELLO',
                name: 'Cuenca Río Coello',
                area_km2: 1250,
                population: 450000,
                location: { lat: 4.25, lon: -75.15 },
                centroid: { lat: 4.30, lon: -75.18 }
            },
            {
                id: 'OPHIR',
                name: 'Cuenca Río Ophir',
                area_km2: 180,
                population: 85000,
                location: { lat: 4.55, lon: -75.30 },
                centroid: { lat: 4.52, lon: -75.28 }
            }
        ]
    });
});

app.get('/api/v1/demo/stations', (req, res) => {
    const { catchmentId } = req.query;
    const stations = [
        { id: 'COMB-001', name: 'Puente Combeima', type: 'caudal', lat: 4.4389, lon: -75.2094, status: 'active' },
        { id: 'COMB-002', name: 'El Carmen', type: 'pluviometro', lat: 4.4567, lon: -75.2234, status: 'active' },
        { id: 'COMB-003', name: 'Buenavista', type: 'caudal', lat: 4.4123, lon: -75.1956, status: 'active' },
        { id: 'COMB-004', name: 'Toche', type: 'meteo', lat: 4.4789, lon: -75.2456, status: 'active' }
    ];
    res.json({ stations });
});

app.get('/api/v1/demo/indices/:indexName', (req, res) => {
    const { indexName } = req.params;
    const { catchmentId = 'COMBEIMA', date } = req.query;
    
    const indices = {
        ndvi: {
            name: 'NDVI',
            description: 'Normalized Difference Vegetation Index',
            value: 0.65,
            min: -1,
            max: 1,
            interpretation: 'Vegetación saludable',
            last_update: new Date().toISOString(),
            coverage: 0.87
        },
        ndwi: {
            name: 'NDWI',
            description: 'Normalized Difference Water Index',
            value: 0.42,
            min: -1,
            max: 1,
            interpretation: 'Niveles hídricos estables',
            last_update: new Date().toISOString(),
            coverage: 0.65
        }
    };
    
    res.json({
        index: indexName,
        catchment_id: catchmentId,
        date: date || new Date().toISOString().split('T')[0],
        data: indices[indexName] || indices.ndvi
    });
});

app.use((req, res) => {
    res.status(404).json({ error: 'Endpoint no encontrado' });
});

app.use(errorHandler);

io.on('connection', (socket) => {
    logger.info(`Client connected: ${socket.id}`);
    
    socket.on('subscribe', (channel) => {
        socket.join(channel);
        logger.info(`Client ${socket.id} subscribed to ${channel}`);
    });
    
    socket.on('unsubscribe', (channel) => {
        socket.leave(channel);
        logger.info(`Client ${socket.id} unsubscribed from ${channel}`);
    });
    
    socket.on('authenticate', (token) => {
        try {
            const JWT_SECRET = process.env.JWT_SECRET || 'skyfusion-secret-key-2024';
            const decoded = jwt.verify(token, JWT_SECRET);
            socket.user = decoded;
            socket.join(`user:${decoded.id}`);
            
            if (decoded.catchments && Array.isArray(decoded.catchments)) {
                decoded.catchments.forEach(c => {
                    socket.join(`catchment:${c}`);
                });
            }
            
            logger.info(`Client ${socket.id} authenticated as ${decoded.username}`);
            socket.emit('authenticated', { userId: decoded.id });
        } catch (error) {
            logger.warn(`Socket authentication failed: ${error.message}`);
            socket.emit('auth_error', { error: 'Invalid token' });
        }
    });
    
    socket.on('disconnect', () => {
        logger.info(`Client disconnected: ${socket.id}`);
    });
});

NotificationService.setSocketIO(io);

function startDataSimulation() {
    logger.info('Starting data simulation for demo mode');
    
    setInterval(() => {
        const catchmentId = 'COMBEIMA';
        const channel = `catchment:${catchmentId}`;
        
        const newMetrics = {
            catchment_id: catchmentId,
            timestamp: new Date().toISOString(),
            metrics: {
                caudal: { value: parseFloat((3.5 + Math.random() * 1.5).toFixed(2)), unit: 'm³/s' },
                precipitacion: { value: parseFloat((Math.random() * 20).toFixed(1)), unit: 'mm' },
                temperatura: { value: parseFloat((20 + Math.random() * 10).toFixed(1)), unit: '°C' },
                humedad: { value: parseFloat((60 + Math.random() * 30).toFixed(1)), unit: '%' }
            }
        };
        
        io.to(channel).emit('metrics', newMetrics);
    }, 10000);
    
    setInterval(() => {
        if (Math.random() > 0.7) {
            const alertTypes = [
                { type: 'drought', severity: 'yellow', message: 'Sequía leve detectada' },
                { type: 'flood', severity: 'orange', message: 'Riesgo de inundación aumentado' },
                { type: 'normal', severity: 'green', message: 'Condiciones normales' }
            ];
            const alert = alertTypes[Math.floor(Math.random() * alertTypes.length)];
            
            io.to('catchment:COMBEIMA').emit('alert', {
                id: `alert-${Date.now()}`,
                catchment_id: 'COMBEIMA',
                severity: alert.severity,
                status: 'active',
                type: alert.type,
                message: alert.message,
                probability: parseFloat((0.5 + Math.random() * 0.4).toFixed(2)),
                created_at: new Date().toISOString()
            });
        }
    }, 30000);
}

async function startServer() {
    try {
        if (!DEMO_MODE) {
            await connectNeo4j();
            logger.info('Connected to Neo4j');
        } else {
            logger.info('Running in DEMO mode - Neo4j disabled');
        }
        
        server.listen(PORT, () => {
            logger.info(`Server running on port ${PORT}`);
            logger.info(`Health check: http://localhost:${PORT}/health`);
            logger.info(`API Base: http://localhost:${PORT}/api/v1`);
            
            if (DEMO_MODE) {
                startDataSimulation();
            }
        });
    } catch (error) {
        logger.error('Failed to start server:', error);
        process.exit(1);
    }
}

process.on('SIGTERM', async () => {
    logger.info('SIGTERM received, shutting down gracefully');
    server.close(() => {
        logger.info('HTTP server closed');
        closeNeo4j();
        process.exit(0);
    });
});

process.on('SIGINT', async () => {
    logger.info('SIGINT received, shutting down gracefully');
    server.close(() => {
        logger.info('HTTP server closed');
        closeNeo4j();
        process.exit(0);
    });
});

startServer();

module.exports = { app, server, io };
