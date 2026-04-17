# Matriz de Versiones - Skyfusion Analytics
# ============================================
# Este archivo documenta las versiones exactas de todas las librerías
# para garantizar reproducibilidad entre entornos

## Versiones Core (Fijadas)

| Librería | Versión | Notas |
|----------|---------|-------|
| Python | 3.10 | Largo soporte hasta octubre 2026 |
| GDAL | 3.6.2 | Version del sistema (apt) |
| Rasterio | 1.3.8 | Requiere GDAL 3.6.x |
| NumPy | 1.24.3 | Compatible con TF 2.15 |
| Pandas | 2.1.4 | Ultima version estable |

## Compatibilidad GDAL/Rasterio

| Rasterio | GDAL | Estado |
|----------|------|--------|
| 1.3.8 | 3.4.x, 3.5.x, 3.6.x | ✅ Recomendado |
| 1.3.9 | 3.4.x - 3.7.x | ✅ Latest |
| 1.4.x | 3.5.x - 3.8.x | ⚠️ Testing |

**Nota:** No mezclar versiones mayores de GDAL con rasterio compilado para versión diferente.

## Actualización de Versiones

Para actualizar versiones:

1. Verificar compatibilidad en https://rasterio.readthedocs.io/en/latest/installation.html
2. Actualizar `requirements.txt` en la raíz
3. Actualizar `Dockerfile` en `.devcontainer/`
4. Actualizar `docker-compose.yml` si aplica
5. Reconstruir el contenedor
6. Actualizar este archivo

## Verificación de Versiones

```bash
# Verificar GDAL
gdal-config --version

# Verificar Rasterio y su GDAL linked
python -c "import rasterio; print(rasterio.__version__, rasterio.__gdal_version__)"

# Verificar que todo esta instalado
pip list | grep -E "(GDAL|Rasterio|geopandas)"
```

## Entornos Soportados

| Entorno | Python | GDAL | Rasterio | Verificado |
|---------|--------|------|----------|------------|
| GitHub Codespaces | 3.10 | 3.6.2 | 1.3.8 | ✅ |
| Docker Local | 3.10 | 3.6.2 | 1.3.8 | ✅ |
| Windows (conda) | 3.10 | 3.6.2 | 1.3.8 | ⚠️ Requiere conda-forge |
| Linux Local | 3.10 | 3.6.2 | 1.3.8 | ⚠️ Requiere apt gdal-bin |
