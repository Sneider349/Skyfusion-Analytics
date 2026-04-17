"""
Validador de Datos Satelitales Crudos
======================================
Skyfusion Analytics - Data Engineering

Script para verificar la integridad de archivos descargados,
detectar inconsistencias y generar reportes de calidad.

Uso:
    python validate_raw_data.py --check-all      # Validar todo
    python validate_raw_data.py --check-missing   # Buscar archivos faltantes
    python validate_raw_data.py --verify-checksums # Verificar integridad
"""

import os
import sys
import csv
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
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
    CATALOG_FILE = DATA_RAW / 'metadata' / 'catalog.csv'
    CHECKSUMS_DIR = DATA_RAW / 'metadata' / 'checksums'
    LOGS_DIR = DATA_RAW / 'metadata' / 'logs'


class ValidationReport:
    """Reporte de validación"""
    
    def __init__(self):
        self.timestamp = datetime.now().isoformat()
        self.total_checked = 0
        self.total_valid = 0
        self.total_invalid = 0
        self.total_missing = 0
        self.errors = []
        self.warnings = []
        self.details = []
    
    def add_error(self, scene_id: str, error_type: str, message: str):
        """Añade un error al reporte"""
        self.errors.append({
            'scene_id': scene_id,
            'type': error_type,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        self.total_invalid += 1
    
    def add_warning(self, scene_id: str, warning_type: str, message: str):
        """Añade una advertencia al reporte"""
        self.warnings.append({
            'scene_id': scene_id,
            'type': warning_type,
            'message': message
        })
    
    def add_detail(self, scene_id: str, field: str, value: str):
        """Añade un detalle al reporte"""
        self.details.append({
            'scene_id': scene_id,
            'field': field,
            'value': value
        })
    
    def add_valid(self):
        """Incrementa el contador de válidos"""
        self.total_valid += 1
    
    def add_missing(self):
        """Incrementa el contador de faltantes"""
        self.total_missing += 1
    
    def get_summary(self) -> Dict:
        """Obtiene el resumen del reporte"""
        return {
            'timestamp': self.timestamp,
            'summary': {
                'total_checked': self.total_checked,
                'total_valid': self.total_valid,
                'total_invalid': self.total_invalid,
                'total_missing': self.total_missing,
                'validation_rate': round(
                    (self.total_valid / self.total_checked * 100)
                    if self.total_checked > 0 else 0, 2
                )
            },
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }
    
    def save_to_file(self, output_path: Path):
        """Guarda el reporte en un archivo JSON"""
        report_data = {
            **self.get_summary(),
            'errors': self.errors[:50],
            'warnings': self.warnings[:50],
            'details': self.details[:100]
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Reporte guardado: {output_path}")


class DataValidator:
    """Validador de datos satelitales crudos"""
    
    def __init__(self):
        self.config = DirectoryConfig()
        self.report = ValidationReport()
        self._setup_logging()
    
    def _setup_logging(self):
        """Configura logging"""
        log_file = self.config.LOGS_DIR / f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    
    def _calculate_md5(self, file_path: Path) -> str:
        """Calcula hash MD5 de un archivo"""
        md5_hash = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculando MD5 de {file_path}: {e}")
            return ""
    
    def _validate_catalog_exists(self) -> bool:
        """Valida que el catálogo exista"""
        if not self.config.CATALOG_FILE.exists():
            self.report.add_error(
                'N/A', 'CATALOG_NOT_FOUND',
                f"Catálogo no encontrado: {self.config.CATALOG_FILE}"
            )
            return False
        return True
    
    def _read_catalog(self) -> List[Dict]:
        """Lee el catálogo de imágenes"""
        entries = []
        if not self._validate_catalog_exists():
            return entries
        
        try:
            with open(self.config.CATALOG_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                entries = list(reader)
            logger.info(f"Catálogo leído: {len(entries)} entradas")
        except Exception as e:
            logger.error(f"Error leyendo catálogo: {e}")
        
        return entries
    
    def check_file_exists(self, entry: Dict) -> bool:
        """Verifica que el archivo físico exista"""
        local_path = entry.get('local_path', '')
        if not local_path:
            self.report.add_error(
                entry.get('scene_id', 'unknown'),
                'MISSING_PATH',
                'Ruta local no especificada en catálogo'
            )
            return False
        
        file_path = Path(local_path)
        if not file_path.is_absolute():
            file_path = self.config.DATA_RAW / local_path
        
        if not file_path.exists():
            self.report.add_missing()
            self.report.add_error(
                entry.get('scene_id', 'unknown'),
                'FILE_MISSING',
                f"Archivo no encontrado: {local_path}"
            )
            return False
        
        return True
    
    def verify_checksum(self, entry: Dict) -> bool:
        """Verifica el checksum MD5 del archivo"""
        scene_id = entry.get('scene_id', 'unknown')
        local_path = entry.get('local_path', '')
        expected_md5 = entry.get('checksum_md5', '')
        
        if not local_path:
            return False
        
        file_path = Path(local_path)
        if not file_path.is_absolute():
            file_path = self.config.DATA_RAW / local_path
        
        if not file_path.exists():
            return False
        
        if not expected_md5:
            self.report.add_warning(
                scene_id, 'NO_CHECKSUM',
                'Checksum MD5 no registrado en catálogo'
            )
            return True
        
        actual_md5 = self._calculate_md5(file_path)
        
        if actual_md5.lower() != expected_md5.lower():
            self.report.add_error(
                scene_id, 'CHECKSUM_MISMATCH',
                f"Checksum no coincide. Esperado: {expected_md5}, Actual: {actual_md5}"
            )
            return False
        
        return True
    
    def check_file_size(self, entry: Dict) -> bool:
        """Verifica que el tamaño del archivo sea válido"""
        local_path = entry.get('local_path', '')
        expected_size = entry.get('file_size_bytes', '0')
        
        if not local_path or not expected_size.isdigit():
            return True
        
        file_path = Path(local_path)
        if not file_path.is_absolute():
            file_path = self.config.DATA_RAW / local_path
        
        if not file_path.exists():
            return False
        
        actual_size = file_path.stat().st_size
        expected = int(expected_size)
        
        if actual_size == 0:
            self.report.add_error(
                entry.get('scene_id', 'unknown'),
                'EMPTY_FILE',
                f"Archivo vacío: {local_path}"
            )
            return False
        
        size_diff_percent = abs(actual_size - expected) / expected * 100 if expected > 0 else 0
        if size_diff_percent > 1:
            self.report.add_warning(
                entry.get('scene_id', 'unknown'),
                'SIZE_MISMATCH',
                f"Tamaño difiere en {size_diff_percent:.2f}%"
            )
        
        return True
    
    def check_cloud_cover(self, entry: Dict) -> bool:
        """Verifica que el valor de nubosidad sea válido"""
        scene_id = entry.get('scene_id', 'unknown')
        cloud_cover = entry.get('cloud_cover', '')
        
        if not cloud_cover:
            self.report.add_warning(scene_id, 'NO_CLOUD_DATA', 'Nubosidad no registrada')
            return True
        
        try:
            cc_value = float(cloud_cover)
            if cc_value < 0 or cc_value > 100:
                self.report.add_error(
                    scene_id, 'INVALID_CLOUD_COVER',
                    f"Valor de nubosidad inválido: {cc_value}"
                )
                return False
            return True
        except ValueError:
            self.report.add_error(
                scene_id, 'CLOUD_COVER_FORMAT',
                f"Formato de nubosidad inválido: {cloud_cover}"
            )
            return False
    
    def validate_entry(self, entry: Dict) -> bool:
        """Valida una entrada completa del catálogo"""
        scene_id = entry.get('scene_id', 'unknown')
        self.report.total_checked += 1
        
        is_valid = True
        
        if not self.check_file_exists(entry):
            is_valid = False
        
        if is_valid:
            if not self.verify_checksum(entry):
                is_valid = False
            
            if not self.check_file_size(entry):
                is_valid = False
        
        if not self.check_cloud_cover(entry):
            is_valid = False
        
        if is_valid:
            self.report.add_valid()
        
        return is_valid
    
    def check_all(self) -> ValidationReport:
        """Ejecuta todas las validaciones"""
        logger.info("=" * 60)
        logger.info("INICIANDO VALIDACIÓN COMPLETA")
        logger.info("=" * 60)
        
        entries = self._read_catalog()
        
        if not entries:
            logger.warning("No hay entradas en el catálogo para validar")
            return self.report
        
        for entry in entries:
            self.validate_entry(entry)
        
        logger.info("=" * 60)
        logger.info("VALIDACIÓN COMPLETADA")
        logger.info("=" * 60)
        
        return self.report
    
    def check_missing_files(self) -> ValidationReport:
        """Busca archivos faltantes"""
        logger.info("=" * 60)
        logger.info("BUSCANDO ARCHIVOS FALTANTES")
        logger.info("=" * 60)
        
        entries = self._read_catalog()
        
        for entry in entries:
            local_path = entry.get('local_path', '')
            if local_path:
                file_path = Path(local_path)
                if not file_path.is_absolute():
                    file_path = self.config.DATA_RAW / local_path
                
                if not file_path.exists():
                    self.report.total_checked += 1
                    self.report.add_missing()
                    self.report.add_error(
                        entry.get('scene_id', 'unknown'),
                        'FILE_MISSING',
                        f"Archivo no encontrado: {local_path}"
                    )
        
        return self.report
    
    def verify_all_checksums(self) -> ValidationReport:
        """Verifica todos los checksums"""
        logger.info("=" * 60)
        logger.info("VERIFICANDO CHECKSUMS")
        logger.info("=" * 60)
        
        entries = self._read_catalog()
        
        for entry in entries:
            local_path = entry.get('local_path', '')
            if local_path:
                self.report.total_checked += 1
                if not self.verify_checksum(entry):
                    pass
        
        return self.report
    
    def print_summary(self):
        """Imprime el resumen de validación"""
        summary = self.report.get_summary()
        
        print("\n" + "=" * 60)
        print("RESUMEN DE VALIDACIÓN")
        print("=" * 60)
        print(f"Total verificados: {summary['summary']['total_checked']}")
        print(f"Válidos: {summary['summary']['total_valid']}")
        print(f"Inválidos: {summary['summary']['total_invalid']}")
        print(f"Faltantes: {summary['summary']['total_missing']}")
        print(f"Tasa de validación: {summary['summary']['validation_rate']}%")
        print(f"Errores: {summary['error_count']}")
        print(f"Advertencias: {summary['warning_count']}")
        print("=" * 60)
        
        if self.report.errors:
            print("\nPRIMEROS 5 ERRORES:")
            for error in self.report.errors[:5]:
                print(f"  - {error['scene_id']}: {error['message']}")
        
        if self.report.warnings:
            print("\nPRIMERAS 5 ADVERTENCIAS:")
            for warning in self.report.warnings[:5]:
                print(f"  - {warning['scene_id']}: {warning['message']}")
        
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Validador de datos satelitales crudos')
    parser.add_argument('--check-all', action='store_true', help='Validar todo')
    parser.add_argument('--check-missing', action='store_true', help='Buscar archivos faltantes')
    parser.add_argument('--verify-checksums', action='store_true', help='Verificar checksums')
    parser.add_argument('--output', type=str, help='Archivo de salida del reporte JSON')
    
    args = parser.parse_args()
    
    if not any([args.check_all, args.check_missing, args.verify_checksums]):
        parser.print_help()
        return
    
    validator = DataValidator()
    
    if args.check_all:
        validator.check_all()
    
    if args.check_missing:
        validator.check_missing_files()
    
    if args.verify_checksums:
        validator.verify_all_checksums()
    
    validator.print_summary()
    
    if args.output:
        validator.report.save_to_file(Path(args.output))
    
    sys.exit(0 if validator.report.total_invalid == 0 else 1)


if __name__ == '__main__':
    main()
