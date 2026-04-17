# Sistema de Sesión de Invitado - Skyfusion Analytics

## Resumen

Se ha implementado un sistema completo de sesiones de invitado que permite a usuarios no autenticados acceder a funcionalidades limitadas de la plataforma sin necesidad de registro.

## Características Principales

### 1. Sesión de Invitado
- **Duración**: 24 horas
- **Token JWT**: Generado automáticamente
- **ID único**: Formato `guest-{timestamp}-{random}`
- **Permisos**: Limitados a solo lectura
- **No requiere**: Registro ni credenciales

### 2. Sistema de Permisos por Rol

El sistema define permisos granulares para cada rol:

```javascript
ROL_PERMISSIONS = {
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
        // Permisos de operador...
        maxCatchments: 3
    },
    user: {
        // Permisos de usuario registrado...
        maxCatchments: 1
    },
    guest: {
        canViewDashboard: true,
        canViewMap: true,
        canViewAnalytics: true,
        canViewPredictions: true,
        canViewAlerts: false,      // ❌
        canViewReports: false,     // ❌
        canManageUsers: false,
        canManageSensors: false,
        canManageProjects: false,
        canManageCatchments: false,
        canExportData: false,      // ❌
        canCreateAlerts: false,    // ❌
        canModifySettings: false,
        maxCatchments: 0
    }
}
```

## API Endpoints

### Crear Sesión de Invitado

```http
POST /api/auth/guest
```

**Respuesta exitosa:**
```json
{
    "message": "Sesión de invitado creada exitosamente",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
        "id": "guest-1713123456789-abc123xyz",
        "username": "guest_1713123456789",
        "email": "guest_1713123456789@guest.local",
        "role": "guest",
        "fullName": "Invitado",
        "catchments": [],
        "isGuest": true,
        "expiresAt": "2024-04-16T00:00:00.000Z"
    },
    "permissions": {
        "canViewDashboard": true,
        "canViewMap": true,
        "canViewAnalytics": true,
        "canViewPredictions": true,
        "canViewAlerts": false,
        "canViewReports": false,
        "canManageUsers": false,
        "canManageSensors": false,
        "canManageProjects": false,
        "canManageCatchments": false,
        "canExportData": false,
        "canCreateAlerts": false,
        "canModifySettings": false,
        "maxCatchments": 0
    },
    "limitations": {
        "canExportData": false,
        "canCreateAlerts": false,
        "canManageCatchments": false,
        "sessionDuration": "24 horas",
        "notice": "Esta es una sesión de demostración. Para acceso completo, regístrese o inicie sesión."
    }
}
```

### Middleware de Autenticación

El sistema incluye middleware flexibles:

```javascript
// Middleware disponibles
const { 
    authenticateToken,      // Requiere token válido
    optionalAuth,           // Opcional, permite acceso anónimo
    blockGuests,            // Bloquea acceso a invitados
    requirePermission,      // Verifica permiso específico
    requireRoles            // Verifica rol específico
} = require('../middleware/authMiddleware');
```

### Uso de Middleware

```javascript
// Ejemplo 1: Ruta pública con acceso opcional
router.get('/public-data', optionalAuth, (req, res) => {
    // Disponible para todos, req.user null si no hay token
});

// Ejemplo 2: Ruta protegida para usuarios autenticados
router.get('/user-data', authenticateToken, (req, res) => {
    // Requiere token válido
});

// Ejemplo 3: Ruta bloqueada para invitados
router.post('/create', authenticateToken, blockGuests, (req, res) => {
    // Usuarios autenticados no-invitados
});

// Ejemplo 4: Requiere permiso específico
router.post('/alert', authenticateToken, requirePermission('canCreateAlerts'), (req, res) => {
    // Requiere permiso específico
});

// Ejemplo 5: Requiere rol específico
router.get('/admin', authenticateToken, requireRoles('admin'), (req, res) => {
    // Solo admins
});
```

## Rutas Actualizadas

### Rutas con Acceso de Invitado

Las siguientes rutas ahora permiten acceso de invitado:

```http
GET /api/predictions/:catchment
GET /api/alerts
GET /api/demo/*
```

**Respuesta con marca de invitado:**
```json
{
    "catchment_id": "COMBEIMA",
    "is_guest_access": true,
    // ... datos
}
```

### Rutas Protegidas

Las siguientes rutas requieren autenticación y no permiten acceso de invitado:

```http
POST /api/notifications/test          # Requiere: canCreateAlerts
PUT  /api/notifications/:id/read     # Requiere: autenticación
POST /api/alerts/:id/acknowledge     # Requiere: canCreateAlerts
POST /api/predictions/trigger        # Bloquea invitados
```

**Respuesta de error para invitados:**
```json
{
    "error": "Los invitados no pueden acceder a este recurso",
    "code": "GUEST_ACCESS_DENIED",
    "suggestion": "Regístrese para obtener acceso completo."
}
```

### Rutas Exclusivas para Administradores

```http
GET  /api/auth/users                  # Solo admins
PUT  /api/auth/profile                # Solo admins
```

## Documentación de la API

```http
GET /api/info
```

Retorna información completa del sistema incluyendo:
- Versión de la API
- Métodos de autenticación
- Permisos por rol
- Endpoints públicos, autenticados y restringidos
- Detalles de la sesión de invitado

## Manejo de Errores

### Errores de Autenticación

```json
{
    "error": "Token no proporcionado",
    "code": "TOKEN_MISSING"
}
```

### Errores de Permisos

```json
{
    "error": "No tienes permiso para realizar esta acción",
    "code": "PERMISSION_DENIED",
    "requiredPermission": "canCreateAlerts",
    "suggestion": "Regístrese para obtener acceso completo a esta función."
}
```

### Errores de Invitado

```json
{
    "error": "Sesión de invitado expirada",
    "code": "GUEST_SESSION_EXPIRED",
    "suggestion": "Inicie sesión con una cuenta registrada para continuar."
}
```

## Ejemplo de Uso en Frontend

### Crear Sesión de Invitado

```javascript
async function createGuestSession() {
    try {
        const response = await fetch('/api/auth/guest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            localStorage.setItem('token', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
            localStorage.setItem('permissions', JSON.stringify(data.permissions));
            localStorage.setItem('isGuest', true);
            
            showWelcomeMessage(data.user);
            updateUIForGuest(data.limitations);
        }
    } catch (error) {
        console.error('Error creando sesión de invitado:', error);
    }
}
```

### Verificar Permisos

```javascript
function canPerformAction(permission) {
    const permissions = JSON.parse(localStorage.getItem('permissions') || '{}');
    return permissions[permission] === true;
}

function showActionButton() {
    if (canPerformAction('canCreateAlerts')) {
        document.getElementById('createAlertBtn').style.display = 'block';
    } else {
        document.getElementById('createAlertBtn').style.display = 'none';
        showUpgradePrompt();
    }
}
```

### UI para Invitados

```javascript
function updateUIForGuest(limitations) {
    const notice = `
        <div class="guest-notice">
            <h3>Modo Invitado</h3>
            <p>${limitations.notice}</p>
            <ul>
                <li>Duración: ${limitations.sessionDuration}</li>
                <li>Exportar datos: ❌</li>
                <li>Crear alertas: ❌</li>
                <li>Ver análisis: ✅</li>
            </ul>
            <button onclick="window.location.href='/register'">
                Registrarse para acceso completo
            </button>
        </div>
    `;
    
    document.getElementById('user-panel').innerHTML += notice;
}
```

## Base de Datos

Los usuarios invitados **NO** se almacenan en la base de datos. Son generados dinámicamente con:

- ID único temporal
- Token JWT con expiración de 24h
- Sin persistencia entre sesiones

## Seguridad

### Características de Seguridad

1. **Tokens JWT seguros**
   - Algoritmo HS256
   - Expiración automática de 24h para invitados
   - Verificación en cada request

2. **Middleware robusto**
   - Verificación de token en cada request
   - Validación de expiración
   - Logging de intentos de acceso denegado

3. **Protección de rutas**
   - Invitados no pueden modificar datos
   - Acciones sensibles requieren permisos específicos
   - Roles verificados en endpoints críticos

### Recomendaciones de Seguridad

1. **Para producción:**
   - Usar tokens más cortos para invitados (ej: 1 hora)
   - Implementar rate limiting
   - Agregar CAPTCHA para crear sesiones de invitado
   - Monitorizar uso excesivo

2. **Para mejor UX:**
   - Mostrar claramente qué funciones no están disponibles
   - Proporcionar CTAs claros para registro
   - Persistir preferencias de invitado (sin cuenta)

## Configuración

### Variables de Entorno

```bash
JWT_SECRET=tu-secreto-seguro
GUEST_SESSION_DURATION=24  # horas
```

### Personalización de Permisos

Modificar `src/backend/models/User.js`:

```javascript
ROL_PERMISSIONS.guest = {
    canViewDashboard: true,
    canViewMap: true,
    // ... agregar nuevos permisos
};
```

## Próximos Pasos Sugeridos

1. **Frontend:**
   - Implementar UI de sesión de invitado
   - Agregar indicadores visuales de permisos
   - Crear modal de registro desde modo invitado

2. **Backend:**
   - Implementar rate limiting para sesiones de invitado
   - Agregar CAPTCHA
   - Mejorar logging y métricas

3. **Testing:**
   - Pruebas de integración para sesión de invitado
   - Pruebas de permisos
   - Pruebas de expiración de token

4. **Documentación:**
   - Actualizar README
   - Agregar ejemplos de uso
   - Documentar API completa

## Soporte

Para soporte técnico o reportar problemas:
- GitHub Issues: [enlace]
- Email: soporte@skyfusion.com
- Documentación: [enlace]

---

**Versión**: 1.0.0  
**Última actualización**: 2024  
**Autor**: Skyfusion Analytics Team
