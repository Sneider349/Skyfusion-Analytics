# 🚀 Guía de Inicio Rápido - Sesión de Invitado

## Resumen de lo Implementado

Se ha creado un sistema completo de autenticación con soporte para invitados:

### ✅ Características Implementadas

1. **Frontend Completo**
   - Página de Login con 3 opciones: Login, Registro, Entrar como Invitado
   - Manejo de tokens JWT con persistencia en localStorage
   - Banner de notificación para usuarios invitados
   - Sistema de permisos por rol
   - Rutas protegidas

2. **Backend Mejorado**
   - Endpoint `/api/auth/guest` para crear sesiones de invitado
   - Sistema de permisos granulares (16 permisos)
   - Middleware de autenticación flexible
   - Protección de rutas por rol

3. **Componentes Nuevos**
   - `AuthContext.js` - Contexto de autenticación global
   - `LoginPage.js` - Página de login moderna
   - `GuestComponents.js` - Banner y componentes para invitados
   - `LogoutPage.js` - Página de cierre de sesión

---

## 🚀 Cómo Usar

### Paso 1: Iniciar el Backend

```bash
cd "C:\Users\edwar\OneDrive - uniminuto.edu\Skyfusion Analytics"
npm run dev
```

El backend estará corriendo en: **http://localhost:3001**

### Paso 2: Iniciar el Frontend

En otra terminal:

```bash
cd "C:\Users\edwar\OneDrive - uniminuto.edu\Skyfusion Analytics\src\frontend"
npm start
```

El frontend estará corriendo en: **http://localhost:3000**

### Paso 3: Probar la Aplicación

1. Abre tu navegador en **http://localhost:3000**
2. Verás la página de login con 3 opciones:
   - **Iniciar Sesión** - Para usuarios registrados
   - **Crear Cuenta** - Para registrarse
   - **Entrar como Invitado** - Para exploración sin registro

---

## 📱 Opciones de Login

### Opción 1: Entrar como Invitado (Recomendado para probar)

1. Haz clic en **"Entrar como Invitado"**
2. Recibirás un token JWT con acceso limitado
3. Serás redirigido al dashboard
4. Verás un banner amarillo indicando "Modo Invitado"
5. Tendrás acceso a:
   - ✅ Ver dashboard
   - ✅ Ver mapas
   - ✅ Ver análisis
   - ✅ Ver predicciones
6. NO tendrás acceso a:
   - ❌ Crear alertas
   - ❌ Exportar datos
   - ❌ Gestionar sensores

### Opción 2: Iniciar Sesión con Usuario Existente

**Credenciales de prueba:**

**Administrador:**
- Email: `admin@skyfusion.com`
- Contraseña: `admin123` ⚠️ (contraseña hasheada, ver notas abajo)

**Operador:**
- Email: `operador@skyfusion.com`
- Contraseña: `operador123` ⚠️

⚠️ **Nota:** Las contraseñas están hasheadas con bcrypt. Para probar login real, necesitas crear usuarios primero.

### Opción 3: Crear Nueva Cuenta

1. Haz clic en **"¿No tienes cuenta? Regístrate aquí"**
2. Completa el formulario:
   - Nombre de usuario
   - Correo electrónico
   - Contraseña (mínimo 6 caracteres)
   - Confirmar contraseña
3. Haz clic en **"Crear Cuenta"**
4. Recibirás un token JWT con rol "user"
5. Serás redirigido al dashboard

---

## 🎨 Cómo Funciona el Frontend

### Estructura de Archivos

```
src/frontend/src/
├── context/
│   └── AuthContext.js          # Contexto de autenticación global
├── pages/
│   ├── LoginPage.js            # Página de login
│   └── LogoutPage.js          # Página de logout
├── components/
│   ├── GuestComponents.js      # Banner y componentes para invitados
│   └── Header.js              # Header actualizado
├── services/
│   └── api.js                 # API mejorada con auth
└── App.js                     # App con routing protegido
```

### Flujo de Autenticación

```
1. Usuario abre app → App.js carga AuthContext
2. AuthContext verifica si hay token en localStorage
3. Si no hay token → Redirige a /login
4. Si hay token → Verifica con backend
5. Si es válido → Carga Dashboard
6. Si expira → Muestra error y limpia localStorage
```

### Permisos Almacenados

Cuando un usuario inicia sesión, se guardan en localStorage:

```javascript
{
  token: "eyJhbGciOiJIUzI1NiIs...",
  user: {
    id: "user-001",
    username: "admin",
    email: "admin@skyfusion.com",
    role: "admin",
    fullName: "Administrador Skyfusion",
    catchments: ["COMBEIMA", "COELLO", "OPHIR"],
    isGuest: false
  },
  permissions: {
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
  isGuest: "false"
}
```

---

## 🔒 Permisos por Rol

### Administrador (admin)
- ✅ Acceso total a todas las funcionalidades
- ✅ Gestión de usuarios
- ✅ Gestión de sensores
- ✅ Gestión de proyectos
- ✅ Exportar datos
- ✅ Crear alertas

### Operador (operator)
- ✅ Ver dashboard, mapas, análisis, predicciones, alertas, reportes
- ✅ Gestión de sensores
- ✅ Gestión de cuencas
- ✅ Exportar datos
- ✅ Crear alertas
- ❌ Gestión de usuarios
- ❌ Gestión de proyectos

### Usuario (user)
- ✅ Ver dashboard, mapas, análisis, predicciones, alertas, reportes
- ❌ Gestión de usuarios, sensores, proyectos
- ❌ Exportar datos
- ❌ Crear alertas

### Invitado (guest)
- ✅ Ver dashboard, mapas, análisis, predicciones
- ❌ Ver alertas personalizadas
- ❌ Ver reportes
- ❌ Gestión de usuarios, sensores, proyectos
- ❌ Exportar datos
- ❌ Crear alertas
- ⏰ Sesión expira en 24 horas

---

## 🌐 Endpoints de la API

### Autenticación

```bash
# Login de usuario
POST /api/v1/auth/login
Body: { email, password }

# Registro de usuario
POST /api/v1/auth/register
Body: { email, password, username, fullName? }

# Crear sesión de invitado
POST /api/v1/auth/guest

# Obtener usuario actual
GET /api/v1/auth/me
Headers: Authorization: Bearer <token>

# Actualizar perfil
PUT /api/v1/auth/profile
Headers: Authorization: Bearer <token>
Body: { fullName?, catchments?, preferences? }
```

### Datos (acceso público/con invitado)

```bash
# Métricas de cuenca
GET /api/v1/demo/metrics/:catchmentId

# Alertas
GET /api/v1/alerts

# Predicciones
GET /api/v1/predictions/:catchment

# Narrativa
GET /api/v1/demo/narrative/:catchmentId

# Cuencas
GET /api/v1/demo/catchments
```

### Rutas Protegidas

```bash
# Notificaciones (requiere auth)
GET /api/v1/notifications
POST /api/v1/notifications/test
PUT /api/v1/notifications/:id/read
```

---

## 📊 Ejemplo de Respuesta de Invitado

Cuando creas una sesión de invitado con `POST /api/v1/auth/guest`:

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
  }
}
```

---

## 🧪 Probar Endpoints

### Probar Login de Invitado (curl)

```bash
# Crear sesión de invitado
curl -X POST http://localhost:3001/api/v1/auth/guest

# Ver información de la API
curl http://localhost:3001/api/v1/info

# Probar acceso con token
TOKEN="tu_token_aqui"
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:3001/api/v1/predictions/COMBEIMA
```

### Probar Login Normal

```bash
# Registro
curl -X POST http://localhost:3001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123","username":"testuser"}'

# Login
curl -X POST http://localhost:3001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123"}'
```

---

## 🎯 Características Destacadas

### 1. Banner de Invitado
Cuando un invitado inicia sesión, aparece un banner amarillo en la parte superior con:
- Indicación de "Modo Invitado"
- Tiempo restante de la sesión
- Lista de funciones disponibles y no disponibles
- Botón para registrarse y obtener acceso completo

### 2. Iconos Diferenciados
- **Usuarios normales**: Icono de persona (👤)
- **Invitados**: Icono de corona (👑)

### 3. Protección de Rutas
Todas las rutas principales (/analisis, /proyectos, /estadisticas, /admin) están protegidas:
- Si no hay sesión → Redirige a /login
- Si la sesión expira → Redirige a /login con mensaje de error

### 4. Persistencia de Sesión
- Tokens guardados en localStorage
- Al recargar la página, se verifica el token con el backend
- Si es válido, se mantiene la sesión
- Si expira, se limpia todo y se pide login

---

## 🔧 Solución de Problemas

### Error: "Token inválido o expirado"

1. Verifica que el backend esté corriendo: `curl http://localhost:3001/health`
2. Limpia localStorage del navegador
3. Intenta crear una nueva sesión de invitado

### Error: "No puedes acceder a este recurso"

Esto es correcto. Indica que estás usando una sesión de invitado y el recurso requiere permisos elevados.

### Frontend no conecta con Backend

1. Verifica que el proxy en `setupProxy.js` apunte a `http://localhost:3001`
2. Verifica que el backend esté corriendo en el puerto 3001
3. Revisa la consola del navegador para errores de CORS

### Sesión de invitado expira inmediatamente

La sesión dura 24 horas. Si expira antes:
1. Verifica que el reloj del sistema esté correcto
2. Verifica que no estés en una zona horaria diferente

---

## 📝 Notas Importantes

### Contraseñas Hasheadas
Las contraseñas en el archivo `users.json` están hasheadas con bcrypt. Para probar login real, necesitas:
1. Usar el endpoint de registro para crear usuarios
2. O hashear manualmente las contraseñas

### Tokens JWT
- Los tokens expiran en 72 horas para usuarios normales
- Los tokens de invitado expiran en 24 horas
- Los tokens se verifican en cada request

### Base de Datos
Los usuarios se guardan en:
- Backend: `src/data/users.json`

---

## 🚀 Próximos Pasos

### Para Usuarios Finales
1. ✅ Ir a http://localhost:3000
2. ✅ Elegir opción de login
3. ✅ Explorar el dashboard
4. ✅ Probar funcionalidades según rol

### Para Desarrolladores
1. Revisar documentación en `docs/GUEST_SESSION.md`
2. Ejecutar pruebas en `tests/test-guest-session.js`
3. Personalizar permisos en `src/backend/models/User.js`
4. Agregar más endpoints protegidos

---

## 📞 Soporte

Si tienes problemas:
1. Verifica que ambos servidores (backend y frontend) estén corriendo
2. Revisa la consola del navegador (F12)
3. Revisa los logs del backend
4. Consulta la documentación en `docs/`

---

**Versión**: 1.0.0  
**Última actualización**: 2024  
**Autor**: Skyfusion Analytics Team
