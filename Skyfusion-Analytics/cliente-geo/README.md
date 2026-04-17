# Sistema GEO - Cliente Frontend

> **Sistema de Gestión y Análisis de Datos Geográficos para monitoreo ambiental**
>
> Desarrollado con React 19 + Vite 7 + React Bootstrap

---

## Tabla de Contenidos

1. [Descripción del Proyecto](#descripción-del-proyecto)
2. [Estructura del Proyecto](#estructura-del-proyecto)
3. [Tecnologías y Dependencias](#tecnologías-y-dependencias)
4. [Instalación y Configuración](#instalación-y-configuración)
5. [Scripts Disponibles](#scripts-disponibles)
6. [Variables de Entorno](#variables-de-entorno)
7. [Arquitectura de la Aplicación](#arquitectura-de-la-aplicación)
8. [Sistema de Rutas](#sistema-de-rutas)
9. [Autenticación y Autorización](#autenticación-y-autorización)
10. [Servicios API](#servicios-api)
11. [Componentes Principales](#componentes-principales)
12. [Guía de Desarrollo](#guía-de-desarrollo)

---

## Descripción del Proyecto

**Cliente-GEO** es el frontend de un sistema de gestión geográfica desarrollado para la **Corporación Uniminuto**, diseñado para:

- **Monitoreo ambiental** de recursos hídricos (ríos)
- **Gestión de proyectos** de investigación
- **Análisis de datos geográficos** y ambientales
- **Generación de reportes** técnicos y estadísticos
- **Administración de usuarios** con roles diferenciados

### Características Principales

- Dashboard interactivo con mapa geográfico
- Módulo de análisis de datos espaciales
- Gestión completa de proyectos
- Reportes y estadísticas en tiempo real
- Perfil de usuario con configuración
- Sistema de autenticación JWT
- Control de acceso basado en roles (RBAC)

---

## Estructura del Proyecto

```
cliente-geo/
├── public/
│   └── Logo.png                 # Logo de la aplicación
├── src/
│   ├── components/
│   │   ├── auth/               # Componentes de autenticación
│   │   │   ├── Login.jsx       # Formulario de inicio de sesión
│   │   │   ├── Registro.jsx     # Formulario de registro
│   │   │   └── RutaProtegida.jsx # HOC para rutas protegidas
│   │   ├── pages/              # Páginas principales
│   │   │   ├── Dashboard.jsx       # Panel principal del usuario
│   │   │   ├── DashboardProtegido.jsx # Dashboard con datos protegidos
│   │   │   └── HomePage.jsx        # Página de inicio pública
│   │   ├── sections/           # Secciones modulares
│   │   │   ├── Analisis.jsx        # Gestión de análisis
│   │   │   ├── Estadisticas.jsx    # Estadísticas y métricas
│   │   │   ├── Proyectos.jsx        # Gestión de proyectos
│   │   │   ├── Reportes.jsx        # Centro de reportes
│   │   │   ├── Resultados.jsx      # Resultados y conclusiones
│   │   │   └── Rios.jsx            # Monitoreo de ríos
│   │   ├── profile/            # Componentes de perfil
│   │   │   ├── VistaPerfil.jsx         # Vista del perfil
│   │   │   ├── VistaConfiguracion.jsx  # Configuración de cuenta
│   │   │   ├── InfoPerfil.jsx          # Información del perfil
│   │   │   └── ConfiguracionPerfil.jsx # Formulario de edición
│   │   └── Estructura/
│   │       └── Layout.jsx      # Layout principal con navbar y footer
│   ├── services/               # Servicios API
│   │   ├── auth.service.js     # Servicio de autenticación
│   │   ├── user.service.js     # Servicio de usuarios/perfil
│   │   └── analysisApi.js      # Servicio de análisis
│   ├── App.jsx                 # Componente principal con rutas
│   ├── App.css                 # Estilos de App
│   ├── main.jsx                # Punto de entrada
│   └── index.css               # Estilos globales
├── .env                        # Variables de entorno
├── .gitignore                  # Archivos ignorados por Git
├── eslint.config.js            # Configuración de ESLint
├── index.html                  # HTML principal
├── package.json                # Dependencias y scripts
├── vite.config.js              # Configuración de Vite
└── README.md                   # Este archivo
```

---

## Tecnologías y Dependencias

### Dependencias de Producción

| Paquete | Versión | Descripción |
|---------|---------|-------------|
| `react` | ^19.2.0 | Biblioteca principal de UI |
| `react-dom` | ^19.2.0 | Renderizado de React para DOM |
| `react-router-dom` | ^7.9.5 | Enrutamiento de la aplicación |
| `react-bootstrap` | ^2.10.10 | Componentes Bootstrap para React |
| `bootstrap` | ^5.3.8 | Framework CSS responsive |
| `axios` | ^1.13.2 | Cliente HTTP para API calls |
| `lucide-react` | ^0.553.0 | Iconos SVG modernos |

### Dependencias de Desarrollo

| Paquete | Versión | Descripción |
|---------|---------|-------------|
| `vite` | ^7.2.2 | Bundler y servidor de desarrollo |
| `@vitejs/plugin-react` | ^5.1.0 | Plugin Vite para React |
| `eslint` | ^9.39.1 | Linter de código |
| `@eslint/js` | ^9.39.1 | Configuración ESLint |
| `eslint-plugin-react-hooks` | ^5.2.0 | Reglas para hooks de React |
| `eslint-plugin-react-refresh` | ^0.4.24 | Fast refresh para ESLint |
| `globals` | ^16.5.0 | Variables globales para ESLint |

---

## Instalación y Configuración

### Requisitos Previos

- **Node.js** versión 18 o superior
- **npm** o **pnpm** como gestor de paquetes
- Servidor backend corriendo en `http://localhost:3000`

### Pasos de Instalación

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd cliente-geo

# 2. Instalar dependencias
npm install

# 3. Configurar variables de entorno
# Editar el archivo .env con la URL del backend

# 4. Iniciar el servidor de desarrollo
npm run dev
```

### Configuración del Backend

El proyecto espera un backend en Express.js corriendo en el puerto 3000. Asegúrate de que el backend exponga las siguientes rutas:

- `POST /api/auth/login` - Inicio de sesión
- `POST /api/auth/register` - Registro de usuarios
- `GET /api/users/profile/me` - Obtener perfil
- `PUT /api/users/profile/me` - Actualizar perfil
- `POST /api/users/profile/avatar` - Subir avatar
- `GET /api/analisis` - Listar análisis
- `POST /api/analisis` - Crear análisis
- `PUT /api/analisis/:id` - Actualizar análisis
- `DELETE /api/analisis/:id` - Eliminar análisis

---

## Scripts Disponibles

| Script | Descripción |
|--------|-------------|
| `npm run dev` | Inicia el servidor de desarrollo con HMR |
| `npm run build` | Genera la versión de producción optimizada |
| `npm run preview` | Previsualiza la build de producción |
| `npm run lint` | Ejecuta ESLint para verificar código |

### Uso de Scripts

```bash
# Desarrollo
npm run dev

# Build para producción
npm run build

# Preview del build
npm run preview

# Linting
npm run lint
```

---

## Variables de Entorno

### Archivo `.env`

```env
# El prefijo VITE_ es OBLIGATORIO para que Vite lea la variable
VITE_API_BASE_URL=http://localhost:3000/api
```

### Variables Disponibles

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `VITE_API_BASE_URL` | URL base del API backend | `http://localhost:3000/api` |

> **Importante:** Las variables de entorno en Vite deben tener el prefijo `VITE_` para ser accesibles en el código.

---

## Arquitectura de la Aplicación

### Patrón de Diseño

El proyecto sigue una **arquitectura basada en componentes** con las siguientes capas:

```
┌─────────────────────────────────────────┐
│           Presentation Layer            │
│  (Components, Pages, Layouts)          │
├─────────────────────────────────────────┤
│           Business Logic Layer          │
│  (Services, Hooks, State Management)    │
├─────────────────────────────────────────┤
│             Data Access Layer           │
│  (API calls, localStorage)             │
└─────────────────────────────────────────┘
```

### Flujo de Datos

1. **Usuario interactúa** con un componente
2. **Componente llama** a un servicio API
3. **Servicio realiza** petición HTTP con token JWT
4. **Respuesta actualiza** el estado del componente
5. **UI se re-renderiza** con los nuevos datos

### Gestión de Estado

El proyecto utiliza **localStorage** para persistir:

- `token` - Token JWT de autenticación
- `userId` - ID del usuario
- `userName` - Nombre del usuario
- `userEmail` - Correo electrónico
- `userRole` - Rol del usuario (1=Admin, 2=Usuario)

---

## Sistema de Rutas

### Configuración de Rutas (`App.jsx`)

```jsx
// Rutas Públicas
/                → HomePage
/login           → Login
/registro        → Registro

// Rutas Protegidas (requieren autenticación)
/dashboard       → Dashboard (disponible para Admin y Usuario)
/perfil          → VistaPerfil
/configuracion   → VistaConfiguracion
/analisis        → Analisis
/proyectos       → Proyectos
/reportes        → Reportes
/rios            → Rios
/estadisticas    → Estadisticas
/resultados      → Resultados

// Rutas de Administrador (solo rol 1)
/admin           → AdminPage
/roles           → Gestión de Roles
/usuarios        → Gestión de Usuarios

// 404
*                → Página no encontrada
```

### Roles de Usuario

| Rol | ID | Permisos |
|-----|-----|----------|
| Administrador | 1 | Acceso completo a todas las rutas |
| Usuario | 2 | Acceso a rutas de usuario estándar |

### Componente de Ruta Protegida

```jsx
<RutaProtegida requiredRoles={[ADMIN_ROLE, USER_ROLE]}>
  <ComponenteProtegido />
</RutaProtegida>
```

---

## Autenticación y Autorización

### Flujo de Autenticación

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│  Login   │───▶│ Backend  │───▶│  JWT     │
│  Form    │    │  API     │    │  Token   │
└──────────┘    └──────────┘    └──────────┘
                                      │
                                      ▼
                              ┌──────────────┐
                              │ localStorage │
                              └──────────────┘
                                      │
                                      ▼
                              ┌──────────────┐
                              │ Auth Header │
                              │ (Bearer)    │
                              └──────────────┘
```

### Servicio de Autenticación (`auth.service.js`)

```javascript
// Funciones principales
login(correo, contrasena)    // Inicia sesión y guarda token
register(nombre, correo, contrasena)  // Registra nuevo usuario
isAuthenticated()            // Verifica si hay token
getCurrentUser()            // Obtiene datos del usuario
logout()                    // Cierra sesión
```

### Protección de Rutas

El componente `RutaProtegida` verifica:

1. **Existencia de token** en localStorage
2. **Validez del rol** del usuario
3. **Redirección apropiada** según el estado

---

## Servicios API

### 1. Auth Service (`auth.service.js`)

```javascript
// URL base del API
const API_URL = 'http://localhost:3000/api/auth';

// Métodos
- login(correo, contrasena) → { token, user }
- register(nombre, correo, contrasena) → { message }
- isAuthenticated() → boolean
- getCurrentUser() → { id, name, email, role, token }
- logout() → void
```

### 2. User Service (`user.service.js`)

```javascript
// URL base del API
const API_URL = 'http://localhost:3000/api/users';

// Métodos
- getProfile() → User
- updateProfile(profileData) → User
- updatePrivacy(isPublic) → { isPublic }
- deleteAccount() → { message }
- uploadAvatar(formData) → { imagenUrl }
```

### 3. Analysis API (`analysisApi.js`)

```javascript
// URL base del API
const API_URL = 'http://localhost:3000/api/analisis';

// Métodos
- getAll() → Analysis[]
- getById(id) → Analysis
- create(data) → Analysis
- update(id, data) → Analysis
- delete(id) → { message }
- run(id) → { result }
- getIndices(id) → Indices[]
- getSensors(id) → Sensors[]
```

---

## Componentes Principales

### Layout (`Layout.jsx`)

Componente contenedor que incluye:

- **Navbar**: Barra de navegación superior con logo y menú de usuario
- **Sidebar**: Menú lateral desplegable (offcanvas)
- **Footer**: Pie de página con información de contacto
- **Content Area**: Área principal para el contenido

**Props:** `children` - Componentes hijos a renderizar

**Estado:**
- `showSidebar`: Controla la visibilidad del sidebar
- `user`: Datos del usuario autenticado

### Dashboard (`Dashboard.jsx`)

Página principal después del login que muestra:

- **Hero Section**: Bienvenida personalizada
- **Mapa Interactivo**: Representación geográfica del monitoreo
- **Panel de Análisis**: Descripción del proyecto e indicadores
- **Esquema de Flujo**: Pasos del proceso (Recolección → Análisis → Determinación)

### Login (`Login.jsx`)

Formulario de autenticación con:

- Campos: correo electrónico y contraseña
- Validación de campos requeridos
- Manejo de errores de autenticación
- Redirección automática al dashboard
- Enlace a página de registro

### Registro (`Registro.jsx`)

Formulario de registro con:

- Campos: nombre, correo, contraseña, confirmar contraseña
- Validación de coincidencia de contraseñas
- Requisito de mínimo 6 caracteres
- Redirección al login tras registro exitoso

### RutaProtegida (`RutaProtegida.jsx`)

HOC (Higher Order Component) que:

1. Verifica autenticación
2. Valida roles del usuario
3. Redirige según corresponda

### Secciones de Monitoreo

#### Rios (`Rios.jsx`)

- Lista de ríos monitoreados
- Indicadores de calidad del agua
- Temperatura, pH, caudal
- Estado de estaciones de monitoreo

#### Analisis (`Analisis.jsx`)

- CRUD completo de análisis
- Modal para crear/editar
- Estados: Pendiente, En Proceso, Completado, Fallido
- Ejecución de análisis

#### Proyectos (`Proyectos.jsx`)

- Gestión de proyectos de investigación
- Barra de progreso
- Estados: Iniciado, En Progreso, Completado
- Información de responsables y fechas

#### Reportes (`Reportes.jsx`)

- Centro de generación de reportes
- Lista de reportes disponibles
- Formatos: PDF, Excel, Word, CSV
- Exportación y envío por email

#### Estadisticas (`Estadisticas.jsx`)

- Métricas y KPIs
- Gráficos de tendencias
- Indicadores por categoría
- Proyecciones anuales

#### Resultados (`Resultados.jsx`)

- Conclusiones de estudios
- Parámetros medidos
- Recomendaciones generales
- Estados: Completado, En Revisión

### Componentes de Perfil

#### VistaPerfil (`VistaPerfil.jsx`)

- Muestra información del perfil
- Avatar con opción de cambio
- Toggle de privacidad
- Enlace a configuración

#### VistaConfiguracion (`VistaConfiguracion.jsx`)

- Formulario de edición de datos
- Cambio de contraseña
- Zona de peligro para eliminación de cuenta

#### InfoPerfil (`InfoPerfil.jsx`)

- Avatar con preview local
- Badges de rol
- Switch de visibilidad pública/privada
- Subida de imagen

#### ConfiguracionPerfil (`ConfiguracionPerfil.jsx`)

- Formulario de actualización
- Validación de datos
- Confirmación de eliminación

---

## Guía de Desarrollo

### Agregar Nueva Ruta

1. Crear el componente de página en `src/components/pages/`
2. Importar en `App.jsx`
3. Agregar la ruta en el componente `Routes`:

```jsx
<Route
  path="/nueva-ruta"
  element={
    <RutaProtegida requiredRoles={[ADMIN_ROLE, USER_ROLE]}>
      <NuevoComponente />
    </RutaProtegida>
  }
/>
```

### Agregar Nuevo Servicio API

1. Crear archivo en `src/services/`
2. Implementar métodos CRUD con axios
3. Incluir interceptor para token JWT
4. Exportar funciones del servicio

```javascript
// Ejemplo: src/services/nuevo.service.js
import axios from 'axios';

const API_URL = 'http://localhost:3000/api/nuevo';

const api = axios.create({
    baseURL: API_URL,
    headers: { 'Content-Type': 'application/json' }
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

export const nuevoService = {
    getAll: async () => {
        const response = await api.get('/');
        return response.data;
    },
    // ... más métodos
};
```

### Agregar Nuevo Componente de Sección

1. Crear en `src/components/sections/`
2. Usar Bootstrap para estilos
3. Incluir estilos hover para interactividad
4. Exportar como componente default

```jsx
const NuevoComponente = () => {
    return (
        <Container>
            {/* Contenido del componente */}
        </Container>
    );
};

export default NuevoComponente;
```

### Agregar Menú en Sidebar

Modificar el array `menuItems` en `Layout.jsx`:

```javascript
const menuItems = [
    // ... items existentes
    { 
        label: 'Nueva Sección', 
        path: '/nueva-ruta', 
        icon: '🆕', 
        protected: true,
        adminOnly: false  // true solo para admins
    },
];
```

### Configurar ESLint

El proyecto usa ESLint con configuración flat. Para modificar reglas, editar `eslint.config.js`:

```javascript
rules: {
    'no-unused-vars': ['error', { varsIgnorePattern: '^[A-Z_]' }],
    // Agregar más reglas según necesidad
}
```

### Deployment

```bash
# 1. Build de producción
npm run build

# 2. Preview local del build
npm run preview

# 3. Subir carpeta 'dist' al servidor
```

---

## Convenciones de Código

### Nomenclatura

- **Componentes**: PascalCase (`Dashboard.jsx`)
- **Servicios**: camelCase (`auth.service.js`)
- **Funciones**: camelCase (`getCurrentUser`)
- **Constantes**: UPPER_SNAKE_CASE (`ADMIN_ROLE`)

### Estructura de Componentes

```jsx
import React from 'react';
import { Componente } from 'react-bootstrap';

const MiComponente = ({ prop1, prop2 }) => {
    // Hooks al inicio
    const [state, setState] = useState();

    // Funciones
    const handleClick = () => { /* ... */ };

    // Render
    return (
        <div>
            {/* JSX */}
        </div>
    );
};

export default MiComponente;
```

### Imports

1. React y librerías externas
2. Componentes de react-bootstrap
3. Servicios y utilities
4. Componentes locales
5. Estilos (si es necesario)

---

## Troubleshooting

### Error: "Token inválido"

1. Verificar que el backend esté corriendo
2. Confirmar que la URL del API en `.env` es correcta
3. Limpiar localStorage: `localStorage.clear()`
4. Volver a iniciar sesión

### Error: "CORS"

El backend debe tener configurados los headers CORS:

```javascript
app.use(cors({
    origin: 'http://localhost:5173',  // Puerto de Vite
    credentials: true
}));
```

### Error: "No se encuentra el módulo"

```bash
# Reinstalar dependencias
rm -rf node_modules package-lock.json
npm install
```

### Puerto ocupado

Vite usa el puerto 5173 por defecto. Para cambiar:

```bash
npm run dev -- --port 3000
```

O en `vite.config.js`:

```javascript
export default defineConfig({
    server: {
        port: 3000
    }
});
```

---

## Contribución

1. Crear branch desde `develop`: `git checkout -b feature/nueva-funcion`
2. Realizar cambios siguiendo convenciones
3. Ejecutar `npm run lint` antes de commit
4. Crear Pull Request a `develop`

---

## Licencia

Este proyecto es propiedad de **Corporación Uniminuto** - © 2025

---

## Contacto

- **Email**: info@sistemageo.com
- **Teléfono**: +57 300 123 4567
- **Ubicación**: Ibagué, Tolima, Colombia
