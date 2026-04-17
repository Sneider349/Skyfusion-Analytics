#!/bin/bash
# Post-attach script para devcontainer de Skyfusion Analytics
# Ejecuta cada vez que el usuario se reconecta al contenedor

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Skyfusion Analytics - Dev Container                         ║"
echo "║  GDAL: $(gdal-config --version) | Rasterio: $(python -c 'import rasterio; print(rasterio.__version__)')                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Mostrar estado del proyecto
if [ -d "/workspace/.git" ]; then
    echo "Git Status:"
    git status --short 2>/dev/null || echo "  Repositorio no disponible"
fi

echo ""
echo "Directorios de datos:"
ls -la /workspace/data/raw/satelite/metadata/ 2>/dev/null || echo "  Directorios no inicializados"
