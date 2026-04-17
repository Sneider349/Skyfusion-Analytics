const express = require('express');
const router = express.Router();
const NotificationService = require('../services/NotificationService');
const { logger } = require('../config/logger');
const { authenticateToken, blockGuests, requirePermission } = require('../middleware/authMiddleware');

router.use(authenticateToken);

router.get('/', (req, res) => {
    try {
        const { unreadOnly, limit = 50, type } = req.query;
        
        const notifications = NotificationService.getUserNotifications(req.user.id, {
            unreadOnly: unreadOnly === 'true',
            limit: parseInt(limit),
            type: type || null
        });
        
        const unreadCount = NotificationService.getUnreadCount(req.user.id);
        
        res.json({
            notifications,
            unreadCount,
            total: notifications.length
        });
    } catch (error) {
        logger.error('Error getting notifications:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

router.get('/stats', (req, res) => {
    try {
        const stats = NotificationService.getNotificationStats(req.user.id);
        res.json(stats);
    } catch (error) {
        logger.error('Error getting notification stats:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

router.put('/:id/read', (req, res) => {
    try {
        const { id } = req.params;
        const success = NotificationService.markAsRead(id, req.user.id);
        
        if (success) {
            res.json({ message: 'Notificación marcada como leída' });
        } else {
            res.status(404).json({ error: 'Notificación no encontrada' });
        }
    } catch (error) {
        logger.error('Error marking notification as read:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

router.put('/read-all', (req, res) => {
    try {
        NotificationService.markAllAsRead(req.user.id);
        res.json({ message: 'Todas las notificaciones marcadas como leídas' });
    } catch (error) {
        logger.error('Error marking all as read:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

router.delete('/:id', (req, res) => {
    try {
        const { id } = req.params;
        const success = NotificationService.deleteNotification(id, req.user.id);
        
        if (success) {
            res.json({ message: 'Notificación eliminada' });
        } else {
            res.status(404).json({ error: 'Notificación no encontrada' });
        }
    } catch (error) {
        logger.error('Error deleting notification:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

router.post('/test', blockGuests, requirePermission('canCreateAlerts'), (req, res) => {
    try {
        const { title, message, type, severity } = req.body;
        
        const notification = NotificationService.createNotification({
            userId: req.user.id,
            catchmentId: req.user.catchments?.[0] || null,
            type: type || 'test',
            title: title || 'Notificación de prueba',
            message: message || 'Esta es una notificación de prueba',
            severity: severity || 'info'
        });
        
        NotificationService.sendToUser(req.user.id, notification);
        
        res.json({
            message: 'Notificación de prueba creada',
            notification
        });
    } catch (error) {
        logger.error('Error creating test notification:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

module.exports = router;