/**
 * Rutas de la API
 */

const express = require('express');
const router = express.Router();
const User = require('../models/User');

const catchmentRoutes = require('./catchmentRoutes');
const sensorRoutes = require('./sensorRoutes');
const indexRoutes = require('./indexRoutes');
const predictionRoutes = require('./predictionRoutes');
const alertRoutes = require('./alertRoutes');
const narrativeRoutes = require('./narrativeRoutes');
const reportRoutes = require('./reportRoutes');
const geeRoutes = require('./geeRoutes');
const analisisRoutes = require('./analisisRoutes');
const proyectoRoutes = require('./proyectoRoutes');
const waterExtensionRoutes = require('./waterExtensionRoutes');
const authRoutes = require('./authRoutes');
const notificationRoutes = require('./notificationRoutes');
const demoRoutes = require('./demoRoutes');

router.use('/demo', demoRoutes);
router.use('/auth', authRoutes);
router.use('/notifications', notificationRoutes);
router.use('/catchments', catchmentRoutes);
router.use('/sensors', sensorRoutes);
router.use('/indices', indexRoutes);
router.use('/predictions', predictionRoutes);
router.use('/alerts', alertRoutes);
router.use('/narrative', narrativeRoutes);
router.use('/reports', reportRoutes);
router.use('/gee', geeRoutes);
router.use('/analisis', analisisRoutes);
router.use('/proyectos', proyectoRoutes);
router.use('/water-extension', waterExtensionRoutes);

router.get('/info', (req, res) => {
    res.json({
        name: 'Skyfusion Analytics API',
        version: '1.0.0',
        description: 'Plataforma SaaS de análisis multitemporal para monitoreo y predicción ambiental',
        authentication: {
            methods: [
                {
                    method: 'POST /api/auth/login',
                    description: 'Iniciar sesión con credenciales',
                    body: { email: 'string', password: 'string' }
                },
                {
                    method: 'POST /api/auth/guest',
                    description: 'Crear sesión de invitado (acceso limitado)',
                    body: {}
                },
                {
                    method: 'POST /api/auth/register',
                    description: 'Registrar nuevo usuario',
                    body: { username: 'string', email: 'string', password: 'string' }
                }
            ]
        },
        guest_session: {
            enabled: true,
            duration: '24 horas',
            access_level: 'lectura limitada',
            permissions: User.getPermissions('guest'),
            features: {
                allowed: [
                    'Ver dashboard',
                    'Ver mapa',
                    'Ver análisis',
                    'Ver predicciones',
                    'Acceso a datos de demostración'
                ],
                denied: [
                    'Crear alertas',
                    'Exportar datos',
                    'Gestionar sensores',
                    'Gestionar proyectos',
                    'Ver reportes avanzados'
                ]
            }
        },
        roles: {
            guest: User.getPermissions('guest'),
            user: User.getPermissions('user'),
            operator: User.getPermissions('operator'),
            admin: User.getPermissions('admin')
        },
        endpoints: {
            public: [
                'POST /api/auth/register',
                'POST /api/auth/login',
                'POST /api/auth/guest',
                'GET /api/demo/*',
                'GET /api/catchments',
                'GET /api/alerts',
                'GET /api/predictions/:catchment'
            ],
            authenticated: [
                'GET /api/notifications',
                'POST /api/notifications/test',
                'PUT /api/notifications/*',
                'GET /api/indices/*'
            ],
            restricted: {
                admin: [
                    'GET /api/auth/users',
                    'PUT /api/auth/profile'
                ],
                operator: [
                    'POST /api/catchments/*',
                    'PUT /api/sensors/*'
                ]
            }
        }
    });
});

module.exports = router;
