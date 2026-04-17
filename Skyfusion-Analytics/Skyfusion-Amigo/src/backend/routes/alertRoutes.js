/**
 * Rutas de Alertas
 */

const express = require('express');
const router = express.Router();
const { authenticateToken, blockGuests, requirePermission, optionalAuth } = require('../middleware/authMiddleware');

router.get('/', optionalAuth, async (req, res, next) => {
    try {
        const { catchment, severity, status = 'active' } = req.query;

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
                severity: 'green',
                status: 'active',
                type: 'normal',
                message: 'Condiciones normales - Sin alertas',
                probability: 0.95,
                created_at: new Date().toISOString(),
                recommendations: []
            }
        ];

        let filtered = alerts;
        if (severity) filtered = filtered.filter(a => a.severity === severity);
        if (catchment) filtered = filtered.filter(a => a.catchment_id === catchment);

        res.json({ 
            alerts: filtered, 
            total: filtered.length,
            is_guest_access: req.user?.role === 'guest',
            guest_notice: req.user?.role === 'guest' 
                ? 'Los invitados no reciben alertas personalizadas.' 
                : null
        });
    } catch (error) {
        next(error);
    }
});

router.get('/:id', optionalAuth, async (req, res, next) => {
    try {
        const { id } = req.params;

        res.json({
            id,
            catchment_id: 'COMBEIMA',
            severity: 'yellow',
            status: 'active',
            type: 'drought',
            message: 'Sequía leve detectada',
            probability: 0.65,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            recommendations: []
        });
    } catch (error) {
        next(error);
    }
});

router.post('/:id/acknowledge', authenticateToken, blockGuests, requirePermission('canCreateAlerts'), async (req, res, next) => {
    try {
        const { id } = req.params;
        const { user_id } = req.body;

        res.json({
            id,
            status: 'acknowledged',
            acknowledged_by: user_id,
            acknowledged_at: new Date().toISOString()
        });
    } catch (error) {
        next(error);
    }
});

module.exports = router;
