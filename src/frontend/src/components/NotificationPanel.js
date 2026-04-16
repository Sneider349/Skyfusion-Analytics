import React, { useState } from 'react';
import { useNotifications } from '../hooks/useNotifications';
import { Bell, X, Check, Trash2, Clock, AlertTriangle, Info, CheckCircle, AlertOctagon } from 'lucide-react';

function NotificationPanel({ isOpen, onClose, externalNotifications = [] }) {
    const {
        notifications,
        unreadCount,
        loading,
        fetchNotifications,
        markAsRead,
        markAllAsRead,
        deleteNotification
    } = useNotifications();

    const [filter, setFilter] = useState('all');

    const displayNotifications = externalNotifications.length > 0 ? externalNotifications : notifications;

    React.useEffect(() => {
        if (isOpen && externalNotifications.length === 0) {
            fetchNotifications({ limit: 100 });
        }
    }, [isOpen, fetchNotifications, externalNotifications.length]);

    const getSeverityStyles = (severity) => {
        switch (severity) {
            case 'critical':
            case 'red':
                return 'bg-red-50 border-red-300 text-red-800';
            case 'warning':
            case 'orange':
                return 'bg-orange-50 border-orange-300 text-orange-800';
            case 'caution':
            case 'yellow':
                return 'bg-yellow-50 border-yellow-300 text-yellow-800';
            case 'error':
                return 'bg-red-100 border-red-400 text-red-900';
            default:
                return 'bg-blue-50 border-blue-200 text-blue-800';
        }
    };

    const getSeverityIcon = (severity) => {
        switch (severity) {
            case 'critical':
            case 'red':
                return <AlertOctagon className="w-5 h-5 text-red-600" />;
            case 'warning':
            case 'orange':
                return <AlertTriangle className="w-5 h-5 text-orange-500" />;
            case 'caution':
            case 'yellow':
                return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
            case 'error':
                return <AlertTriangle className="w-5 h-5 text-red-500" />;
            case 'success':
            case 'green':
                return <CheckCircle className="w-5 h-5 text-green-500" />;
            default:
                return <Info className="w-5 h-5 text-blue-500" />;
        }
    };

    const getTypeIcon = (type) => {
        if (type?.includes('flood')) {
            return <AlertOctagon className="w-4 h-4" />;
        }
        if (type?.includes('drought')) {
            return <AlertTriangle className="w-4 h-4" />;
        }
        if (type?.includes('system')) {
            return <Info className="w-4 h-4" />;
        }
        return <Bell className="w-4 h-4" />;
    };

    const formatTime = (dateString) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Ahora';
        if (diffMins < 60) return `Hace ${diffMins}m`;
        if (diffHours < 24) return `Hace ${diffHours}h`;
        if (diffDays < 7) return `Hace ${diffDays}d`;
        return date.toLocaleDateString('es-CO');
    };

    const filteredNotifications = displayNotifications.filter(n => {
        if (filter === 'unread') return !n.read;
        if (filter === 'alerts') return n.type?.includes('alert');
        return true;
    });

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[9999] flex justify-end">
            <div 
                className="absolute inset-0 bg-black/30 backdrop-blur-sm"
                onClick={onClose}
            />
            
            <div className="relative w-full max-w-md bg-white shadow-2xl h-full flex flex-col">
                <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-sky-600 to-sky-700">
                    <div className="flex items-center space-x-2">
                        <Bell className="w-5 h-5 text-white" />
                        <h2 className="text-lg font-semibold text-white">Notificaciones</h2>
                        {unreadCount > 0 && (
                            <span className="px-2 py-0.5 text-xs font-bold bg-red-500 text-white rounded-full">
                                {unreadCount}
                            </span>
                        )}
                    </div>
                    <button 
                        onClick={onClose}
                        className="p-1 text-white/80 hover:text-white hover:bg-white/20 rounded"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                <div className="flex items-center space-x-2 p-3 border-b border-gray-100 bg-gray-50">
                    <button
                        onClick={() => setFilter('all')}
                        className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                            filter === 'all' 
                                ? 'bg-sky-600 text-white' 
                                : 'bg-white text-gray-600 hover:bg-gray-100'
                        }`}
                    >
                        Todas
                    </button>
                    <button
                        onClick={() => setFilter('unread')}
                        className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                            filter === 'unread' 
                                ? 'bg-sky-600 text-white' 
                                : 'bg-white text-gray-600 hover:bg-gray-100'
                        }`}
                    >
                        No leídas
                    </button>
                    <button
                        onClick={() => setFilter('alerts')}
                        className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                            filter === 'alerts' 
                                ? 'bg-sky-600 text-white' 
                                : 'bg-white text-gray-600 hover:bg-gray-100'
                        }`}
                    >
                        Alertas
                    </button>
                    <div className="flex-1" />
                    {unreadCount > 0 && (
                        <button
                            onClick={markAllAsRead}
                            className="flex items-center px-3 py-1.5 text-sm text-sky-600 hover:bg-sky-50 rounded-lg transition-colors"
                        >
                            <Check className="w-4 h-4 mr-1" />
                            Todo leído
                        </button>
                    )}
                </div>

                <div className="flex-1 overflow-y-auto">
                    {loading && notifications.length === 0 ? (
                        <div className="flex items-center justify-center h-40">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600"></div>
                        </div>
                    ) : filteredNotifications.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-40 text-gray-500">
                            <Bell className="w-12 h-12 mb-2 text-gray-300" />
                            <p>Sin notificaciones</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-gray-100">
                            {filteredNotifications.map((notification) => (
                                <div
                                    key={notification.id}
                                    className={`p-4 hover:bg-gray-50 transition-colors cursor-pointer ${
                                        !notification.read ? 'bg-blue-50/50' : ''
                                    }`}
                                    onClick={() => !notification.read && markAsRead(notification.id)}
                                >
                                    <div className="flex items-start space-x-3">
                                        <div className="flex-shrink-0 mt-0.5">
                                            {getSeverityIcon(notification.severity)}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center justify-between">
                                                <p className={`text-sm font-medium truncate ${
                                                    !notification.read ? 'text-gray-900' : 'text-gray-700'
                                                }`}>
                                                    {notification.title}
                                                </p>
                                                {getTypeIcon(notification.type)}
                                            </div>
                                            <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                                                {notification.message}
                                            </p>
                                            <div className="flex items-center justify-between mt-2">
                                                <div className="flex items-center text-xs text-gray-400">
                                                    <Clock className="w-3 h-3 mr-1" />
                                                    {formatTime(notification.createdAt)}
                                                </div>
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        deleteNotification(notification.id);
                                                    }}
                                                    className="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </div>
                                        {!notification.read && (
                                            <div className="w-2 h-2 bg-sky-500 rounded-full flex-shrink-0 mt-2" />
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function NotificationBadge() {
    const [unreadCount, setUnreadCount] = useState(2);
    const [showPanel, setShowPanel] = useState(false);
    const [demoNotifications] = useState([
        {
            id: 'alert-sys-1',
            type: 'system',
            title: 'Sistema activo',
            message: 'Skyfusion Analytics conectado correctamente',
            severity: 'info',
            read: false,
            createdAt: new Date().toISOString()
        },
        {
            id: 'alert-sys-2',
            type: 'alert',
            title: 'Alertas activas en COMBEIMA',
            message: '2 alertas monitoreadas en la cuenca',
            severity: 'warning',
            read: false,
            createdAt: new Date().toISOString()
        }
    ]);

    return (
        <>
            <button
                onClick={() => setShowPanel(true)}
                className="relative p-2 text-gray-600 hover:text-sky-600 hover:bg-sky-50 rounded-lg transition-colors"
            >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 w-5 h-5 flex items-center justify-center text-xs font-bold bg-red-500 text-white rounded-full">
                        {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                )}
            </button>
            
            <NotificationPanel 
                isOpen={showPanel} 
                onClose={() => setShowPanel(false)} 
                externalNotifications={demoNotifications}
            />
        </>
    );
}

export { NotificationPanel, NotificationBadge };
export default NotificationPanel;