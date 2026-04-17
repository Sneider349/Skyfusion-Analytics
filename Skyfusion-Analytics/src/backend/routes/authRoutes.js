const express = require('express');
const router = express.Router();
const jwt = require('jsonwebtoken');
const User = require('../models/User');
const { logger } = require('../config/logger');

const JWT_SECRET = process.env.JWT_SECRET || 'skyfusion-secret-key-2024';

function generateToken(user) {
    return jwt.sign(
        {
            id: user.id,
            email: user.email,
            username: user.username,
            role: user.role,
            catchments: user.catchments
        },
        JWT_SECRET,
        { expiresIn: '72h' }
    );
}

router.post('/register', async (req, res) => {
    try {
        const { username, email, password, fullName, catchments } = req.body;
        
        if (!username || !email || !password) {
            return res.status(400).json({
                error: ' username, email y password son requeridos'
            });
        }
        
        if (password.length < 6) {
            return res.status(400).json({
                error: 'La contraseña debe tener al menos 6 caracteres'
            });
        }
        
        const user = await User.createUser({
            username,
            email,
            password,
            fullName,
            catchments
        });
        
        const token = generateToken(user);
        
        logger.info(`Nuevo usuario registrado: ${email}`);
        
        res.status(201).json({
            message: 'Usuario creado exitosamente',
            token,
            user: User.getPublicUser(user),
            permissions: User.getPermissions(user.role)
        });
    } catch (error) {
        logger.error('Error en registro:', error);
        res.status(400).json({ error: error.message });
    }
});

router.post('/login', async (req, res) => {
    try {
        const { email, password } = req.body;
        
        if (!email || !password) {
            return res.status(400).json({
                error: 'Email y password son requeridos'
            });
        }
        
        const user = await User.validateCredentials(email, password);
        
        if (!user) {
            return res.status(401).json({
                error: 'Credenciales inválidas'
            });
        }
        
        User.updateLastLogin(user.id);
        
        const token = generateToken(user);
        
        logger.info(`Usuario logueado: ${email}`);
        
        res.json({
            message: 'Login exitoso',
            token,
            user: User.getPublicUser(user),
            permissions: User.getPermissions(user.role)
        });
    } catch (error) {
        logger.error('Error en login:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

router.post('/guest', async (req, res) => {
    try {
        const guestSession = User.createGuestSession();
        
        const token = jwt.sign(
            {
                id: guestSession.id,
                email: guestSession.email,
                username: guestSession.username,
                role: 'guest',
                catchments: guestSession.catchments,
                isGuest: true
            },
            JWT_SECRET,
            { expiresIn: '24h' }
        );
        
        logger.info(`Sesión de invitado creada: ${guestSession.id}`);
        
        res.status(201).json({
            message: 'Sesión de invitado creada exitosamente',
            token,
            user: {
                id: guestSession.id,
                username: guestSession.username,
                email: guestSession.email,
                role: 'guest',
                fullName: guestSession.fullName,
                catchments: guestSession.catchments,
                isGuest: true,
                expiresAt: guestSession.expiresAt
            },
            permissions: User.getPermissions('guest'),
            limitations: {
                canExportData: false,
                canCreateAlerts: false,
                canManageCatchments: false,
                sessionDuration: '24 horas',
                notice: 'Esta es una sesión de demostración. Para acceso completo, regístrese o inicie sesión.'
            }
        });
    } catch (error) {
        logger.error('Error al crear sesión de invitado:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

router.get('/me', async (req, res) => {
    try {
        const authHeader = req.headers.authorization;
        
        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return res.status(401).json({ error: 'Token no proporcionado' });
        }
        
        const token = authHeader.split(' ')[1];
        
        const decoded = jwt.verify(token, JWT_SECRET);
        
        const user = User.findById(decoded.id);
        
        if (!user) {
            return res.status(404).json({ error: 'Usuario no encontrado' });
        }
        
        res.json({ 
            user: User.getPublicUser(user),
            permissions: User.getPermissions(user.role)
        });
    } catch (error) {
        logger.error('Error en /me:', error);
        res.status(401).json({ error: 'Token inválido o expirado' });
    }
});

router.put('/profile', async (req, res) => {
    try {
        const authHeader = req.headers.authorization;
        
        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return res.status(401).json({ error: 'Token no proporcionado' });
        }
        
        const token = authHeader.split(' ')[1];
        const decoded = jwt.verify(token, JWT_SECRET);
        
        const { fullName, catchments, preferences } = req.body;
        
        const updatedUser = User.updateUser(decoded.id, {
            fullName,
            catchments,
            preferences
        });
        
        res.json({
            message: 'Perfil actualizado',
            user: User.getPublicUser(updatedUser)
        });
    } catch (error) {
        logger.error('Error en /profile:', error);
        res.status(400).json({ error: error.message });
    }
});

router.post('/change-password', async (req, res) => {
    try {
        const authHeader = req.headers.authorization;
        
        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return res.status(401).json({ error: 'Token no proporcionado' });
        }
        
        const token = authHeader.split(' ')[1];
        const decoded = jwt.verify(token, JWT_SECRET);
        
        const { currentPassword, newPassword } = req.body;
        
        if (!currentPassword || !newPassword) {
            return res.status(400).json({
                error: 'Contraseña actual y nueva son requeridas'
            });
        }
        
        if (newPassword.length < 6) {
            return res.status(400).json({
                error: 'La nueva contraseña debe tener al menos 6 caracteres'
            });
        }
        
        const user = User.findById(decoded.id);
        
        const isValid = await User.comparePassword(currentPassword, user.password);
        
        if (!isValid) {
            return res.status(401).json({
                error: 'Contraseña actual incorrecta'
            });
        }
        
        const hashedPassword = await User.hashPassword(newPassword);
        
        User.updateUser(decoded.id, { password: hashedPassword });
        
        res.json({ message: 'Contraseña actualizada exitosamente' });
    } catch (error) {
        logger.error('Error en change-password:', error);
        res.status(400).json({ error: error.message });
    }
});

router.get('/users', async (req, res) => {
    try {
        const authHeader = req.headers.authorization;
        
        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return res.status(401).json({ error: 'Token no proporcionado' });
        }
        
        const token = authHeader.split(' ')[1];
        const decoded = jwt.verify(token, JWT_SECRET);
        
        if (decoded.role !== 'admin') {
            return res.status(403).json({ error: 'Solo administradores pueden ver usuarios' });
        }
        
        const users = User.getAllUsers();
        
        res.json({ users });
    } catch (error) {
        logger.error('Error en /users:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

module.exports = router;