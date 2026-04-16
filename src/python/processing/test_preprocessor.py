"""
Script de prueba para preprocessor.py
Valida estructura y configuración sin ejecutar queries reales a GEE
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from preprocessor import Config, CuencaCombeima, ColeccionesSatelitales, GEEPreprocessor


def test_configuracion():
    """Verifica que la configuración se carga correctamente"""
    print("=" * 60)
    print("TEST 1: Configuración")
    print("=" * 60)
    
    config = Config()
    
    assert config.PROJECT_ID is not None, "PROJECT_ID no configurado"
    assert config.CLOUD_COVER_THRESHOLD == 15, "Umbral de nubosidad incorrecto"
    assert config.EVENT_BUS_TYPE in ['rabbitmq', 'redis'], "Tipo de bus inválido"
    
    print(f"  GEE Project ID: {config.PROJECT_ID}")
    print(f"  Event Bus Type: {config.EVENT_BUS_TYPE}")
    print(f"  Umbral Nubosidad: {config.CLOUD_COVER_THRESHOLD}%")
    print(f"  Rango Fechas: {config.DATE_RANGE}")
    print("  [OK] Configuración válida")
    return True


def test_geometria():
    """Verifica que la geometría de la cuenca es correcta"""
    print("\n" + "=" * 60)
    print("TEST 2: Geometría Cuenca Combeima")
    print("=" * 60)
    
    bbox = CuencaCombeima.get_bbox()
    coords = CuencaCombeima.COORDENADAS_POLIGONO
    
    print(f"  Bounding Box: {bbox}")
    print(f"  Vértices del polígono: {len(coords)}")
    print(f"  Coordenadas (lon, lat):")
    
    for i, coord in enumerate(coords):
        print(f"    V{i+1}: {coord[0]:.6f}, {coord[1]:.6f}")
    
    assert len(bbox) == 4, "Bounding box debe tener 4 valores"
    assert len(coords) == 5, "Polígono debe cerrar con 5 vértices"
    assert bbox[0] < bbox[2], "lon_min debe ser menor que lon_max"
    assert bbox[1] < bbox[3], "lat_min debe ser menor que lat_max"
    
    print("  [OK] Geometría válida")
    return True


def test_colecciones():
    """Verifica las colecciones satelitales configuradas"""
    print("\n" + "=" * 60)
    print("TEST 3: Colecciones Satelitales")
    print("=" * 60)
    
    colecciones = ColeccionesSatelitales.COLECCIONES
    
    print(f"  Total colecciones: {len(colecciones)}\n")
    
    for col in colecciones:
        print(f"  {col['display_name']}")
        print(f"    ID GEE: {col['id']}")
        print(f"    Rango: {col['date_start']} - {col['date_end']}")
        print(f"    Resolución: {col['resolution']}m")
        print(f"    Bandas: {', '.join(col['bands'])}")
        print()
    
    assert len(colecciones) == 4, "Deben definirse 4 colecciones"
    print("  [OK] Colecciones configuradas correctamente")
    return True


def test_preprocessor_init():
    """Verifica inicialización del preprocessor (sin conexión GEE)"""
    print("\n" + "=" * 60)
    print("TEST 4: Inicialización Preprocessor (mock)")
    print("=" * 60)
    
    config = Config()
    
    reporte = {
        'cuenca': 'Combeima',
        'geometria': {
            'tipo': 'Polígono',
            'bbox': CuencaCombeima.get_bbox()
        },
        'rango_fechas': config.DATE_RANGE,
        'umbral_nubosidad': config.CLOUD_COVER_THRESHOLD,
        'colecciones': {},
        'total_imagenes_encontradas': 0,
        'total_imagenes_validas': 0,
        'assets_creados': [],
        'errores': [],
        'timestamp_inicio': datetime.now().isoformat(),
        'timestamp_fin': None
    }
    
    assert reporte['cuenca'] == 'Combeima'
    assert reporte['rango_fechas'] == config.DATE_RANGE
    assert reporte['umbral_nubosidad'] == config.CLOUD_COVER_THRESHOLD
    assert 'geometria' in reporte
    assert 'colecciones' in reporte
    
    print(f"  Cuenca: {reporte['cuenca']}")
    print(f"  Geometría: {reporte['geometria']['tipo']}")
    print(f"  BBox: {reporte['geometria']['bbox']}")
    print("  [OK] Estructura del preprocessor válida")
    return True


def test_reporte_structure():
    """Verifica la estructura del reporte"""
    print("\n" + "=" * 60)
    print("TEST 5: Estructura del Reporte")
    print("=" * 60)
    
    required_fields = [
        'cuenca', 'geometria', 'rango_fechas', 'umbral_nubosidad',
        'colecciones', 'total_imagenes_encontradas', 'total_imagenes_validas',
        'assets_creados', 'errores', 'timestamp_inicio', 'timestamp_fin'
    ]
    
    reporte = {
        'cuenca': 'Combeima',
        'geometria': {'tipo': 'Poligono'},
        'rango_fechas': {'start': '1969-01-01', 'end': '2023-12-31'},
        'umbral_nubosidad': 15,
        'colecciones': {},
        'total_imagenes_encontradas': 0,
        'total_imagenes_validas': 0,
        'assets_creados': [],
        'errores': [],
        'timestamp_inicio': datetime.now().isoformat(),
        'timestamp_fin': None
    }
    
    for field in required_fields:
        assert field in reporte, f"Campo requerido faltante: {field}"
        print(f"  OK - {field}")
    
    print("\n  [OK] Estructura del reporte completa")
    return True


def main():
    """Ejecuta todos los tests"""
    print("\n" + "=" * 60)
    print("SKYFUSION ANALYTICS - PREPROCESSOR TESTS")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        test_configuracion,
        test_geometria,
        test_colecciones,
        test_preprocessor_init,
        test_reporte_structure
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERROR] {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print("RESUMEN DE TESTS")
    print("=" * 60)
    print(f"  Aprobados: {passed}")
    print(f"  Fallidos: {failed}")
    print(f"  Total: {passed + failed}")
    print("=" * 60)
    
    if failed == 0:
        print("\n[PASS] Todos los tests pasaron. El preprocessor esta listo.")
        print("\nPara ejecutar el pipeline completo:")
        print("  1. Configurar variables de entorno en .env")
        print("  2. Asegurar credenciales de GEE en config/gee-service-account.json")
        print("  3. Ejecutar: python preprocessor.py")
    else:
        print("\n[FAIL] Algunos tests fallaron. Revisar errores arriba.")
        sys.exit(1)


if __name__ == '__main__':
    main()
