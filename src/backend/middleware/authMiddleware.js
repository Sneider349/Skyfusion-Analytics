const jwt = require('jsonwebtoken');
const User = require('../models/User');
const { logger } = require('../config/logger');

const JWT_SECRET = process.env.JWT_SECRET || 'skyfusion-secret-key-2024';

function authenticateToken(req, res, next) {
    const authHeader = req.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({ 
            error: 'Token no proporcionado',
            code: 'TOKEN_MISSING'
        });
    }
    
    const token = authHeader.split(' ')[1];
    
    try {
        const decoded = jwt.verify(token, JWT_SECRET);
        
        const user = User.findById(decoded.id);
        
        if (!user && !decoded.isGuest) {
            return res.status(404).json({ 
                error: 'Usuario no encontrado',
                code: 'USER_NOT_FOUND'
            });
        }
        
        if (decoded.isGuest && decoded.exp) {
            const expTime = decoded.exp * 1000;
            if (Date.now() > expTime) {
                return res.status(401).json({ 
                    error: 'Sesión de invitado expirada',
                    code: 'GUEST_SESSION_EXPIRED',
                    suggestion: 'Inicie sesión con una cuenta registrada para continuar.'
                });
            }
        }
        
        req.user = decoded;
        req.permissions = User.getPermissions(decoded.role);
        
        next();
    } catch (error) {
        logger.error('Error en autenticación:', error);
        return res.status(401).json({ 
            error: 'Token inválido o expirado',
            code: 'TOKEN_INVALID'
        });
    }
}

function requirePermission(permission) {
    return (req, res, next) => {
        if (!req.permissions) {
            return res.status(401).json({ 
                error: 'Permisos no definidos',
                code: 'PERMISSIONS_MISSING'
            });
        }
        
        if (req.permissions[permission] !== true) {
            logger.warn(`Acceso denegado: Usuario ${req.user?.id} intentó acceder a ${permission}`);
            return res.status(403).json({ 
                error: `No tienes permiso para realizar esta acción`,
                code: 'PERMISSION_DENIED',
                requiredPermission: permission,
                suggestion: req.user.role === 'guest' 
                    ? 'Regístrese para obtener acceso completo a esta función.'
                    : 'Contacte al administrador para solicitar permisos.'
            });
        }
        
        next();
    };
}

function requireRoles(...roles) {
    return (req, res, next) => {
        if (!req.user) {
            return res.status(401).json({ 
                error: 'Usuario no autenticado',
                code: 'USER_NOT_AUTHENTICATED'
            });
        }
        
        if (!roles.includes(req.user.role)) {
            logger.warn(`Acceso denegado: Usuario ${req.user.id} con rol ${req.user.role} intentó acceder a ruta restringida`);
            return res.status(403).json({ 
                error: 'No tienes el rol necesario para acceder a este recurso',
                code: 'ROLE_REQUIRED',
                requiredRoles: roles,
                currentRole: req.user.role
            });
        }
        
        next();
    };
}

function blockGuests(req, res, next) {
    if (req.user && req.user.role === 'guest') {
        logger.warn(`Invitado ${req.user.id} intentó acceder a recurso restringido: ${req.originalUrl}`);
        return res.status(403).json({ 
            error: 'Los invitados no pueden acceder a este recurso',
            code: 'GUEST_ACCESS_DENIED',
            suggestion: 'Regístrese para obtener acceso completo.'
        });
    }
    
    next();
}

function requireAuthenticated(req, res, next) {
    if (!req.user) {
        return res.status(401).json({ 
            error: 'Autenticación requerida',
            code: 'AUTHENTICATION_REQUIRED',
            guestAlternative: '/api/auth/guest'
        });
    }
    next();
}

function optionalAuth(req, res, next) {
    const authHeader = req.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        req.user = null;
        req.permissions = User.getPermissions('guest');
        return next();
    }
    
    const token = authHeader.split(' ')[1];
    
    try {
        const decoded = jwt.verify(token, JWT_SECRET);
        req.user = decoded;
        req.permissions = User.getPermissions(decoded.role);
    } catch (error) {
        req.user = null;
        req.permissions = User.getPermissions('guest');
    }
    
    next();
}

module.exports = {
    authenticateToken,
    requirePermission,
    requireRoles,
    blockGuests,
    requireAuthenticated,
    optionalAuth
};
