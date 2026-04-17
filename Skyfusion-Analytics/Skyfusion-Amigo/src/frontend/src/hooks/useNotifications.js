import { useState, useEffect, useCallback, useRef } from 'react';
import { io } from 'socket.io-client';
import api from '../services/api';

const SOCKET_URL = process.env.REACT_APP_API_URL 
    ? process.env.REACT_APP_API_URL.replace('/api/v1', '')
    : 'http://localhost:3001';

export function useNotifications() {
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const socketRef = useRef(null);

    const fetchNotifications = useCallback(async (options = {}) => {
        const { unreadOnly = false, limit = 50, type = null } = options;
        
        try {
            setLoading(true);
            setError(null);
            
            const params = new URLSearchParams();
            if (unreadOnly) params.append('unreadOnly', 'true');
            if (limit) params.append('limit', limit.toString());
            if (type) params.append('type', type);
            
            const queryString = params.toString();
            const url = queryString 
                ? `/notifications?${queryString}` 
                : '/notifications';
            
            const response = await api.get(url);
            
            setNotifications(response.notifications || []);
            setUnreadCount(response.unreadCount || 0);
            
            return response;
        } catch (err) {
            setError(err.message);
            console.error('Error fetching notifications:', err);
            return { notifications: [], unreadCount: 0 };
        } finally {
            setLoading(false);
        }
    }, []);

    const markAsRead = useCallback(async (notificationId) => {
        try {
            await api.put(`/notifications/${notificationId}/read`);
            
            setNotifications(prev => 
                prev.map(n => 
                    n.id === notificationId 
                        ? { ...n, read: true, readAt: new Date().toISOString() }
                        : n
                )
            );
            
            setUnreadCount(prev => Math.max(0, prev - 1));
            
            return true;
        } catch (err) {
            console.error('Error marking notification as read:', err);
            return false;
        }
    }, []);

    const markAllAsRead = useCallback(async () => {
        try {
            await api.put('/notifications/read-all');
            
            setNotifications(prev => 
                prev.map(n => ({ ...n, read: true, readAt: new Date().toISOString() }))
            );
            
            setUnreadCount(0);
            
            return true;
        } catch (err) {
            console.error('Error marking all as read:', err);
            return false;
        }
    }, []);

    const deleteNotification = useCallback(async (notificationId) => {
        try {
            await api.delete(`/notifications/${notificationId}`);
            
            const deleted = notifications.find(n => n.id === notificationId);
            
            setNotifications(prev => prev.filter(n => n.id !== notificationId));
            
            if (deleted && !deleted.read) {
                setUnreadCount(prev => Math.max(0, prev - 1));
            }
            
            return true;
        } catch (err) {
            console.error('Error deleting notification:', err);
            return false;
        }
    }, [notifications]);

    const sendTestNotification = useCallback(async (data) => {
        try {
            const response = await api.post('/notifications/test', data);
            return response;
        } catch (err) {
            console.error('Error sending test notification:', err);
            throw err;
        }
    }, []);

    const getStats = useCallback(async () => {
        try {
            const response = await api.get('/notifications/stats');
            return response;
        } catch (err) {
            console.error('Error getting notification stats:', err);
            return { total: 0, unread: 0, byType: {}, bySeverity: {} };
        }
    }, []);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) return;

        const socket = io(SOCKET_URL, {
            transports: ['websocket'],
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
        });

        socketRef.current = socket;

        socket.on('connect', () => {
            console.log('Notification socket connected');
            socket.emit('authenticate', token);
        });

        socket.on('authenticated', ({ userId }) => {
            console.log('Socket authenticated for user:', userId);
        });

        socket.on('auth_error', ({ error }) => {
            console.warn('Socket auth error:', error);
        });

        socket.on('notification', (notification) => {
            console.log('New notification received:', notification);
            
            setNotifications(prev => [notification, ...prev]);
            
            if (!notification.read) {
                setUnreadCount(prev => prev + 1);
            }
        });

        socket.on('disconnect', () => {
            console.log('Notification socket disconnected');
        });

        socket.on('connect_error', (err) => {
            console.error('Socket connection error:', err);
        });

        return () => {
            socket.disconnect();
        };
    }, []);

    return {
        notifications,
        unreadCount,
        loading,
        error,
        fetchNotifications,
        markAsRead,
        markAllAsRead,
        deleteNotification,
        sendTestNotification,
        getStats
    };
}

export function useAuth() {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const login = useCallback(async (email, password) => {
        try {
            setLoading(true);
            setError(null);
            
            const response = await api.post('/auth/login', { email, password });
            
            localStorage.setItem('token', response.token);
            localStorage.setItem('user', JSON.stringify(response.user));
            
            setUser(response.user);
            
            return response;
        } catch (err) {
            setError(err.response?.data?.error || err.message || 'Error en el login');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    const register = useCallback(async (userData) => {
        try {
            setLoading(true);
            setError(null);
            
            const response = await api.post('/auth/register', userData);
            
            localStorage.setItem('token', response.token);
            localStorage.setItem('user', JSON.stringify(response.user));
            
            setUser(response.user);
            
            return response;
        } catch (err) {
            setError(err.response?.data?.error || err.message || 'Error en el registro');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    const logout = useCallback(() => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setUser(null);
    }, []);

    const checkAuth = useCallback(async () => {
        const token = localStorage.getItem('token');
        const savedUser = localStorage.getItem('user');
        
        if (!token) {
            setLoading(false);
            return null;
        }
        
        if (savedUser) {
            setUser(JSON.parse(savedUser));
        }
        
        try {
            const response = await api.get('/auth/me');
            setUser(response.user);
            localStorage.setItem('user', JSON.stringify(response.user));
            return response.user;
        } catch (err) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            setUser(null);
            return null;
        } finally {
            setLoading(false);
        }
    }, []);

    const updateProfile = useCallback(async (updates) => {
        try {
            const response = await api.put('/auth/profile', updates);
            
            setUser(response.user);
            localStorage.setItem('user', JSON.stringify(response.user));
            
            return response;
        } catch (err) {
            setError(err.response?.data?.error || err.message || 'Error actualizando perfil');
            throw err;
        }
    }, []);

    useEffect(() => {
        checkAuth();
    }, [checkAuth]);

    return {
        user,
        loading,
        error,
        login,
        register,
        logout,
        checkAuth,
        updateProfile,
        isAuthenticated: !!user
    };
}

export default useNotifications;