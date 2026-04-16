#!/bin/bash
# Post-create script para devcontainer de Skyfusion Analytics
# Ejecuta DESPUÉS de que el contenedor se crea

set -e

echo "=========================================="
echo "Skyfusion Analytics - Post-Creación"
echo "=========================================="

# ===========================================
# VERIFICACIÓN DE VERSIONES
# ===========================================
echo ""
echo "Verificando versiones de librerías geoespaciales..."
echo "------------------------------------------------"

GDAL_VER=$(gdal-config --version)
echo "GDAL: $GDAL_VER"

python -c "import rasterio; print('Rasterio:', rasterio.__version__)"
python -c "import rasterio; print('GDAL (via rasterio):', rasterio.__gdal_version__)"
python -c "import numpy; print('NumPy:', numpy.__version__)"
python -c "import geopandas; print('GeoPandas:', geopandas.__version__)" 2>/dev/null || echo "GeoPandas: No instalado (opcional)"

# ===========================================
# CONFIGURACIÓN DE ENTORNO
# ===========================================
echo ""
echo "Configurando entorno de desarrollo..."

# Crear directorio de datos si no existe
mkdir -p /workspace/data/raw/satelite/metadata/logs
mkdir -p /workspace/data/output
mkdir -p /workspace/logs

# Configurar git
git config --global init.defaultBranch main
git config --global pull.rebase false

# ===========================================
# INSTALAR PAQUETES ADICIONALES
# ===========================================
echo ""
echo "Instalando dependencias adicionales del proyecto..."

# Instalar desde los archivos requirements del proyecto
if [ -f "/workspace/src/python/requirements-ml.txt" ]; then
    echo "  Instalando requirements-ml.txt..."
    pip install --quiet -r /workspace/src/python/requirements-ml.txt
fi

if [ -f "/workspace/src/python/requirements-preprocessing.txt" ]; then
    echo "  Instalando requirements-preprocessing.txt..."
    pip install --quiet -r /workspace/src/python/requirements-preprocessing.txt
fi

# ===========================================
# VERIFICACIÓN FINAL
# ===========================================
echo ""
echo "=========================================="
echo "CONFIGURACIÓN COMPLETADA"
echo "=========================================="
echo ""
echo "Comandos útiles:"
echo "  python -c 'import rasterio; print(rasterio.__version__)'  # Verificar rasterio"
echo "  gdalinfo --version                                         # Verificar GDAL"
echo "  pytest src/python/                                         # Ejecutar tests"
echo ""
echo "Para iniciar el servidor de desarrollo:"
echo "  npm start  (desde la raíz)"
echo ""
echo "=========================================="
