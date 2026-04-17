# 🚀 Guía de Inicio - Skyfusion Analytics Frontend

## ✅ Problema Resuelto

El error `cd : No se encuentra la ruta de acceso` ocurría porque intentabas hacer `cd src/frontend` cuando ya estabas en ese directorio. ¡Ya está solucionado!

## 🎯 Instrucciones de Inicio Correctas

### ✓ Opción 1: Desde la raíz del proyecto (RECOMENDADO)
```powershell
cd src\frontend
npm start
```

### ✓ Opción 2: Si ya estás en src/frontend
```powershell
npm start
```

### ❌ NUNCA hagas esto:
```powershell
cd src/frontend; npm start  # ❌ Error si ya estás aquí
```

## 🔧 Configuración Realizada

✅ **setupProxy.js** - Proxy para desarrollo  
✅ **.env.development** - Variables de entorno  
✅ **.env** - Token de Mapbox y URLs  
✅ **http-proxy-middleware** - Instalado  

## 📋 Scripts Disponibles

```bash
npm start          # ✓ Inicia servidor en puerto 3000
npm run build      # Compila para producción
npm test           # Ejecuta pruebas
npm run eject      # Acceso a configuración (⚠️ irreversible)
```

## 🔌 Conectividad

| Servicio | URL |
|----------|-----|
| **Frontend** | http://localhost:3000 |
| **Backend API** | http://localhost:3001 (proxy automático) |
| **WebSocket** | ws://localhost:3001 |
| **Red Local** | http://10.78.203.157:3000 |

## ⚡ Características

- ✅ Hot reload automático
- ✅ Proxy de desarrollo configurado
- ✅ Mapbox GL integrado
- ✅ Tailwind CSS listo
- ✅ Socket.io cliente configurado
- ✅ Chart.js y D3 disponibles

## 📝 Troubleshooting

**Puerto 3000 ocupado?** → npm preguntará si usar otro puerto (3001, 3002, etc.)

**npm modules no encontrados?** → Ejecuta `npm install`

**Cambios no se reflejan?** → Recarga el navegador (Ctrl+Shift+R)

## ✨ ¡Listo para comenzar!

```powershell
npm start
```

Accede a **http://localhost:3000** en tu navegador 🚀
