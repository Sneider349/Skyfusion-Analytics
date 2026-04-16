# Dev Container - Skyfusion Analytics
# ====================================

Configuración de desarrollo para GitHub Codespaces con versiones
fijadas y consistentes de librerías geoespaciales.

## Versiones Fijadas

| Librería | Versión |
|----------|---------|
| GDAL | 3.6.2 |
| Rasterio | 1.3.8 |
| Python | 3.10 |
| NumPy | 1.24.3 |

## Uso

### Abrir en Codespaces

1. Fork del repositorio
2. GitHub → Code → Create codespace
3. Esperar construcción (~5-10 min)
4. Verificar versiones:
   ```bash
   gdal-config --version  # 3.6.2
   python -c "import rasterio; print(rasterio.__version__)"  # 1.3.8
   ```

### Reconstruir Contenedor

Si hay cambios en `Dockerfile` o `requirements.txt`:

1. `F1` → "Dev Containers: Rebuild Container"
2. O ejecutar en terminal:
   ```bash
   devcontainer rebuild
   ```

## Estructura

```
.devcontainer/
├── Dockerfile           # Imagen base + GDAL + Rasterio
├── devcontainer.json   # Configuración de Codespaces
├── pre-init.sh         # Pre-inicialización
├── post-create.sh      # Post-creación (instala deps)
├── post-attach.sh      # Al reconectar
└── on-open.sh         # Al abrir proyecto
```

## Dependencias Instaladas

### Geoespacial
- GDAL 3.6.2 (binarios del sistema)
- Rasterio 1.3.8 (Python)
- GeoPandas 0.14.0
- Shapely 2.0.2
- pyproj 3.6.1

### ML/AI
- TensorFlow 2.15.0
- scikit-learn 1.3.2
- OpenCV 4.8.1

### Datos
- Pandas 2.1.4
- NumPy 1.24.3
- earthengine-api 0.1.374

## Solución de Problemas

### Error: libgdal.so not found

```bash
# Verificar que GDAL está instalado
ldconfig -p | grep gdal

# Reinstalar si es necesario
apt-get update && apt-get install -y gdal-bin libgdal-dev
```

### Error: Rasterio version mismatch

```bash
# Desinstalar versión actual
pip uninstall rasterio

# Instalar versión fija
pip install rasterio==1.3.8 --force-reinstall --no-cache-dir
```

### Error: Python version

El contenedor usa Python 3.10. Verificar:

```bash
python --version  # Debe ser 3.10.x
```

## Integración con GitHub Actions

Para CI/CD, usar la misma imagen:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    container:
      image: mcr.microsoft.com/vscode/devcontainers/python:3.10
    steps:
      - run: |
          apt-get update && apt-get install -y gdal-bin libgdal-dev
          pip install GDAL==3.6.2 rasterio==1.3.8
          pip install -r requirements.txt
```

## Notas

- Las versiones están fijadas para garantizar reproducibilidad
- No usar `>=` o `latest` para GDAL/Rasterio
- Al actualizar, modificar tanto `Dockerfile` como `requirements.txt`
