const fs = require('fs');
const path = require('path');
const bcrypt = require('bcrypt');
const { logger } = require('../config/logger');

const USERS_FILE = path.join(__dirname, '../../data/users.json');

const ROL_PERMISSIONS = {
    admin: {
        canViewDashboard: true,
        canViewMap: true,
        canViewAnalytics: true,
        canViewPredictions: true,
        canViewAlerts: true,
        canViewReports: true,
        canManageUsers: true,
        canManageSensors: true,
        canManageProjects: true,
        canManageCatchments: true,
        canExportData: true,
        canCreateAlerts: true,
        canModifySettings: true,
        maxCatchments: Infinity
    },
    operator: {
        canViewDashboard: true,
        canViewMap: true,
        canViewAnalytics: true,
        canViewPredictions: true,
        canViewAlerts: true,
        canViewReports: true,
        canManageUsers: false,
        canManageSensors: true,
        canManageProjects: false,
        canManageCatchments: true,
        canExportData: true,
        canCreateAlerts: true,
        canModifySettings: false,
        maxCatchments: 3
    },
    user: {
        canViewDashboard: true,
        canViewMap: true,
        canViewAnalytics: true,
        canViewPredictions: true,
        canViewAlerts: true,
        canViewReports: true,
        canManageUsers: false,
        canManageSensors: false,
        canManageProjects: false,
        canManageCatchments: false,
        canExportData: false,
        canCreateAlerts: false,
        canModifySettings: false,
        maxCatchments: 1
    },
    guest: {
        canViewDashboard: true,
        canViewMap: true,
        canViewAnalytics: true,
        canViewPredictions: true,
        canViewAlerts: false,
        canViewReports: false,
        canManageUsers: false,
        canManageSensors: false,
        canManageProjects: false,
        canManageCatchments: false,
        canExportData: false,
        canCreateAlerts: false,
        canModifySettings: false,
        maxCatchments: 0
    }
};

const DEFAULT_USERS = [
    {
        id: 'user-001',
        username: 'admin',
        email: 'admin@skyfusion.com',
        password: '$2b$10$XQxGxQXxQxGxQXxQxGxQOeIxGxQXxQxGxQXxQxGxQXxQxGxQXOe',
        role: 'admin',
        fullName: 'Administrador Skyfusion',
        catchments: ['COMBEIMA', 'COELLO', 'OPHIR'],
        preferences: {
            notifications: true,
            emailAlerts: true,
            language: 'es'
        },
        createdAt: new Date().toISOString(),
        lastLogin: null,
        status: 'active'
    },
    {
        id: 'user-002',
        username: 'operador',
        email: 'operador@skyfusion.com',
        password: '$2b$10$XQxGxQXxQxGxQXxQxGxQXxQxGxQXxQxGxQXxQxGxQXxQxGxQXOe',
        role: 'operator',
        fullName: 'Operador de Cuenca',
        catchments: ['COMBEIMA'],
        preferences: {
            notifications: true,
            emailAlerts: false,
            language: 'es'
        },
        createdAt: new Date().toISOString(),
        lastLogin: null,
        status: 'active'
    }
];

function ensureUsersFile() {
    const dataDir = path.join(__dirname, '../../data');
    if (!fs.existsSync(dataDir)) {
        fs.mkdirSync(dataDir, { recursive: true });
    }
    if (!fs.existsSync(USERS_FILE)) {
        fs.writeFileSync(USERS_FILE, JSON.stringify(DEFAULT_USERS, null, 2));
        logger.info('Users file created with default users');
    }
}

function getUsers() {
    ensureUsersFile();
    try {
        const data = fs.readFileSync(USERS_FILE, 'utf-8');
        return JSON.parse(data);
    } catch (error) {
        logger.error('Error reading users:', error);
        return [];
    }
}

function saveUsers(users) {
    try {
        fs.writeFileSync(USERS_FILE, JSON.stringify(users, null, 2));
        return true;
    } catch (error) {
        logger.error('Error saving users:', error);
        return false;
    }
}

async function hashPassword(password) {
    return bcrypt.hash(password, 10);
}

async function comparePassword(password, hashedPassword) {
    try {
        return await bcrypt.compare(password, hashedPassword);
    } catch (error) {
        return false;
    }
}

function findByEmail(email) {
    const users = getUsers();
    return users.find(u => u.email === email);
}

function findByUsername(username) {
    const users = getUsers();
    return users.find(u => u.username === username);
}

function findById(id) {
    const users = getUsers();
    return users.find(u => u.id === id);
}

async function createUser(userData) {
    const users = getUsers();
    
    if (findByEmail(userData.email)) {
        throw new Error('El correo electrónico ya está registrado');
    }
    
    if (findByUsername(userData.username)) {
        throw new Error('El nombre de usuario ya está en uso');
    }
    
    const hashedPassword = await hashPassword(userData.password);
    
    const newUser = {
        id: `user-${Date.now()}`,
        username: userData.username,
        email: userData.email,
        password: hashedPassword,
        role: userData.role || 'user',
        fullName: userData.fullName || userData.username,
        catchments: userData.catchments || [],
        preferences: {
            notifications: true,
            emailAlerts: true,
            language: 'es'
        },
        createdAt: new Date().toISOString(),
        lastLogin: null,
        status: 'active'
    };
    
    users.push(newUser);
    saveUsers(users);
    
    logger.info(`User created: ${newUser.email}`);
    
    return newUser;
}

async function validateCredentials(email, password) {
    const user = findByEmail(email);
    
    if (!user) {
        return null;
    }
    
    const isValid = await comparePassword(password, user.password);
    
    if (!isValid) {
        return null;
    }
    
    return user;
}

function updateUser(id, updates) {
    const users = getUsers();
    const index = users.findIndex(u => u.id === id);
    
    if (index === -1) {
        throw new Error('Usuario no encontrado');
    }
    
    const allowedUpdates = ['fullName', 'catchments', 'preferences', 'role'];
    
    for (const key of allowedUpdates) {
        if (updates[key] !== undefined) {
            users[index][key] = updates[key];
        }
    }
    
    users[index].updatedAt = new Date().toISOString();
    
    saveUsers(users);
    
    return users[index];
}

function updateLastLogin(id) {
    const users = getUsers();
    const index = users.findIndex(u => u.id === id);
    
    if (index !== -1) {
        users[index].lastLogin = new Date().toISOString();
        saveUsers(users);
    }
}

function getPublicUser(user) {
    const { password, ...publicUser } = user;
    return publicUser;
}

function getAllUsers() {
    return getUsers().map(getPublicUser);
}

function getUserById(id) {
    const user = findById(id);
    return user ? getPublicUser(user) : null;
}

function getPermissions(role) {
    return ROL_PERMISSIONS[role] || ROL_PERMISSIONS.guest;
}

function hasPermission(role, permission) {
    const permissions = getPermissions(role);
    return permissions[permission] === true;
}

function createGuestSession() {
    return {
        id: `guest-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        username: `guest_${Date.now()}`,
        email: `guest_${Date.now()}@guest.local`,
        role: 'guest',
        fullName: 'Invitado',
        catchments: [],
        preferences: {
            notifications: false,
            emailAlerts: false,
            language: 'es'
        },
        createdAt: new Date().toISOString(),
        lastLogin: new Date().toISOString(),
        status: 'active',
        isGuest: true,
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
    };
}

module.exports = {
    ensureUsersFile,
    getUsers,
    saveUsers,
    hashPassword,
    comparePassword,
    findByEmail,
    findByUsername,
    findById,
    createUser,
    validateCredentials,
    updateUser,
    updateLastLogin,
    getPublicUser,
    getAllUsers,
    getUserById,
    ROL_PERMISSIONS,
    getPermissions,
    hasPermission,
    createGuestSession
};