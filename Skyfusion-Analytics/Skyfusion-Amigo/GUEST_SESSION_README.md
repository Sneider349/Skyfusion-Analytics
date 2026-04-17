# 🚀 Sesión de Invitado - Skyfusion Analytics

## ✨ Nueva Funcionalidad

Ahora puedes explorar **Skyfusion Analytics** sin necesidad de registrarte. La sesión de invitado te proporciona acceso limitado a las funcionalidades principales de la plataforma.

## 🎯 ¿Qué puedes hacer como invitado?

### ✅ Funcionalidades Disponibles
- 📊 Ver dashboard principal
- 🗺️ Explorar mapas interactivos
- 📈 Visualizar análisis de datos
- 🔮 Ver predicciones hídricas
- 🎓 Acceder a datos de demostración

### ❌ Funcionalidades Restringidas
- 🚫 Crear alertas personalizadas
- 🚫 Exportar datos
- 🚫 Gestionar sensores
- 🚫 Gestionar proyectos
- 🚫 Ver reportes avanzados

## 🔐 ¿Cómo funciona?

### 1️⃣ Crear Sesión de Invitado

Simplemente haz una solicitud POST al endpoint:

```bash
curl -X POST http://localhost:3000/api/auth/guest
```

**Respuesta:**
```json
{
    "message": "Sesión de invitado creada exitosamente",
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
        "id": "guest-1713123456789-abc123xyz",
        "username": "guest_1713123456789",
        "role": "guest",
        "fullName": "Invitado",
        "isGuest": true,
        "expiresAt": "2024-04-16T00:00:00.000Z"
    },
    "permissions": {
        "canViewDashboard": true,
        "canViewMap": true,
        "canViewAnalytics": true,
        "canViewPredictions": true,
        "canCreateAlerts": false,
        "canExportData": false,
        // ... más permisos
    }
}
```

### 2️⃣ Usar el Token

Incluye el token en tus solicitudes:

```bash
curl -H "Authorization: Bearer TU_TOKEN" \
     http://localhost:3000/api/predictions/COMBEIMA
```

### 3️⃣ Duración

⏰ La sesión de invitado dura **24 horas**

## 🛠️ Uso en tu Aplicación

### JavaScript/Node.js

```javascript
// Crear sesión de invitado
const response = await fetch('/api/auth/guest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
});

const { token, user, permissions } = await response.json();

// Guardar en localStorage
localStorage.setItem('token', token);
localStorage.setItem('isGuest', true);
```

### Verificar Permisos

```javascript
function canExport() {
    const permissions = JSON.parse(localStorage.getItem('permissions'));
    return permissions.canExportData;
}

if (canExport()) {
    // Mostrar botón de exportar
} else {
    // Mostrar mensaje de actualización
}
```

## 📡 Endpoints Disponibles

### 🌐 Acceso Público (con/sin token)

```bash
GET  /api/predictions/:catchment    # Ver predicciones
GET  /api/alerts                    # Ver alertas
GET  /api/demo/*                    # Datos de demostración
GET  /api/info                      # Información de la API
```

### 🔒 Requiere Autenticación

```bash
GET  /api/notifications             # Ver notificaciones
PUT  /api/notifications/:id/read    # Marcar como leída
POST /api/notifications/test        # Crear notificación (❌ Invitados no)
```

### 🚫 Solo Administradores

```bash
GET  /api/auth/users                # Ver usuarios
PUT  /api/auth/profile             # Actualizar perfil
```

## 🎨 Indicadores de Invitado

Cuando uses una sesión de invitado, la API incluirá:

```json
{
    "is_guest_access": true,
    "guest_notice": "Los invitados no reciben alertas personalizadas."
}
```

Usa estos campos para mostrar UI específica para invitados.

## 💡 Ejemplo: UI para Invitados

```javascript
// Mostrar banner de invitado
<div class="guest-banner" style="display: ${isGuest ? 'block' : 'none'}">
    <h3>🎓 Modo Invitado</h3>
    <p>Estás explorando con acceso limitado.</p>
    <p>⚠️ No puedes: Crear alertas, Exportar datos</p>
    <button onclick="window.location.href='/register'">
        🎉 Registrarse para acceso completo
    </button>
</div>
```

## 🔄 Comparación de Roles

| Funcionalidad | Guest | User | Operator | Admin |
|--------------|-------|------|----------|-------|
| Ver Dashboard | ✅ | ✅ | ✅ | ✅ |
| Ver Mapa | ✅ | ✅ | ✅ | ✅ |
| Ver Análisis | ✅ | ✅ | ✅ | ✅ |
| Ver Predicciones | ✅ | ✅ | ✅ | ✅ |
| Ver Reportes | ❌ | ✅ | ✅ | ✅ |
| Ver Alertas | ❌ | ✅ | ✅ | ✅ |
| Crear Alertas | ❌ | ❌ | ✅ | ✅ |
| Exportar Datos | ❌ | ❌ | ✅ | ✅ |
| Gestionar Sensores | ❌ | ❌ | ✅ | ✅ |
| Gestionar Usuarios | ❌ | ❌ | ❌ | ✅ |

## 🛡️ Seguridad

- ✅ Tokens JWT con expiración automática
- ✅ Permisos verificados en cada request
- ✅ Logging de intentos de acceso denegado
- ✅ Middleware robusto de autenticación
- ❌ Invitados no pueden modificar datos
- ❌ Acciones sensibles requieren permisos específicos

## 📚 Documentación

Para más detalles, consulta:
- [Documentación completa](./docs/GUEST_SESSION.md)
- [Documentación técnica](../SKYFUSION_ANALYTICS_Documentacion_Tecnica.md)
- Endpoint: `GET /api/info`

## 🧪 Probar la Funcionalidad

```bash
# 1. Iniciar el servidor
npm run dev

# 2. En otra terminal, ejecutar el script de prueba
node tests/test-guest-session.js
```

## ❓ Preguntas Frecuentes

### ¿Puedo convertir mi sesión de invitado en cuenta permanente?
¡Sí! Contacta a soporte o usa el formulario de registro para crear tu cuenta.

### ¿Mis datos de invitado se guardan?
No. Las sesiones de invitado son temporales y no se almacenan en la base de datos.

### ¿Puedo tener acceso completo temporalmente?
Regístrate para obtener acceso completo a todas las funcionalidades.

### ¿Qué pasa cuando expira mi sesión?
Recibirás un error 401. Puedes crear una nueva sesión de invitado o registrarte.

## 🆘 Soporte

- 📧 Email: soporte@skyfusion.com
- 📖 Documentación: [enlace]
- 🐛 Reportar problemas: GitHub Issues

## 🎉 ¡Empieza Ahora!

```bash
curl -X POST http://localhost:3000/api/auth/guest
```

¡Explora Skyfusion Analytics hoy mismo!

---

**Última actualización**: 2024  
**Versión**: 1.0.0
