"""
Setup del Entorno de Datos Satelitales Crudos
==============================================
Skyfusion Analytics - Data Engineering

Script para inicializar y gestionar la estructura de directorios
data/raw/satelite/ incluyendo catálogos y logs.

Uso:
    python setup_raw_directory.py --init          # Inicializar estructura
    python setup_raw_directory.py --status        # Verificar estado
    python setup_raw_directory.py --cleanup        # Limpiar estructura
"""

import os
import sys
import csv
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import argparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DirectoryConfig:
    """Configuración de rutas del entorno de datos"""
    
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.resolve()
    DATA_RAW = PROJECT_ROOT / 'data' / 'raw' / 'satelite'
    
    LANDSAT_MSS = DATA_RAW / 'landsat' / 'mss'
    LANDSAT_TM = DATA_RAW / 'landsat' / 'tm'
    LANDSAT_OLI = DATA_RAW / 'landsat' / 'oli'
    
    SENTINEL2_L1C = DATA_RAW / 'sentinel2' / 'L1C'
    SENTINEL2_L2A = DATA_RAW / 'sentinel2' / 'L2A'
    
    METADATA_DIR = DATA_RAW / 'metadata'
    CATALOG_FILE = METADATA_DIR / 'catalog.csv'
    LOGS_DIR = METADATA_DIR / 'logs'
    CHECKSUMS_DIR = METADATA_DIR / 'checksums'
    
    OUTPUT_DIR = PROJECT_ROOT / 'data' / 'output'
    
    ALL_DIRECTORIES = [
        LANDSAT_MSS, LANDSAT_TM, LANDSAT_OLI,
        SENTINEL2_L1C, SENTINEL2_L2A,
        METADATA_DIR, LOGS_DIR, CHECKSUMS_DIR,
        OUTPUT_DIR
    ]
    
    SENSOR_PATHS = {
        'LANDSAT_MSS': LANDSAT_MSS,
        'LANDSAT_TM': LANDSAT_TM,
        'LANDSAT_OLI': LANDSAT_OLI,
        'SENTINEL2_L1C': SENTINEL2_L1C,
        'SENTINEL2_L2A': SENTINEL2_L2A
    }


class CatalogManager:
    """Gestor del catálogo de imágenes satelitales"""
    
    CATALOG_COLUMNS = [
        'scene_id', 'sensor', 'satellite', 'product_level',
        'acquisition_date', 'acquisition_time', 'cloud_cover',
        'bounds_min_lon', 'bounds_min_lat', 'bounds_max_lon', 'bounds_max_lat',
        'local_path', 'gee_asset_id', 'gee_collection',
        'checksum_md5', 'checksum_sha256',
        'file_size_bytes', 'download_status', 'download_timestamp',
        'downloaded_by', 'gee_task_id', 'notes'
    ]
    
    def __init__(self, catalog_path: Path):
        self.catalog_path = catalog_path
        self._ensure_catalog_exists()
    
    def _ensure_catalog_exists(self):
        """Crea el archivo CSV del catálogo si no existe"""
        if not self.catalog_path.exists():
            self.catalog_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.catalog_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.CATALOG_COLUMNS)
                writer.writeheader()
            logger.info(f"Catálogo creado: {self.catalog_path}")
    
    def add_entry(self, entry: Dict) -> bool:
        """Añade una entrada al catálogo"""
        try:
            entry.setdefault('download_status', 'pending')
            entry.setdefault('download_timestamp', datetime.now().isoformat())
            
            with open(self.catalog_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.CATALOG_COLUMNS)
                writer.writerow(entry)
            
            logger.debug(f"Entrada añadida: {entry.get('scene_id', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Error añadiendo entrada al catálogo: {e}")
            return False
    
    def update_entry(self, scene_id: str, updates: Dict) -> bool:
        """Actualiza una entrada existente en el catálogo"""
        try:
            rows = []
            updated = False
            
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for row in reader:
                    if row['scene_id'] == scene_id:
                        row.update(updates)
                        updated = True
                    rows.append(row)
            
            if updated:
                with open(self.catalog_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
                logger.info(f"Entrada actualizada: {scene_id}")
            
            return updated
        except Exception as e:
            logger.error(f"Error actualizando entrada: {e}")
            return False
    
    def get_entries(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Obtiene entradas del catálogo con filtros opcionales"""
        try:
            entries = []
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if filters:
                        if all(row.get(k) == v for k, v in filters.items()):
                            entries.append(row)
                    else:
                        entries.append(row)
            return entries
        except Exception as e:
            logger.error(f"Error leyendo catálogo: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del catálogo"""
        stats = {
            'total_entries': 0,
            'by_sensor': {},
            'by_status': {},
            'total_size_bytes': 0
        }
        
        try:
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    stats['total_entries'] += 1
                    
                    sensor = row.get('sensor', 'unknown')
                    stats['by_sensor'][sensor] = stats['by_sensor'].get(sensor, 0) + 1
                    
                    status = row.get('download_status', 'unknown')
                    stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                    
                    size = row.get('file_size_bytes', '0')
                    stats['total_size_bytes'] += int(size) if size.isdigit() else 0
        except Exception as e:
            logger.error(f"Error calculando estadísticas: {e}")
        
        return stats


class ChecksumManager:
    """Gestor de checksums para verificación de integridad"""
    
    def __init__(self, checksum_dir: Path):
        self.checksum_dir = checksum_dir
        self.checksum_dir.mkdir(parents=True, exist_ok=True)
    
    def calculate_md5(self, file_path: Path) -> str:
        """Calcula hash MD5 de un archivo"""
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    def calculate_sha256(self, file_path: Path) -> str:
        """Calcula hash SHA256 de un archivo"""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def verify_file(self, file_path: Path, expected_md5: str) -> bool:
        """Verifica la integridad de un archivo contra MD5 esperado"""
        actual_md5 = self.calculate_md5(file_path)
        return actual_md5.lower() == expected_md5.lower()
    
    def save_checksums(self, scene_id: str, md5: str, sha256: str):
        """Guarda checksums para un scene_id específico"""
        checksum_file = self.checksum_dir / f"{scene_id}.json"
        data = {
            'scene_id': scene_id,
            'md5': md5,
            'sha256': sha256,
            'timestamp': datetime.now().isoformat()
        }
        with open(checksum_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Checksums guardados: {scene_id}")


class RawDataEnvironment:
    """Gestor principal del entorno de datos satelitales crudos"""
    
    def __init__(self):
        self.config = DirectoryConfig()
        self.catalog = CatalogManager(self.config.CATALOG_FILE)
        self.checksums = ChecksumManager(self.config.CHECKSUMS_DIR)
        self._setup_logging()
    
    def _setup_logging(self):
        """Configura logging a archivo"""
        log_file = self.config.LOGS_DIR / f"setup_{datetime.now().strftime('%Y%m%d')}.log"
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    
    def initialize(self) -> bool:
        """Inicializa la estructura completa de directorios"""
        logger.info("=" * 60)
        logger.info("INICIALIZANDO ENTORNO DE DATOS SATELITALES CRUDOS")
        logger.info("=" * 60)
        logger.info(f"Proyecto: {self.config.PROJECT_ROOT}")
        logger.info(f"Directorio base: {self.config.DATA_RAW}")
        
        created = []
        for directory in self.config.ALL_DIRECTORIES:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                created.append(str(directory))
                logger.info(f"  [OK] {directory.relative_to(self.config.PROJECT_ROOT)}")
            except Exception as e:
                logger.error(f"  [FAIL] {directory}: {e}")
                return False
        
        logger.info(f"\n{len(created)} directorios creados/verificados")
        
        self._create_readme()
        self._create_gitkeep()
        
        logger.info("=" * 60)
        logger.info("INICIALIZACIÓN COMPLETADA")
        logger.info("=" * 60)
        
        return True
    
    def _create_readme(self):
        """Crea archivo README en el directorio raíz de datos"""
        readme_content = """# Directorio de Datos Satelitales Crudos

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
"""
        readme_path = self.config.DATA_RAW / 'README.md'
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        logger.info(f"README creado: {readme_path}")
    
    def _create_gitkeep(self):
        """Crea archivos .gitkeep en directorios vacíos"""
        for directory in self.config.ALL_DIRECTORIES:
            gitkeep = directory / '.gitkeep'
            if not gitkeep.exists():
                gitkeep.touch()
    
    def get_status(self) -> Dict:
        """Obtiene el estado actual del entorno"""
        status = {
            'initialized': self.config.DATA_RAW.exists(),
            'directories': {},
            'stats': self.catalog.get_stats(),
            'disk_usage': self._get_disk_usage()
        }
        
        for name, path in self.config.SENSOR_PATHS.items():
            status['directories'][name] = {
                'path': str(path),
                'exists': path.exists(),
                'subdirs': len(list(path.rglob('*'))) if path.exists() else 0
            }
        
        return status
    
    def _get_disk_usage(self) -> Dict:
        """Obtiene uso de disco"""
        try:
            import shutil
            usage = shutil.disk_usage(self.config.DATA_RAW)
            return {
                'total_bytes': usage.total,
                'used_bytes': usage.used,
                'free_bytes': usage.free,
                'percent_used': round((usage.used / usage.total) * 100, 2)
            }
        except Exception:
            return {'error': 'No se pudo obtener información de disco'}
    
    def print_status(self):
        """Imprime el estado del entorno"""
        status = self.get_status()
        
        print("\n" + "=" * 60)
        print("ESTADO DEL ENTORNO DE DATOS SATELITALES")
        print("=" * 60)
        
        print(f"\nInicializado: {'Si' if status['initialized'] else 'No'}")
        print(f"Directorio base: {self.config.DATA_RAW}")
        
        print("\n--- Directorios ---")
        for name, info in status['directories'].items():
            icon = "[OK]" if info['exists'] else "[--]"
            print(f"  {icon} {name}: {info['subdirs']} elementos")
        
        print("\n--- Catálogo ---")
        stats = status['stats']
        print(f"  Total entradas: {stats['total_entries']}")
        print(f"  Por sensor:")
        for sensor, count in stats['by_sensor'].items():
            print(f"    - {sensor}: {count}")
        print(f"  Por estado:")
        for status_name, count in stats['by_status'].items():
            print(f"    - {status_name}: {count}")
        
        print("\n--- Uso de Disco ---")
        usage = status['disk_usage']
        if 'error' not in usage:
            total_gb = usage['total_bytes'] / (1024**3)
            used_gb = usage['used_bytes'] / (1024**3)
            free_gb = usage['free_bytes'] / (1024**3)
            print(f"  Total: {total_gb:.1f} GB")
            print(f"  Usado: {used_gb:.1f} GB ({usage['percent_used']}%)")
            print(f"  Libre: {free_gb:.1f} GB")
            
            if usage['percent_used'] > 80:
                print("  [ALERTA] Uso de disco superior al 80%")
        else:
            print(f"  {usage['error']}")
        
        print("=" * 60)
    
    def cleanup(self, confirm: bool = False):
        """Limpia archivos temporales y logs antiguos"""
        if not confirm:
            response = input("¿Está seguro de que desea limpiar el entorno? (yes/no): ")
            if response.lower() != 'yes':
                print("Operación cancelada")
                return
        
        logger.info("Iniciando limpieza...")
        
        for log_file in self.config.LOGS_DIR.glob('*.log'):
            if log_file.stat().st_mtime < (datetime.now().timestamp() - 30 * 86400):
                log_file.unlink()
                logger.info(f"  Eliminado: {log_file.name}")
        
        print("Limpieza completada")


def main():
    parser = argparse.ArgumentParser(description='Gestión del entorno de datos satelitales crudos')
    parser.add_argument('--init', action='store_true', help='Inicializar estructura de directorios')
    parser.add_argument('--status', action='store_true', help='Mostrar estado del entorno')
    parser.add_argument('--cleanup', action='store_true', help='Limpiar archivos temporales')
    parser.add_argument('--stats', action='store_true', help='Mostrar estadísticas del catálogo')
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    env = RawDataEnvironment()
    
    if args.init:
        env.initialize()
    
    if args.status:
        env.print_status()
    
    if args.stats:
        stats = env.catalog.get_stats()
        print(json.dumps(stats, indent=2))
    
    if args.cleanup:
        env.cleanup()


if __name__ == '__main__':
    main()
