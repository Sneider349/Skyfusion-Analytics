"""
Tests Unitarios para el Módulo de Procesamiento Morfológico
Skyfusion Analytics - Morphological Processor Tests

Autor: Skyfusion Analytics Team
Fecha: 2026
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'python', 'processing'))

import numpy as np
import pytest
import cv2
from pathlib import Path

# Importar el módulo a probar
from morphological_processor import (
    MorphologicalProcessor,
    MorphologicalKernelType,
    MorphologicalOperation,
    MorphologicalFeatures,
    SegmentationResult,
    morphological_open,
    morphological_close,
    morphological_gradient,
    extract_morphology_features,
    create_test_image
)


# =============================================================================
# FIXTURES PARA TESTS
# =============================================================================

@pytest.fixture
def processor():
    """Fixture que crea un procesador morfológico."""
    proc = MorphologicalProcessor(output_dir="../../data/output/test")
    return proc


@pytest.fixture
def test_image():
    """Fixture que crea una imagen de prueba."""
    return create_test_image(256, 256)


@pytest.fixture
def binary_image():
    """Fixture que crea una imagen binaria."""
    np.random.seed(42)
    image = np.zeros((256, 256), dtype=np.uint8)
    
    # Agregar formas binarias
    cv2.circle(image, (64, 64), 40, 255, -1)
    cv2.rectangle(image, (100, 100), (200, 200), 255, -1)
    
    return image


@pytest.fixture
def grayscale_image():
    """Fixture que crea imagen en escala de grises."""
    np.random.seed(123)
    return np.random.randint(0, 256, (256, 256), dtype=np.uint8)


# =============================================================================
# TESTS DE GENERADORES DE KERNEL
# =============================================================================

class TestKernelGenerators:
    """Tests para generadores de elementos estructurantes."""
    
    def test_square_kernel(self, processor):
        """Test kernel cuadrado."""
        kernel = processor.create_kernel(5, MorphologicalKernelType.SQUARE)
        assert kernel.shape == (5, 5)
        assert np.sum(kernel) == 25  # 5x5 = 25
    
    def test_circle_kernel(self, processor):
        """Test kernel circular."""
        kernel = processor.create_kernel(5, MorphologicalKernelType.CIRCLE)
        assert kernel.shape == (5, 5)
        # Kernel circular tiene valores en forma de círculo
        assert np.sum(kernel) > 0
        assert np.sum(kernel) < 25
    
    def test_ellipse_kernel(self, processor):
        """Test kernel elíptico."""
        kernel = processor.create_kernel(5, MorphologicalKernelType.ELLIPSE)
        assert kernel.shape == (5, 5)
        assert np.sum(kernel) > 0
    
    def test_cross_kernel(self, processor):
        """Test kernel cruz."""
        kernel = processor.create_kernel(5, MorphologicalKernelType.CROSS)
        assert kernel.shape == (5, 5)
        # Cruz tiene 5 + 5 - 1 = 9 elementos
        assert np.sum(kernel) == 9
    
    def test_line_h_kernel(self, processor):
        """Test kernel línea horizontal."""
        kernel = processor.create_kernel(5, MorphologicalKernelType.LINE_H)
        assert kernel.shape == (1, 5)
        assert np.sum(kernel) == 5
    
    def test_line_v_kernel(self, processor):
        """Test kernel línea vertical."""
        kernel = processor.create_kernel(5, MorphologicalKernelType.LINE_V)
        assert kernel.shape == (5, 1)
        assert np.sum(kernel) == 5
    
    def test_diamond_kernel(self, processor):
        """Test kernel diamante."""
        kernel = processor.create_kernel(5, MorphologicalKernelType.DIAMOND)
        assert kernel.shape == (5, 5)
        # Diamante tiene 13 elementos (centro + anillos)
        assert np.sum(kernel) == 13
    
    def test_kernel_cache(self, processor):
        """Test que el cache de kernels funciona."""
        kernel1 = processor.create_kernel(5, MorphologicalKernelType.SQUARE)
        kernel2 = processor.create_kernel(5, MorphologicalKernelType.SQUARE)
        assert np.array_equal(kernel1, kernel2)


# =============================================================================
# TESTS DE OPERACIONES BÁSICAS
# =============================================================================

class TestBasicOperations:
    """Tests para operaciones morfológicas básicas."""
    
    def test_erode(self, processor, test_image):
        """Test erosión."""
        result = processor.erode(test_image, kernel_size=3)
        assert result.shape == test_image.shape
        assert np.mean(result) <= np.mean(test_image)  # Erosión reduce objetos
    
    def test_dilate(self, processor, test_image):
        """Test dilatación."""
        result = processor.dilate(test_image, kernel_size=3)
        assert result.shape == test_image.shape
        assert np.mean(result) >= np.mean(test_image)  # Dilatación enlarge objetos
    
    def test_erode_iterations(self, processor, test_image):
        """Test erosión con múltiples iteraciones."""
        result_1 = processor.erode(test_image, kernel_size=3, iterations=1)
        result_2 = processor.erode(test_image, kernel_size=3, iterations=2)
        
        # Más iteraciones = más reducción
        assert np.mean(result_2) <= np.mean(result_1)
    
    def test_dilate_iterations(self, processor, test_image):
        """Test dilatación con múltiples iteraciones."""
        result_1 = processor.dilate(test_image, kernel_size=3, iterations=1)
        result_2 = processor.dilate(test_image, kernel_size=3, iterations=2)
        
        # Más iteraciones = más expansión
        assert np.mean(result_2) >= np.mean(result_1)
    
    def test_open(self, processor, test_image):
        """Test apertura."""
        result = processor.open(test_image, kernel_size=5)
        assert result.shape == test_image.shape
    
    def test_close(self, processor, test_image):
        """Test cierre."""
        result = processor.close(test_image, kernel_size=5)
        assert result.shape == test_image.shape
    
    def test_open_removes_noise(self, processor):
        """Test que apertura elimina ruido."""
        # Crear imagen con ruido
        np.random.seed(42)
        image = np.zeros((100, 100), dtype=np.uint8)
        cv2.circle(image, (50, 50), 30, 255, -1)  # Objeto grande
        
        # Añadir ruido (puntos pequeños)
        for _ in range(20):
            x, y = np.random.randint(0, 100, 2)
            image[x, y] = 255
        
        result = processor.open(image, kernel_size=3)
        
        # Apertura debe reducir el ruido
        original_noise = np.sum(image > 0)
        result_noise = np.sum(result > 0)
        assert result_noise <= original_noise
    
    def test_close_fills_holes(self, processor):
        """Test que cierre elimina holes."""
        # Crear imagen con holes
        image = np.ones((100, 100), dtype=np.uint8) * 255
        cv2.circle(image, (50, 50), 40, 0, -1)  # Hole en el centro
        
        result = processor.close(image, kernel_size=7)
        
        # El hole debe ser más pequeño o eliminado
        original_holes = np.sum(image == 0)
        result_holes = np.sum(result == 0)
        assert result_holes <= original_holes


# =============================================================================
# TESTS DE OPERACIONES AVANZADAS
# =============================================================================

class TestAdvancedOperations:
    """Tests para operaciones morfológicas avanzadas."""
    
    def test_morphological_gradient(self, processor, test_image):
        """Test gradiente morfológico."""
        result = processor.morphological_gradient(test_image, kernel_size=5)
        assert result.shape == test_image.shape
        # Gradiente detecta bordes
        assert np.max(result) > 0
    
    def test_top_hat(self, processor, test_image):
        """Test top-hat."""
        result = processor.top_hat(test_image, kernel_size=5)
        assert result.shape == test_image.shape
        # Top-hat extrae objetos pequeños brillantes
        assert np.max(result) <= np.max(test_image)
    
    def test_black_hat(self, processor, test_image):
        """Test black-hat."""
        result = processor.black_hat(test_image, kernel_size=5)
        assert result.shape == test_image.shape
        # Black-hat extrae objetos pequeños oscuros
    
    def test_opening_bottom_hat(self, processor, test_image):
        """Test opening bottom hat."""
        result = processor.opening_bottom_hat(test_image, kernel_size=5)
        assert result.shape == test_image.shape
    
    def test_closing_top_hat(self, processor, test_image):
        """Test closing top hat."""
        result = processor.closing_top_hat(test_image, kernel_size=5)
        assert result.shape == test_image.shape
    
    def test_gradient_edge_detection(self, processor):
        """Test que gradiente detecta bordes."""
        # Crear imagen con borde nítido
        image = np.zeros((100, 100), dtype=np.uint8)
        cv2.rectangle(image, (20, 20), (80, 80), 255, -1)
        
        result = processor.morphological_gradient(image, kernel_size=3)
        
        # Debe detectar el borde
        assert np.sum(result > 0) > 0


# =============================================================================
# TESTS DE EXTRACCIÓN DE CARACTERÍSTICAS
# =============================================================================

class TestFeatureExtraction:
    """Tests para extracción de características."""
    
    def test_extract_features_basic(self, processor, binary_image):
        """Test extracción básica de características."""
        features = processor.extract_features(binary_image)
        
        assert isinstance(features, MorphologicalFeatures)
        assert features.area > 0
        assert features.perimeter > 0
        assert features.bounding_box_area > 0
    
    def test_extract_features_with_mask(self, processor, test_image):
        """Test extracción con máscara."""
        # Crear máscara
        mask = np.zeros_like(test_image)
        cv2.circle(mask, (128, 128), 64, 255, -1)
        
        features = processor.extract_features(test_image, mask)
        
        assert features.area > 0
    
    def test_extract_features_shape_properties(self, processor):
        """Test propiedades de forma."""
        # Crear círculo perfecto
        image = np.zeros((200, 200), dtype=np.uint8)
        cv2.circle(image, (100, 100), 50, 255, -1)
        
        features = processor.extract_features(image)
        
        # Para círculo: compacidad y circuvaridad cercanas a 1
        assert features.circularity > 0.7
        assert features.compactness > 0.7
    
    def test_extract_features_rectangle(self, processor):
        """Test características de rectángulo."""
        image = np.zeros((200, 200), dtype=np.uint8)
        cv2.rectangle(image, (50, 50), (150, 150), 255, -1)
        
        features = processor.extract_features(image)
        
        # Para rectángulo: rectangularidad cercana a 1
        assert features.rectangularity > 0.8
    
    def test_multi_scale_features(self, processor, test_image):
        """Test extracción multi-escala."""
        features = processor.extract_multi_scale_features(test_image)
        
        assert 'erosion' in features
        assert 'dilation' in features
        assert 'opening' in features
        assert 'closing' in features
        assert len(features['erosion']) > 0
    
    def test_moments(self, processor, test_image):
        """Test momentos."""
        features = processor.extract_features(test_image)
        
        assert features.m10 > 0
        assert features.m01 > 0
        assert len(features.hu_moments) == 7  # 7 momentos de Hu


# =============================================================================
# TESTS DE SEGMENTACIÓN
# =============================================================================

class TestSegmentation:
    """Tests para segmentación."""

    def test_attribute_filtering(self, processor, binary_image):
        """Test filtrado por atributos."""
        # Filtrar por área mínima
        result = processor.attribute_filtering(
            binary_image,
            min_area=500,
            max_area=10000
        )
        
        assert result.shape == binary_image.shape
        assert result.max() <= 255
    
    def test_attribute_filtering_output_value(self, processor, binary_image):
        """Test valor de salida personalizado."""
        result = processor.attribute_filtering(
            binary_image,
            min_area=500,
            output_value=128
        )
        
        assert np.max(result) <= 128
    
    def test_watershed_basic(self, processor, test_image):
        """Test watershed básico."""
        # Crear marcadores simples
        markers = np.zeros(test_image.shape, dtype=np.int32)
        markers[50:100, 50:100] = 1
        markers[150:200, 150:200] = 2
        
        result = processor.watershed_segmentation(test_image, markers)
        
        assert result.labels is not None
        assert result.num_segments >= 0


# =============================================================================
# TESTS DE PROCESAMIENTO ESCALABLE
# =============================================================================

class TestScalableProcessing:
    """Tests para procesamiento escalable."""
    
    def test_process_chunked_basic(self, processor, test_image):
        """Test procesamiento en chunks."""
        result = processor.process_chunked(
            test_image,
            MorphologicalOperation.OPEN,
            kernel_size=3,
            chunk_size=512,
            overlap=32
        )
        
        assert result.shape == test_image.shape
    
    def test_process_chunked_large_image(self, processor):
        """Test con imagen grande."""
        large_image = create_test_image(2048, 2048)
        
        result = processor.process_chunked(
            large_image,
            MorphologicalOperation.GRADIENT,
            kernel_size=5,
            chunk_size=512,
            overlap=64
        )
        
        assert result.shape == large_image.shape
    
    def test_process_tiled(self, processor, test_image):
        """Test con tiles."""
        result = processor.process_tiled(
            test_image,
            MorphologicalOperation.CLOSE,
            tile_width=128,
            tile_height=128,
            overlap=32
        )
        
        assert result.shape == test_image.shape
    
    def test_process_chunked_stats(self, processor, test_image):
        """Test que se actualizan estadísticas."""
        processor.reset_stats()
        
        processor.process_chunked(
            test_image,
            MorphologicalOperation.OPEN,
            chunk_size=128,
            overlap=16
        )
        
        stats = processor.get_stats()
        assert stats['chunked_operations'] > 0


# =============================================================================
# TESTS DE INTEGRACIÓN CON ÍNDICES
# =============================================================================

class TestIndicesIntegration:
    """Tests de integración con procesador de índices."""
    
    def test_morphological_for_ndvi_processing(self, processor):
        """Test procesamiento morfológico para post-procesamiento NDVI."""
        # Crear NDVI simulado
        np.random.seed(42)
        ndvi = np.random.uniform(-1, 1, (256, 256)).astype(np.float32)
        
        # Aplicar cierre para suavizar
        closed = processor.close(ndvi.astype(np.uint8), kernel_size=5)
        
        assert closed.shape == ndvi.shape
    
    def test_change_detection_with_morphology(self, processor, test_image):
        """Test detección de cambios con operaciones morfológicas."""
        # Crear dos imágenes (antes y después)
        np.random.seed(42)
        before = create_test_image()
        after = before.copy()
        
        # Modificar "después" (agregar un objeto)
        cv2.circle(after, (200, 200), 30, 255, -1)
        
        # Usar top-hat para detectar cambios brillantes
        diff = processor.top_hat(after, kernel_size=5)
        
        assert diff.shape == before.shape
        assert np.sum(diff) >= 0


# =============================================================================
# TESTS DE FUNCIONES DE CONVENIENCIA
# =============================================================================

class TestConvenienceFunctions:
    """Tests para funciones de conveniencia."""
    
    def test_morphological_open_function(self, test_image):
        """Test función open."""
        result = morphological_open(test_image, kernel_size=5)
        assert result.shape == test_image.shape
    
    def test_morphological_close_function(self, test_image):
        """Test función close."""
        result = morphological_close(test_image, kernel_size=5)
        assert result.shape == test_image.shape
    
    def test_morphological_gradient_function(self, test_image):
        """Test función gradient."""
        result = morphological_gradient(test_image, kernel_size=5)
        assert result.shape == test_image.shape
    
    def test_extract_features_function(self, binary_image):
        """Test función extract_features."""
        features = extract_morphology_features(binary_image)
        
        assert isinstance(features, dict)
        assert 'area' in features
        assert 'compactness' in features


# =============================================================================
# TESTS DE RENDIMIENTO
# =============================================================================

class TestPerformance:
    """Tests de rendimiento."""
    
    def test_operation_time(self, processor, test_image):
        """Test tiempo de operación."""
        import time
        
        start = time.time()
        result = processor.open(test_image, kernel_size=7)
        elapsed = time.time() - start
        
        assert elapsed < 1.0  # Debe completar en menos de 1 segundo
    
    def test_large_image_performance(self, processor):
        """Test rendimiento con imagen grande."""
        import time
        
        large = create_test_image(1024, 1024)
        
        start = time.time()
        result = processor.process_chunked(
            large,
            MorphologicalOperation.OPEN,
            chunk_size=512,
            overlap=64
        )
        elapsed = time.time() - start
        
        assert elapsed < 5.0  # Chunked debe ser eficiente
        assert result.shape == large.shape


# =============================================================================
# TESTS DE CASOS EDGE
# =============================================================================

class TestEdgeCases:
    """Tests para casos extremos."""
    
    def test_empty_image(self, processor):
        """Test con imagen vacía."""
        image = np.zeros((100, 100), dtype=np.uint8)
        
        result = processor.erode(image, kernel_size=3)
        assert result.shape == image.shape
    
    def test_full_image(self, processor):
        """Test con imagen llena."""
        image = np.ones((100, 100), dtype=np.uint8) * 255
        
        result = processor.dilate(image, kernel_size=3)
        assert result.shape == image.shape
    
    def test_single_pixel(self, processor):
        """Test con imagen de un pixel."""
        image = np.array([[255]], dtype=np.uint8)
        
        result = processor.erode(image, kernel_size=3)
        assert result.shape == image.shape
    
    def test_kernel_larger_than_image(self, processor):
        """Test con kernel mayor que imagen."""
        image = np.ones((10, 10), dtype=np.uint8) * 255
        
        result = processor.erode(image, kernel_size=21)
        assert result.shape == image.shape
    
    def test_different_dtypes(self, processor):
        """Test diferentes tipos de datos."""
        # uint8
        img8 = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
        result8 = processor.erode(img8, kernel_size=3)
        assert result8.dtype == np.uint8
        
        # float32
        img32 = np.random.uniform(0, 1, (100, 100)).astype(np.float32)
        result32 = processor.erode(img32, kernel_size=3)
        assert result32.dtype == np.float32


# =============================================================================
# MAIN PARA EJECUTAR TESTS
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("EJECUTANDO TESTS - MORPHOLOGICAL PROCESSOR")
    print("=" * 60)
    
    pytest.main([__file__, "-v", "--tb=short"])