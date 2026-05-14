"""
Demo Completa: Clasificación y Alteraciones Morfológicas
==========================================================
Skyfusion Analytics - Demo de Procesamiento Morfológico

Este script demuestra todas las funcionalidades implementadas:
1. Operaciones morfológicas básicas y avanzadas
2. Segmentación y watershed
3. Extracción de características morfológicas
4. Clasificación de cobertura de suelo
5. Detección de cambios temporales
6. Procesamiento escalable para imágenes grandes

Uso: python demo_morphological.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import cv2
import json
from datetime import datetime

# Importar módulos
try:
    from morphological_processor import (
        MorphologicalProcessor,
        MorphologicalKernelType,
        MorphologicalOperation,
        create_test_image
    )
    from indices_processor import EnvironmentalIndexProcessor
    from classification_processor import (
        LandCoverClassifier,
        ChangeDetectionClassifier,
        ClassificationConfig
    )
except ImportError as e:
    print(f"Error al importar módulos: {e}")
    print("Asegúrate de ejecutar desde el directorio src/python/processing/")
    sys.exit(1)


def demo_basic_operations():
    """Demo 1: Operaciones morfológicas básicas."""
    print("\n" + "=" * 60)
    print("DEMO 1: OPERACIONES MORFOLOGICAS BASICAS")
    print("=" * 60)
    
    proc = MorphologicalProcessor()
    img = create_test_image(256, 256)
    
    print(f"\nImagen original: {img.shape}, mean={np.mean(img):.2f}")
    
    # Erosión
    eroded = proc.erode(img, kernel_size=5)
    print(f"Erosion (k=5): mean={np.mean(eroded):.2f} - reduce objetos brillantes")
    
    # Dilatación
    dilated = proc.dilate(img, kernel_size=5)
    print(f"Dilatacion (k=5): mean={np.mean(dilated):.2f} - expande objetos brillantes")
    
    # Apertura
    opened = proc.open(img, kernel_size=5)
    print(f"Apertura (k=5): mean={np.mean(opened):.2f} - elimina ruido blanco")
    
    # Cierre
    closed = proc.close(img, kernel_size=5)
    print(f"Cierre (k=5): mean={np.mean(closed):.2f} - llena huecos")
    
    print("\n[OK] Demo 1 completada")


def demo_advanced_operations():
    """Demo 2: Operaciones morfológicas avanzadas."""
    print("\n" + "=" * 60)
    print("DEMO 2: OPERACIONES AVANZADAS")
    print("=" * 60)
    
    proc = MorphologicalProcessor()
    img = create_test_image(256, 256)
    
    # Gradiente morfológico (detecta bordes)
    gradient = proc.morphological_gradient(img, kernel_size=5)
    print(f"\nGradiente Morfologico: mean={np.mean(gradient):.2f}")
    print("  - Detecta bordes de objetos (dilatacion - erosion)")
    
    # Top-Hat (extrae objetos brillantes pequeños)
    tophat = proc.top_hat(img, kernel_size=15)
    print(f"Top-Hat (k=15): mean={np.mean(tophat):.2f}")
    print("  - Extrae objetos brillantes pequenos (imagen - apertura)")
    
    # Black-Hat (extrae objetos oscuros pequeños)
    blackhat = proc.black_hat(img, kernel_size=15)
    print(f"Black-Hat (k=15): mean={np.mean(blackhat):.2f}")
    print("  - Extrae objetos oscuros pequenos (cierre - imagen)")
    
    # Reconstrucción morfológica
    opened_rec = proc.opening_by_reconstruction(img, kernel_size=7)
    print(f"Opening by Rec (k=7): mean={np.mean(opened_rec):.2f}")
    print("  - Preserva formas mejor que apertura estandar")
    
    closed_rec = proc.closing_by_reconstruction(img, kernel_size=7)
    print(f"Closing by Rec (k=7): mean={np.mean(closed_rec):.2f}")
    print("  - Preserva formas mejor que cierre estandar")
    
    # Esqueletización
    line_img = np.zeros((128, 128), dtype=np.uint8)
    cv2.line(line_img, (20, 20), (100, 100), 255, 8)
    skeleton = proc.skeletonize(line_img, method='morphological')
    print(f"\nEsqueletizacion: {np.sum(skeleton > 0)} pixeles en esqueleto")
    print("  - Reduce objetos a su estructura lineal central")
    
    print("\n[OK] Demo 2 completada")


def demo_watershed():
    """Demo 3: Segmentación Watershed."""
    print("\n" + "=" * 60)
    print("DEMO 3: SEGMENTACION WATERSHED")
    print("=" * 60)
    
    proc = MorphologicalProcessor()
    
    # Crear imagen con objetos que se tocan
    img = np.zeros((256, 256, 3), dtype=np.uint8)
    cv2.circle(img, (100, 100), 50, (200, 200, 200), -1)
    cv2.circle(img, (150, 130), 45, (180, 180, 180), -1)
    cv2.circle(img, (80, 160), 40, (160, 160, 160), -1)
    
    # Segmentar con watershed
    result = proc.watershed_segmentation(img, use_threshold_marker=True)
    
    print(f"\nSegmentos encontrados: {result.num_segments}")
    print(f"Pixeles en bordes: {np.sum(result.boundary_mask > 0)}")
    
    for label, props in list(result.segment_properties.items())[:5]:
        print(f"  Segmento {label}: area={props['area']}, "
              f"centro=({props['centroid_x']:.0f}, {props['centroid_y']:.0f})")
    
    print("\n[OK] Demo 3 completada")


def demo_feature_extraction():
    """Demo 4: Extracción de características morfológicas."""
    print("\n" + "=" * 60)
    print("DEMO 4: EXTRACCION DE CARACTERISTICAS")
    print("=" * 60)
    
    proc = MorphologicalProcessor()
    
    # Crear formas geométricas
    circle_img = np.zeros((200, 200), dtype=np.uint8)
    cv2.circle(circle_img, (100, 100), 60, 255, -1)
    
    rect_img = np.zeros((200, 200), dtype=np.uint8)
    cv2.rectangle(rect_img, (40, 40), (160, 160), 255, -1)
    
    # Extraer características
    circle_feat = proc.extract_features(circle_img)
    rect_feat = proc.extract_features(rect_img)
    
    print("\nComparacion de caracteristicas:")
    print(f"{'Caracteristica':<25} {'Circulo':<12} {'Rectangulo':<12}")
    print("-" * 49)
    print(f"{'Area':<25} {circle_feat.area:<12.0f} {rect_feat.area:<12.0f}")
    print(f"{'Perimetro':<25} {circle_feat.perimeter:<12.1f} {rect_feat.perimeter:<12.1f}")
    print(f"{'Compacidad':<25} {circle_feat.compactness:<12.4f} {rect_feat.compactness:<12.4f}")
    print(f"{'Circularidad':<25} {circle_feat.circularity:<12.4f} {rect_feat.circularity:<12.4f}")
    print(f"{'Rectangularidad':<25} {circle_feat.rectangularity:<12.4f} {rect_feat.rectangularity:<12.4f}")
    print(f"{'Solididad':<25} {circle_feat.solidity:<12.4f} {rect_feat.solidity:<12.4f}")
    
    print("\n[OK] Demo 4 completada")


def demo_classification():
    """Demo 5: Clasificación de cobertura de suelo."""
    print("\n" + "=" * 60)
    print("DEMO 5: CLASIFICACION DE COBERTURA")
    print("=" * 60)
    
    classifier = LandCoverClassifier()
    
    # Crear datos simulados de Landsat
    print("\nSimulando bandas satelitales Landsat...")
    np.random.seed(42)
    h, w = 256, 256
    
    # Patrones: agua (valores altos en green, bajos en NIR)
    #           vegetacion (altos en NIR, bajos en red)
    y, x = np.ogrid[:h, :w]
    
    nir = np.random.uniform(1000, 4000, (h, w)).astype(np.float32)
    red = np.random.uniform(500, 2500, (h, w)).astype(np.float32)
    green = np.random.uniform(800, 3000, (h, w)).astype(np.float32)
    
    # Zona de agua
    nir[200:240, 200:240] = 800
    green[200:240, 200:240] = 3500
    
    # Zona de vegetación densa
    nir[50:100, 50:100] = 3800
    red[50:100, 50:100] = 600
    
    print("Clasificando cobertura de suelo...")
    result = classifier.classify(nir, red, green)
    
    print(f"\nResultados de clasificacion:")
    print(f"{'Clase':<25} {'Area (px)':<12} {'%'} ")
    print("-" * 40)
    for class_name in ['agua', 'vegetacion_densa', 'vegetacion_moderada',
                       'vegetacion_escasa', 'suelo_desnudo', 'area_urbana', 'otro']:
        area = result.class_areas.get(class_name, 0)
        pct = result.class_percentages.get(class_name, 0)
        if area > 0:
            bar = '#' * int(pct / 2)
            print(f"{class_name:<25} {area:<12} {pct:5.1f}% {bar}")
    
    # Crear visualización
    viz = classifier.create_visualization(result)
    print(f"\nVisualizacion creada: {viz.shape}")
    
    print("\n[OK] Demo 5 completada")


def demo_change_detection():
    """Demo 6: Detección de cambios temporales."""
    print("\n" + "=" * 60)
    print("DEMO 6: DETECCION DE CAMBIOS TEMPORALES")
    print("=" * 60)
    
    index_proc = EnvironmentalIndexProcessor()
    change_detector = ChangeDetectionClassifier()
    
    # Crear datos "antes" y "después"
    np.random.seed(42)
    h, w = 128, 128
    
    nir_before = np.random.uniform(1000, 4000, (h, w)).astype(np.float32)
    red_before = np.random.uniform(500, 2500, (h, w)).astype(np.float32)
    green_before = np.random.uniform(800, 3000, (h, w)).astype(np.float32)
    
    # Simular deforestación en una zona
    nir_after = nir_before.copy()
    red_after = red_before.copy()
    green_after = green_before.copy()
    
    # Zona deforestada: NIR baja, Red sube
    nir_after[30:60, 30:60] = 1500
    red_after[30:60, 30:60] = 2000
    
    # Detectar cambios de vegetación
    print("\nDetectando cambios de vegetacion...")
    ndvi_before = index_proc.calculate_ndvi(nir_before, red_before)
    ndvi_after = index_proc.calculate_ndvi(nir_after, red_after)
    
    change_result = index_proc.detect_vegetation_change_morphological(
        ndvi_before, ndvi_after, threshold=0.15
    )
    
    print(f"Vegetacion perdida: {change_result.get('vegetation_loss', 0):.0f} pixeles")
    print(f"Vegetacion ganada: {change_result.get('vegetation_gain', 0):.0f} pixeles")
    print(f"Cambio neto: {change_result.get('net_change', 0):.0f} pixeles")
    
    print("\n[OK] Demo 6 completada")


def demo_scalability():
    """Demo 7: Procesamiento escalable."""
    print("\n" + "=" * 60)
    print("DEMO 7: PROCESAMIENTO ESCALABLE")
    print("=" * 60)
    
    proc = MorphologicalProcessor()
    
    # Probar diferentes tamaños
    for size in [256, 512, 1024, 2048]:
        img = np.random.randint(0, 256, (size, size), dtype=np.uint8)
        
        import time
        start = time.time()
        result = proc.process_chunked(img, MorphologicalOperation.OPEN, 
                                      chunk_size=256, kernel_size=3)
        elapsed = time.time() - start
        
        print(f"  {size}x{size}: {elapsed:.3f}s -> {result.shape}")
    
    print("\n[OK] Demo 7 completada")


def demo_full_workflow():
    """
    Demo 8: Flujo de trabajo completo.
    
    Este demo simula un análisis completo desde la ingesta
    de datos satelitales hasta la clasificación y detección de cambios.
    """
    print("\n" + "=" * 60)
    print("DEMO 8: FLUJO DE TRABAJO COMPLETO")
    print("=" * 60)
    
    # 1. Inicializar procesadores
    morph_proc = MorphologicalProcessor()
    index_proc = EnvironmentalIndexProcessor()
    classifier = LandCoverClassifier()
    
    print("\n[Paso 1] Simulando datos satelitales...")
    np.random.seed(42)
    size = 256
    
    nir = np.random.uniform(1000, 4000, (size, size)).astype(np.float32)
    red = np.random.uniform(500, 2500, (size, size)).astype(np.float32)
    green = np.random.uniform(800, 3000, (size, size)).astype(np.float32)
    
    # 2. Calcular índices
    print("[Paso 2] Calculando indices espectrales...")
    ndvi = index_proc.calculate_ndvi(nir, red)
    ndwi = index_proc.calculate_ndwi(green, nir)
    
    print(f"  NDVI: mean={np.mean(ndvi):.3f}, std={np.std(ndvi):.3f}")
    print(f"  NDWI: mean={np.mean(ndwi):.3f}, std={np.std(ndwi):.3f}")
    
    # 3. Aplicar suavizado morfológico
    print("[Paso 3] Aplicando suavizado morfologico...")
    ndvi_smooth = index_proc.apply_morphological_smoothing(ndvi, kernel_size=5, operation='both')
    print(f"  NDVI suavizado correctamente")
    
    # 4. Clasificar
    print("[Paso 4] Clasificando cobertura de suelo...")
    result = classifier.classify(nir, red, green)
    
    for class_name in ['agua', 'vegetacion_densa', 'vegetacion_moderada', 
                       'suelo_desnudo', 'area_urbana']:
        pct = result.class_percentages.get(class_name, 0)
        if pct > 0:
            print(f"  {class_name}: {pct:.1f}%")
    
    # 5. Extraer características morfológicas
    print("[Paso 5] Extrayendo caracteristicas morfologicas...")
    features = morph_proc.extract_features((ndvi * 127.5 + 127.5).astype(np.uint8))
    print(f"  Area total: {features.area:.0f} pixeles")
    print(f"  Num. componentes: {features.num_components}")
    print(f"  Num. huecos: {features.num_holes}")
    
    # 6. Guardar resultados
    print("[Paso 6] Guardando resultados...")
    classifier.save_result(result, "demo_classification_result.npy",
                          {'timestamp': datetime.now().isoformat()})
    
    print("\n[OK] Demo 8 completada - Flujo de trabajo completo!")


def print_summary():
    """Resumen final del módulo."""
    print("\n" + "=" * 60)
    print("RESUMEN: MODULO DE PROCESAMIENTO MORFOLOGICO")
    print("=" * 60)
    
    print("""
FUNCIONALIDADES IMPLEMENTADAS:
-------------------------------
[1] Operaciones Basicas:
    - Erosion        : Reduce objetos brillantes
    - Dilatacion     : Expande objetos brillantes
    - Apertura       : Elimina ruido blanco
    - Cierre         : Llena huecos oscuros

[2] Operaciones Avanzadas:
    - Gradiente      : Detecta bordes de objetos
    - Top-Hat        : Extrae objetos brillantes pequenos
    - Black-Hat      : Extrae objetos oscuros pequenos
    - Opening by Rec : Apertura preservando formas
    - Closing by Rec : Cierre preservando formas
    - Esqueletizacion: Reduce objetos a su estructura central

[3] Segmentacion:
    - Watershed          : Separa objetos que se tocan
    - Attribute Filtering: Filtra por area, solidez, compacidad

[4] Extraccion de Caracteristicas (20+ features):
    - Area, Perimetro, Compacidad, Circularidad
    - Solididad, Elongacion, Rectangularidad
    - Euler Number, Numero de Huecos
    - Momentos de Hu (invariantes a rotacion)
    - Perfil multi-escala

[5] Clasificacion de Cobertura:
    - 7 clases: agua, vegetacion densa/moderada/escasa,
                suelo desnudo, area urbana, otro
    - Integracion con NDVI, NDWI, EVI

[6] Deteccion de Cambios:
    - Cambios en vegetacion (deforestacion)
    - Cambios en cuerpos de agua
    - Expansio urbana
    - Analisis multitemporal

[7] Escalabilidad:
    - Chunked processing para imagenes 4K+
    - Batch processing para multiples imagenes
    - Procesamiento en tiles

ARQUITECTURA:
-------------
src/python/processing/
  morphological_processor.py   -> Procesamiento morfologico puro
  indices_processor.py          -> Calculo de indices (NDVI, NDWI, EVI)
  classification_processor.py   -> Clasificacion y deteccion de cambios
""")


if __name__ == "__main__":
    print("=" * 60)
    print("SKYFUSION ANALYTICS - DEMO COMPLETA")
    print("Clasificacion y Alteraciones Morfologicas")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # Ejecutar demos
    demo_basic_operations()
    demo_advanced_operations()
    demo_watershed()
    demo_feature_extraction()
    demo_classification()
    demo_change_detection()
    demo_scalability()
    demo_full_workflow()
    
    # Resumen
    print_summary()
    print("\nDEMO COMPLETADA EXITOSAMENTE!")
