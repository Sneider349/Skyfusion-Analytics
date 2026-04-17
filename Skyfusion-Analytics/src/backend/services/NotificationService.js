const fs = require('fs');
const path = require('path');
const { logger } = require('../config/logger');

const NOTIFICATIONS_FILE = path.join(__dirname, '../../data/notifications.json');

let io = null;

function setSocketIO(socketIO) {
    io = socketIO;
}

function ensureNotificationsFile() {
    const dataDir = path.join(__dirname, '../../data');
    if (!fs.existsSync(dataDir)) {
        fs.mkdirSync(dataDir, { recursive: true });
    }
    if (!fs.existsSync(NOTIFICATIONS_FILE)) {
        fs.writeFileSync(NOTIFICATIONS_FILE, JSON.stringify([], null, 2));
    }
}

function getNotifications() {
    ensureNotificationsFile();
    try {
        const data = fs.readFileSync(NOTIFICATIONS_FILE, 'utf-8');
        return JSON.parse(data);
    } catch (error) {
        logger.error('Error reading notifications:', error);
        return [];
    }
}

function saveNotifications(notifications) {
    try {
        fs.writeFileSync(NOTIFICATIONS_FILE, JSON.stringify(notifications, null, 2));
        return true;
    } catch (error) {
        logger.error('Error saving notifications:', error);
        return false;
    }
}

function generateNotificationId() {
    return `notif-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

function createNotification(data) {
    const notifications = getNotifications();
    
    const notification = {
        id: generateNotificationId(),
        userId: data.userId || null,
        catchmentId: data.catchmentId || null,
        type: data.type || 'info',
        title: data.title,
        message: data.message,
        severity: data.severity || 'info',
        read: false,
        createdAt: new Date().toISOString(),
        expiresAt: data.expiresAt || null,
        metadata: data.metadata || {}
    };
    
    notifications.unshift(notification);
    
    const maxNotifications = 1000;
    if (notifications.length > maxNotifications) {
        notifications.splice(maxNotifications);
    }
    
    saveNotifications(notifications);
    
    logger.info(`Notification created: ${notification.id} - ${notification.title}`);
    
    return notification;
}

function sendToUser(userId, notification) {
    if (io) {
        io.to(`user:${userId}`).emit('notification', notification);
    }
}

function sendToCatchment(catchmentId, notification) {
    if (io) {
        io.to(`catchment:${catchmentId}`).emit('notification', notification);
    }
}

function broadcast(notification) {
    if (io) {
        io.emit('notification', notification);
    }
}

function getUserNotifications(userId, options = {}) {
    const notifications = getNotifications();
    const { unreadOnly = false, limit = 50, type = null } = options;
    
    let filtered = notifications.filter(n => 
        n.userId === userId || n.userId === null
    );
    
    if (unreadOnly) {
        filtered = filtered.filter(n => !n.read);
    }
    
    if (type) {
        filtered = filtered.filter(n => n.type === type);
    }
    
    return filtered.slice(0, limit);
}

function markAsRead(notificationId, userId) {
    const notifications = getNotifications();
    const index = notifications.findIndex(n => n.id === notificationId);
    
    if (index !== -1) {
        notifications[index].read = true;
        notifications[index].readAt = new Date().toISOString();
        saveNotifications(notifications);
        return true;
    }
    
    return false;
}

function markAllAsRead(userId) {
    const notifications = getNotifications();
    let changed = false;
    
    notifications.forEach(n => {
        if ((n.userId === userId || n.userId === null) && !n.read) {
            n.read = true;
            n.readAt = new Date().toISOString();
            changed = true;
        }
    });
    
    if (changed) {
        saveNotifications(notifications);
    }
    
    return changed;
}

function deleteNotification(notificationId, userId) {
    const notifications = getNotifications();
    const index = notifications.findIndex(n => 
        n.id === notificationId && (n.userId === userId || n.userId === null)
    );
    
    if (index !== -1) {
        notifications.splice(index, 1);
        saveNotifications(notifications);
        return true;
    }
    
    return false;
}

function getUnreadCount(userId) {
    const notifications = getNotifications();
    return notifications.filter(n => 
        (n.userId === userId || n.userId === null) && !n.read
    ).length;
}

function createAlertNotification(catchmentId, alert) {
    let severity = 'info';
    let type = 'alert';
    
    switch (alert.severity) {
        case 'red':
            severity = 'critical';
            type = 'flood_alert';
            break;
        case 'orange':
            severity = 'warning';
            type = 'flood_alert';
            break;
        case 'yellow':
            severity = 'caution';
            type = 'drought_alert';
            break;
        default:
            severity = 'info';
            type = 'normal';
    }
    
    const notification = createNotification({
        userId: null,
        catchmentId: catchmentId,
        type: type,
        title: `Alerta: ${alert.type || 'Notificación'}`,
        message: alert.message,
        severity: severity,
        metadata: { alert }
    });
    
    sendToCatchment(catchmentId, notification);
    broadcast(notification);
    
    return notification;
}

function createSystemNotification(title, message, severity = 'info') {
    const notification = createNotification({
        userId: null,
        catchmentId: null,
        type: 'system',
        title: title,
        message: message,
        severity: severity
    });
    
    broadcast(notification);
    
    return notification;
}

function createUserNotification(userId, title, message, type = 'info') {
    const notification = createNotification({
        userId: userId,
        catchmentId: null,
        type: type,
        title: title,
        message: message,
        severity: type === 'error' ? 'error' : 'info'
    });
    
    sendToUser(userId, notification);
    
    return notification;
}

function cleanupExpiredNotifications() {
    const notifications = getNotifications();
    const now = new Date().toISOString();
    
    const valid = notifications.filter(n => 
        !n.expiresAt || n.expiresAt > now
    );
    
    if (valid.length !== notifications.length) {
        saveNotifications(valid);
        logger.info(`Cleaned up ${notifications.length - valid.length} expired notifications`);
    }
    
    return valid;
}

setInterval(cleanupExpiredNotifications, 60 * 60 * 1000);

function getNotificationStats(userId) {
    const notifications = getNotifications();
    const userNotifications = notifications.filter(n => 
        n.userId === userId || n.userId === null
    );
    
    return {
        total: userNotifications.length,
        unread: userNotifications.filter(n => !n.read).length,
        byType: userNotifications.reduce((acc, n) => {
            acc[n.type] = (acc[n.type] || 0) + 1;
            return acc;
        }, {}),
        bySeverity: userNotifications.reduce((acc, n) => {
            acc[n.severity] = (acc[n.severity] || 0) + 1;
            return acc;
        }, {})
    };
}

module.exports = {
    setSocketIO,
    createNotification,
    sendToUser,
    sendToCatchment,
    broadcast,
    getUserNotifications,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    getUnreadCount,
    createAlertNotification,
    createSystemNotification,
    createUserNotification,
    getNotificationStats
};