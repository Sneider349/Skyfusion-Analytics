import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [permissions, setPermissions] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isGuest, setIsGuest] = useState(false);

    const login = useCallback(async (email, password) => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await api.post('/auth/login', { email, password });
            
            localStorage.setItem('token', response.token);
            localStorage.setItem('user', JSON.stringify(response.user));
            localStorage.setItem('permissions', JSON.stringify(response.permissions || {}));
            localStorage.setItem('isGuest', 'false');
            
            setUser(response.user);
            setPermissions(response.permissions || {});
            setIsGuest(false);
            
            return response;
        } catch (err) {
            const errorMessage = err.message || 'Error en el login';
            setError(errorMessage);
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    const register = useCallback(async (userData) => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await api.post('/auth/register', userData);
            
            localStorage.setItem('token', response.token);
            localStorage.setItem('user', JSON.stringify(response.user));
            localStorage.setItem('permissions', JSON.stringify(response.permissions || {}));
            localStorage.setItem('isGuest', 'false');
            
            setUser(response.user);
            setPermissions(response.permissions || {});
            setIsGuest(false);
            
            return response;
        } catch (err) {
            const errorMessage = err.message || 'Error en el registro';
            setError(errorMessage);
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    const loginAsGuest = useCallback(async () => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await api.post('/auth/guest');
            
            localStorage.setItem('token', response.token);
            localStorage.setItem('user', JSON.stringify(response.user));
            localStorage.setItem('permissions', JSON.stringify(response.permissions || {}));
            localStorage.setItem('isGuest', 'true');
            localStorage.setItem('guestExpiresAt', response.user.expiresAt);
            
            setUser(response.user);
            setPermissions(response.permissions || {});
            setIsGuest(true);
            
            return response;
        } catch (err) {
            const errorMessage = err.message || 'Error al crear sesión de invitado';
            setError(errorMessage);
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    const logout = useCallback(() => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('permissions');
        localStorage.removeItem('isGuest');
        localStorage.removeItem('guestExpiresAt');
        
        setUser(null);
        setPermissions(null);
        setIsGuest(false);
    }, []);

    const checkAuth = useCallback(async () => {
        const token = localStorage.getItem('token');
        const savedUser = localStorage.getItem('user');
        const savedPermissions = localStorage.getItem('permissions');
        const guestStatus = localStorage.getItem('isGuest');
        
        if (!token) {
            setLoading(false);
            return null;
        }
        
        if (savedUser) {
            setUser(JSON.parse(savedUser));
        }
        
        if (savedPermissions) {
            setPermissions(JSON.parse(savedPermissions));
        }
        
        setIsGuest(guestStatus === 'true');
        
        try {
            const response = await api.get('/auth/me');
            setUser(response.user);
            setPermissions(response.permissions || {});
            localStorage.setItem('user', JSON.stringify(response.user));
            localStorage.setItem('permissions', JSON.stringify(response.permissions || {}));
            setLoading(false);
            return response.user;
        } catch (err) {
            const guestExpiry = localStorage.getItem('guestExpiresAt');
            if (guestExpiry && new Date(guestExpiry) > new Date()) {
                console.log('Sesión de invitado aún válida, manteniendo...');
                setLoading(false);
                return JSON.parse(localStorage.getItem('user') || 'null');
            }
            
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            localStorage.removeItem('permissions');
            localStorage.removeItem('isGuest');
            localStorage.removeItem('guestExpiresAt');
            
            setUser(null);
            setPermissions(null);
            setIsGuest(false);
            setLoading(false);
            return null;
        }
    }, []);

    const hasPermission = useCallback((permission) => {
        if (!permissions) return false;
        return permissions[permission] === true;
    }, [permissions]);

    const canPerform = useCallback((action) => {
        return hasPermission(action);
    }, [hasPermission]);

    const getSessionInfo = useCallback(() => {
        if (isGuest) {
            const expiresAt = localStorage.getItem('guestExpiresAt');
            return {
                type: 'guest',
                expiresAt: expiresAt ? new Date(expiresAt) : null,
                remainingTime: expiresAt 
                    ? Math.max(0, new Date(expiresAt) - new Date()) 
                    : 0
            };
        }
        return {
            type: user?.role || 'user',
            expiresAt: null,
            remainingTime: null
        };
    }, [isGuest, user]);

    useEffect(() => {
        checkAuth();
    }, [checkAuth]);

    const value = {
        user,
        permissions,
        loading,
        error,
        isGuest,
        login,
        register,
        loginAsGuest,
        logout,
        checkAuth,
        hasPermission,
        canPerform,
        getSessionInfo,
        isAuthenticated: !!user
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth debe usarse dentro de un AuthProvider');
    }
    return context;
}

export default AuthContext;
