# Directorio de Datos Satelitales Crudos

## Estructura
```
data/raw/satelite/
├── landsat/
│   ├── mss/           # Landsat 1-3 MSS (1972-1983)
│   ├── tm/            # Landsat 4-5 TM (1984-2012)
│   └── oli/           # Landsat 8-9 OLI/TIRS (2013-presente)
├── sentinel2/
│   ├── L1C/           # Nivel 1C (Top of Atmosphere)
│   └── L2A/           # Nivel 2A (Surface Reflectance)
└── metadata/
    ├── catalog.csv     # Catálogo maestro de imágenes
    ├── logs/           # Logs de descarga y validación
    └── checksums/      # Verificación de integridad
```

## Convenciones de Nomenclatura

### Landsat
- Formato: `YYYY/MM/DD/<scene_id>_B{band}.tif`
- Ejemplo: `1990/06/15/LT50080551990167XXX01_B3.tif`

### Sentinel-2
- Formato: Carpeta SAFE estándar Copernicus
- Ejemplo: `2023/01/15/S2A_MSIL2A_20230115T104421_N0400_R008_T18NUJ_20230115T123456.SAFE/`

## Catálogo (catalog.csv)
| Campo | Descripción |
|-------|-------------|
| scene_id | Identificador único de la escena |
| sensor | Tipo de sensor (LANDSAT_MSS, etc.) |
| acquisition_date | Fecha de adquisición |
| cloud_cover | Porcentaje de nubosidad |
| local_path | Ruta local del archivo |
| gee_asset_id | ID del asset en GEE |
| checksum_md5 | Hash MD5 del archivo |
| download_status | Estado de descarga |

## Uso
1. El preprocessor.py descarga imágenes desde GEE
2. Cada descarga se registra en catalog.csv
3. Los checksums se generan para verificación de integridad
4. Logs de errores en metadata/logs/
