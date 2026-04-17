"""
Módulo de Procesamiento Morfológico para Skyfusion Analytics
=============================================================
Procesamiento morfológico avanzado para clasificación y detección de cambios
en imágenes satelitales y datos geoespaciales.

Operaciones implementadas:
- Erosión y Dilatación
- Apertura y Cierre
- Gradiente Morfológico
- Top-Hat y Black-Hat
- Segmentación por Watershed
- Filtrado de Atributos
- Extracción de características morfológicas
- Procesamiento escalable para imágenes grandes

Autor: Skyfusion Analytics Team
Fecha: 2026
"""

import numpy as np
import cv2
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime
import warnings
from scipy import ndimage as scipy_ndimage
from scipy.ndimage import label as scipy_label


class MorphologicalKernelType(Enum):
    """Tipos de elementos estructurantes disponibles."""
    SQUARE = "square"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    CROSS = "cross"
    LINE_H = "line_h"
    LINE_V = "line_v"
    DIAMOND = "diamond"


class MorphologicalOperation(Enum):
    """Operaciones morfológicas disponibles."""
    ERODE = "erode"
    DILATE = "dilate"
    OPEN = "open"
    CLOSE = "close"
    GRADIENT = "gradient"
    TOP_HAT = "top_hat"
    BLACK_HAT = "black_hat"
    OPENING_BOTTOM_HAT = "opening_bottom_hat"
    CLOSING_TOP_HAT = "closing_top_hat"


@dataclass
class MorphologicalConfig:
    """Configuración para operaciones morfológicas."""
    kernel_size: int = 3
    kernel_type: MorphologicalKernelType = MorphologicalKernelType.SQUARE
    iterations: int = 1
    border_type: int = cv2.BORDER_CONSTANT
    border_value: float = 0
    use_gpu: bool = False
    
    def validate(self) -> bool:
        """Valida la configuración."""
        if self.kernel_size < 1:
            raise ValueError("El tamaño del kernel debe ser >= 1")
        if self.iterations < 1:
            raise ValueError("Las iteraciones deben ser >= 1")
        if self.border_type not in [cv2.BORDER_CONSTANT, cv2.BORDER_REPLICATE, cv2.BORDER_REFLECT]:
            raise ValueError("Tipo de borde no válido")
        return True


@dataclass
class MorphologicalFeatures:
    """Características morfológicas extraídas para clasificación."""
    # Características de forma
    area: float = 0
    perimeter: float = 0
    bounding_box_area: float = 0
    bounding_box_width: float = 0
    bounding_box_height: float = 0
    centroid_x: float = 0
    centroid_y: float = 0
    compactness: float = 0
    circularity: float = 0
    elongation: float = 0
    rectangularity: float = 0
    solidity: float = 0
    
    # Características de textura morfológica
    euler_number: int = 0
    num_holes: int = 0
    num_components: int = 0
    
    # Estadísticas de intensidad
    mean_intensity: float = 0
    std_intensity: float = 0
    min_intensity: float = 0
    max_intensity: float = 0
    
    # Características basadas en momentos
    m10: float = 0
    m01: float = 0
    m20: float = 0
    m02: float = 0
    m11: float = 0
    hu_moments: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, float]:
        """Convierte a diccionario para serialización."""
        return {
            'area': self.area,
            'perimeter': self.perimeter,
            'bounding_box_area': self.bounding_box_area,
            'bounding_box_width': self.bounding_box_width,
            'bounding_box_height': self.bounding_box_height,
            'centroid_x': self.centroid_x,
            'centroid_y': self.centroid_y,
            'compactness': self.compactness,
            'circularity': self.circularity,
            'elongation': self.elongation,
            'rectangularity': self.rectangularity,
            'solidity': self.solidity,
            'euler_number': self.euler_number,
            'num_holes': self.num_holes,
            'num_components': self.num_components,
            'mean_intensity': self.mean_intensity,
            'std_intensity': self.std_intensity,
            'min_intensity': self.min_intensity,
            'max_intensity': self.max_intensity,
            'm10': self.m10,
            'm01': self.m01,
            'm20': self.m20,
            'm02': self.m02,
            'm11': self.m11,
            'hu_moments': self.hu_moments
        }


@dataclass
class SegmentationResult:
    """Resultado de segmentación."""
    labels: np.ndarray
    num_segments: int
    segment_areas: Dict[int, int]
    segment_properties: Dict[int, Dict[str, Any]]
    boundary_mask: Optional[np.ndarray] = None


class MorphologicalProcessor:
    """
    Procesador Morfológico Avanzado para Skyfusion Analytics.
    
    Proporciona operaciones morfológicas completas para análisis de imágenes
    satelitales y clasificación, incluyendo operaciones avanzadas y
    procesamiento escalable para imágenes de gran tamaño.
    """
    
    # Constantes para tipos de borde
    BORDER_CONSTANT = cv2.BORDER_CONSTANT
    BORDER_REPLICATE = cv2.BORDER_REPLICATE
    BORDER_REFLECT = cv2.BORDER_REFLECT
    
    def __init__(
        self,
        output_dir: str = "../../data/output/morphological",
        default_kernel_size: int = 3,
        default_kernel_type: MorphologicalKernelType = MorphologicalKernelType.SQUARE,
        memory_limit_mb: int = 2048
    ):
        """
        Inicializa el procesador morfológico.
        
        Args:
            output_dir: Directorio para guardar resultados
            default_kernel_size: Tamaño de kernel por defecto
            default_kernel_type: Tipo de kernel por defecto
            memory_limit_mb: Límite de memoria en MB para procesamiento chunked
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.default_kernel_size = default_kernel_size
        self.default_kernel_type = default_kernel_type
        self.memory_limit_mb = memory_limit_mb
        
        # Cache de kernels precalculados
        self._kernel_cache: Dict[Tuple, np.ndarray] = {}
        
        # Estadísticas de procesamiento
        self.stats = {
            'total_operations': 0,
            'gpu_operations': 0,
            'chunked_operations': 0,
            'processing_time_ms': 0
        }
    
    # =========================================================================
    # GENERADORES DE ELEMENTOS ESTRUCTURANTES
    # =========================================================================
    
    def create_kernel(
        self,
        kernel_size: int,
        kernel_type: MorphologicalKernelType = None,
        angle: float = 0
    ) -> np.ndarray:
        """
        Crea un elemento estructural según el tipo especificado.
        
        Args:
            kernel_size: Tamaño del kernel (debe ser impar)
            kernel_type: Tipo de elemento estructural
            angle: Ángulo para kernels lineales (grados)
            
        Returns:
            Kernel numpy binario
        """
        if kernel_type is None:
            kernel_type = self.default_kernel_type
        
        cache_key = (kernel_size, kernel_type.value, angle)
        if cache_key in self._kernel_cache:
            return self._kernel_cache[cache_key].copy()
        
        ksize = kernel_size if kernel_size % 2 == 1 else kernel_size + 1
        
        if kernel_type == MorphologicalKernelType.SQUARE:
            kernel = np.ones((ksize, ksize), dtype=np.uint8)
            
        elif kernel_type == MorphologicalKernelType.CIRCLE:
            kernel = cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE,
                (ksize, ksize)
            )
            
        elif kernel_type == MorphologicalKernelType.ELLIPSE:
            kernel = cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE,
                (ksize, ksize)
            )
            
        elif kernel_type == MorphologicalKernelType.CROSS:
            kernel = np.zeros((ksize, ksize), dtype=np.uint8)
            center = ksize // 2
            kernel[center, :] = 1
            kernel[:, center] = 1
            
        elif kernel_type == MorphologicalKernelType.LINE_H:
            kernel = np.ones((1, ksize), dtype=np.uint8)
            
        elif kernel_type == MorphologicalKernelType.LINE_V:
            kernel = np.ones((ksize, 1), dtype=np.uint8)
            
        elif kernel_type == MorphologicalKernelType.DIAMOND:
            kernel = self._create_diamond_kernel(ksize)
            
        else:
            raise ValueError(f"Tipo de kernel no reconocido: {kernel_type}")
        
        self._kernel_cache[cache_key] = kernel
        return kernel.copy()
    
    def _create_diamond_kernel(self, size: int) -> np.ndarray:
        """Crea un kernel diamantado."""
        half = size // 2
        kernel = np.zeros((size, size), dtype=np.uint8)
        
        for i in range(size):
            for j in range(size):
                if abs(i - half) + abs(j - half) <= half:
                    kernel[i, j] = 1
        
        return kernel
    
    # =========================================================================
    # OPERACIONES MORFOLÓGICAS BÁSICAS
    # =========================================================================
    
    def erode(
        self,
        image: np.ndarray,
        kernel_size: int = None,
        kernel_type: MorphologicalKernelType = None,
        iterations: int = 1,
        border_type: int = None,
        mask: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Erosión morfológica.
        
        La erosión shrinks objetos明亮 en una imagen, eliminando píxeles
        en los bordes de regiones brillantes.
        
        Args:
            image: Imagen de entrada (uint8 o float32)
            kernel_size: Tamaño del elemento estructural
            kernel_type: Tipo de elemento estructural
            iterations: Número de iteraciones
            border_type: Tipo de manejo de bordes
            mask: Máscara opcional para operación enmascarada
            
        Returns:
            Imagen erosionada
        """
        if kernel_size is None:
            kernel_size = self.default_kernel_size
        if kernel_type is None:
            kernel_type = self.default_kernel_type
        if border_type is None:
            border_type = cv2.BORDER_CONSTANT
        
        kernel = self.create_kernel(kernel_size, kernel_type)
        
        if mask is not None:
            result = cv2.erode(image, kernel, iterations=iterations, borderType=border_type, mask=mask)
        else:
            result = cv2.erode(image, kernel, iterations=iterations, borderType=border_type)
        
        self.stats['total_operations'] += 1
        return result
    
    def dilate(
        self,
        image: np.ndarray,
        kernel_size: int = None,
        kernel_type: MorphologicalKernelType = None,
        iterations: int = 1,
        border_type: int = None,
        mask: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Dilatación morfológica.
        
        La dilatación expande objetos明亮 en una imagen, añadiendo píxeles
        en los bordes de regiones brillantes.
        
        Args:
            image: Imagen de entrada
            kernel_size: Tamaño del elemento estructural
            kernel_type: Tipo de elemento estructural
            iterations: Número de iteraciones
            border_type: Tipo de manejo de bordes
            mask: Máscara opcional
            
        Returns:
            Imagen dilatada
        """
        if kernel_size is None:
            kernel_size = self.default_kernel_size
        if kernel_type is None:
            kernel_type = self.default_kernel_type
        if border_type is None:
            border_type = cv2.BORDER_CONSTANT
        
        kernel = self.create_kernel(kernel_size, kernel_type)
        
        if mask is not None:
            result = cv2.dilate(image, kernel, iterations=iterations, borderType=border_type, mask=mask)
        else:
            result = cv2.dilate(image, kernel, iterations=iterations, borderType=border_type)
        
        self.stats['total_operations'] += 1
        return result
    
    def open(
        self,
        image: np.ndarray,
        kernel_size: int = None,
        kernel_type: MorphologicalKernelType = None,
        iterations: int = 1,
        border_type: int = None
    ) -> np.ndarray:
        """
        Apertura morfológica.
        
        Erosión seguida de dilatación. Elimina objetos pequeños (ruido)
        mientras preserva la forma general de objetos más grandes.
        
        Args:
            image: Imagen de entrada
            kernel_size: Tamaño del elemento estructural
            kernel_type: Tipo de elemento estructural
            iterations: Iteraciones para cada operación
            border_type: Tipo de manejo de bordes
            
        Returns:
            Imagen procesada con apertura
        """
        if kernel_size is None:
            kernel_size = self.default_kernel_size
        if kernel_type is None:
            kernel_type = self.default_kernel_type
        if border_type is None:
            border_type = cv2.BORDER_CONSTANT
        
        kernel = self.create_kernel(kernel_size, kernel_type)
        result = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel, 
                              iterations=iterations, borderType=border_type)
        
        self.stats['total_operations'] += 1
        return result
    
    def close(
        self,
        image: np.ndarray,
        kernel_size: int = None,
        kernel_type: MorphologicalKernelType = None,
        iterations: int = 1,
        border_type: int = None
    ) -> np.ndarray:
        """
        Cierre morfológico.
        
        Dilatación seguida de erosión. Elimina agujeros pequeños (ruido)
        dentro de objetos mientras preserva la forma general.
        
        Args:
            image: Imagen de entrada
            kernel_size: Tamaño del elemento estructural
            kernel_type: Tipo de elemento estructural
            iterations: Iteraciones para cada operación
            border_type: Tipo de manejo de bordes
            
        Returns:
            Imagen procesada con cierre
        """
        if kernel_size is None:
            kernel_size = self.default_kernel_size
        if kernel_type is None:
            kernel_type = self.default_kernel_type
        if border_type is None:
            border_type = cv2.BORDER_CONSTANT
        
        kernel = self.create_kernel(kernel_size, kernel_type)
        result = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel,
                              iterations=iterations, borderType=border_type)
        
        self.stats['total_operations'] += 1
        return result
    
    # =========================================================================
    # OPERACIONES MORFOLÓGICAS AVANZADAS
    # =========================================================================
    
    def morphological_gradient(
        self,
        image: np.ndarray,
        kernel_size: int = None,
        kernel_type: MorphologicalKernelType = None,
        border_type: int = None
    ) -> np.ndarray:
        """
        Gradiente morfológico.
        
        Calcula el borde de objetos como: dilatación - erosión.
        Útil para detección de bordes y contornos.
        
        Args:
            image: Imagen de entrada
            kernel_size: Tamaño del elemento estructural
            kernel_type: Tipo de elemento estructural
            border_type: Tipo de manejo de bordes
            
        Returns:
            Imagen con gradiente morfológico
        """
        if kernel_size is None:
            kernel_size = self.default_kernel_size
        if kernel_type is None:
            kernel_type = self.default_kernel_type
        if border_type is None:
            border_type = cv2.BORDER_CONSTANT
        
        kernel = self.create_kernel(kernel_size, kernel_type)
        result = cv2.morphologyEx(image, cv2.MORPH_GRADIENT, kernel, borderType=border_type)
        
        self.stats['total_operations'] += 1
        return result
    
    def top_hat(
        self,
        image: np.ndarray,
        kernel_size: int = None,
        kernel_type: MorphologicalKernelType = None,
        border_type: int = None
    ) -> np.ndarray:
        """
        Transformada Top-Hat.
        
        Extrae objetos pequeños明亮的 de la imagen: imagen - apertura(imagen).
        Útil para detectar estructuras pequeñas (rios, caminos, edificios).
        
        Args:
            image: Imagen de entrada
            kernel_size: Tamaño del elemento estructural
            kernel_type: Tipo de elemento estructural
            border_type: Tipo de manejo de bordes
            
        Returns:
            Imagen con transformada top-hat
        """
        if kernel_size is None:
            kernel_size = self.default_kernel_size
        if kernel_type is None:
            kernel_type = self.default_kernel_type
        if border_type is None:
            border_type = cv2.BORDER_CONSTANT
        
        kernel = self.create_kernel(kernel_size, kernel_type)
        result = cv2.morphologyEx(image, cv2.MORPH_TOPHAT, kernel, borderType=border_type)
        
        self.stats['total_operations'] += 1
        return result
    
    def black_hat(
        self,
        image: np.ndarray,
        kernel_size: int = None,
        kernel_type: MorphologicalKernelType = None,
        border_type: int = None
    ) -> np.ndarray:
        """
        Transformada Black-Hat.
        
        Extrae objetos pequeños oscuros de la imagen: cierre(imagen) - imagen.
        Útil para detectar huecos y regiones oscuras pequeñas.
        
        Args:
            image: Imagen de entrada
            kernel_size: Tamaño del elemento estructural
            kernel_type: Tipo de elemento estructural
            border_type: Tipo de manejo de bordes
            
        Returns:
            Imagen con transformada black-hat
        """
        if kernel_size is None:
            kernel_size = self.default_kernel_size
        if kernel_type is None:
            kernel_type = self.default_kernel_type
        if border_type is None:
            border_type = cv2.BORDER_CONSTANT
        
        kernel = self.create_kernel(kernel_size, kernel_type)
        result = cv2.morphologyEx(image, cv2.MORPH_BLACKHAT, kernel, borderType=border_type)
        
        self.stats['total_operations'] += 1
        return result
    
    def opening_bottom_hat(
        self,
        image: np.ndarray,
        kernel_size: int = None,
        kernel_type: MorphologicalKernelType = None
    ) -> np.ndarray:
        """
        Apertura seguida de Bottom-Hat.
        
        Combina apertura (para eliminar ruido pequeño) con bottom-hat
        (para extraer detalles oscuros restantes).
        
        Args:
            image: Imagen de entrada
            kernel_size: Tamaño del elemento estructural
            kernel_type: Tipo de elemento estructural
            
        Returns:
            Imagen procesada
        """
        if kernel_size is None:
            kernel_size = self.default_kernel_size
        if kernel_type is None:
            kernel_type = self.default_kernel_type
        
        opened = self.open(image, kernel_size, kernel_type)
        result = cv2.absdiff(opened, image)
        
        return result
    
    def closing_top_hat(
        self,
        image: np.ndarray,
        kernel_size: int = None,
        kernel_type: MorphologicalKernelType = None
    ) -> np.ndarray:
        """
        Cierre seguido de Top-Hat.
        
        Combina cierre (para eliminar huecos) con top-hat
        (para extraer detalles brillantes restantes).
        
        Args:
            image: Imagen de entrada
            kernel_size: Tamaño del elemento estructural
            kernel_type: Tipo de elemento estructural
            
        Returns:
            Imagen procesada
        """
        if kernel_size is None:
            kernel_size = self.default_kernel_size
        if kernel_type is None:
            kernel_type = self.default_kernel_type
        
        closed = self.close(image, kernel_size, kernel_type)
        result = cv2.absdiff(image, closed)
        
        return result
    
    # =========================================================================
    # OPERACIONES DE SEGMENTACIÓN AVANZADA
    # =========================================================================
    
    def watershed_segmentation(
        self,
        image: np.ndarray,
        markers: np.ndarray,
        mask: Optional[np.ndarray] = None,
        use_threshold_marker: bool = False,
        threshold_value: int = 128
    ) -> SegmentationResult:
        """
        Segmentación por Watershed (marcador-controlado).
        
        Implementa watershed basado en marcadores para separación de objetos
        que se tocan entre sí.
        
        Args:
            image: Imagen de entrada (grayscale o color)
            markers: Marcadores iniciales (uint8, same shape as image)
            mask: Máscara opcional para región de interés
            use_threshold_marker: Si True, genera marcadores阈值 automáticos
            threshold_value: Valor umbral para生成 marcadores automáticos
            
        Returns:
            SegmentationResult con etiquetas y propiedades
        """
        # Asegurar tipo correcto
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Generar marcadores si no se proporcionan
        if use_threshold_marker:
            _, markers = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)
            markers = scipy_label(markers)[0]
        
        # Asegurar que los marcadores sean int32
        markers = markers.astype(np.int32)
        
        # cv2.watershed requiere imagen de 3 canales
        if len(image.shape) == 3:
            image_3ch = image.copy()
        else:
            image_3ch = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        
        # Marker watershed
        markers = cv2.watershed(image_3ch, markers)
        
        # Calcular propiedades de segmentos
        num_segments = len(np.unique(markers)) - 1  # Excluir -1 (bordes)
        segment_areas = {}
        segment_properties = {}
        
        for label in np.unique(markers):
            if label == -1:
                continue
            segment_mask = (markers == label)
            area = np.sum(segment_mask)
            segment_areas[int(label)] = int(area)
            
            # Propiedades adicionales
            if area > 0:
                y_coords, x_coords = np.where(segment_mask)
                segment_properties[int(label)] = {
                    'area': int(area),
                    'centroid_x': float(np.mean(x_coords)),
                    'centroid_y': float(np.mean(y_coords)),
                    'bbox_x1': int(np.min(x_coords)),
                    'bbox_y1': int(np.min(y_coords)),
                    'bbox_x2': int(np.max(x_coords)),
                    'bbox_y2': int(np.max(y_coords))
                }
        
        return SegmentationResult(
            labels=markers,
            num_segments=num_segments,
            segment_areas=segment_areas,
            segment_properties=segment_properties
        )
    
    def markerControlledWatershed(
        self,
        image: np.ndarray,
        foreground_markers: np.ndarray,
        background_markers: Optional[np.ndarray] = None,
        kernel_size: int = 3
    ) -> np.ndarray:
        """
        Watershed controlado por marcadores (versión simplificada).
        
        Args:
            image: Imagen de entrada
            foreground_markers: Marcadores de primer plano
            background_markers: Marcadores de fondo (opcional)
            kernel_size: Tamaño para cierre antes de marcadores
            
        Returns:
            Imagen con etiquetas de segmentación
        """
        # Asegurar entrada binaria
        if foreground_markers.max() > 1:
            _, fg = cv2.threshold(foreground_markers, 127, 255, cv2.THRESH_BINARY)
        else:
            fg = (foreground_markers * 255).astype(np.uint8)
        
        # Cerrar para smoothing de marcadores
        kernel = self.create_kernel(kernel_size)
        fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, kernel)
        
        # Etiquetar marcadores
        if background_markers is not None:
            if background_markers.max() > 1:
                _, bg = cv2.threshold(background_markers, 127, 255, cv2.THRESH_BINARY)
            else:
                bg = (background_markers * 255).astype(np.uint8)
            bg = cv2.morphologyEx(bg, cv2.MORPH_CLOSE, kernel)
            
            # Combinar marcadores
            markers = fg + bg
        else:
            markers = fg
        
        # Encontrar distancia y watershed
        dist = cv2.distanceTransform(markers, cv2.DIST_L2, 5)
        
        # Marcadores para watershed
        _, markers = cv2.threshold(dist, 0.3 * dist.max(), 255, cv2.THRESH_BINARY)
        markers = np.uint8(markers)
        markers = scipy_label(markers)[0]
        
        # Aplicar watershed
        result = cv2.watershed(image, markers)
        
        return result
    
    def attribute_filtering(
        self,
        image: np.ndarray,
        min_area: int = None,
        max_area: int = None,
        min_solidity: float = None,
        max_solidity: float = None,
        min_compactness: float = None,
        output_value: int = 255
    ) -> np.ndarray:
        """
        Filtrado de objetos por atributos.
        
        Elimina o conserva objetos basándose en características morfológicas.
        
        Args:
            image: Imagen binaria de entrada
            min_area: Área mínima del objeto (píxeles)
            max_area: Área máxima del objeto
            min_solidity: Solidez mínima (área/área_convex)
            max_solidity: Solidez máxima
            min_compactness: Compacidad mínima
            output_value: Valor de salida para objetos conservados
            
        Returns:
            Imagen filtrada
        """
        # Asegurar imagen binaria
        if image.max() > 1:
            _, binary = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)
        else:
            binary = (image * 255).astype(np.uint8)
        
        # Etiquetar componentes conectados
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary)
        
        result = np.zeros_like(binary)
        
        for i in range(1, num_labels):  # Excluir fondo (label 0)
            area = stats[i, cv2.CC_STAT_AREA]
            solidity = 1.0
            compactness = 1.0
            
            # Calcular convex hull para solidez
            contour = np.where(labels == i)
            if len(contour[0]) > 0:
                hull = cv2.convexHull(np.column_stack(contour).astype(np.int32))
                hull_area = cv2.contourArea(hull)
                if hull_area > 0:
                    solidity = area / hull_area
            
            # Calcular compacidad
            perimeter = stats[i, 4]  # cv2.CC_STAT_PERIMETER equivalente
            if perimeter > 0:
                compactness = (4 * np.pi * area) / (perimeter ** 2)
            
            # Verificar criterios
            keep = True
            
            if min_area is not None and area < min_area:
                keep = False
            if max_area is not None and area > max_area:
                keep = False
            if min_solidity is not None and solidity < min_solidity:
                keep = False
            if max_solidity is not None and solidity > max_solidity:
                keep = False
            if min_compactness is not None and compactness < min_compactness:
                keep = False
            
            if keep:
                result[labels == i] = output_value
        
        return result
    
    # =========================================================================
    # EXTRACCIÓN DE CARACTERÍSTICAS MORFOLÓGICAS
    # =========================================================================
    
    def extract_features(
        self,
        image: np.ndarray,
        region_mask: Optional[np.ndarray] = None
    ) -> MorphologicalFeatures:
        """
        Extrae características morfológicas completas para clasificación.
        
        Args:
            image: Imagen de entrada (escala de grises o binaria)
            region_mask: Máscara de región a analizar (None = toda la imagen)
            
        Returns:
            MorphologicalFeatures con características extraídas
        """
        # Convertir a escala de grises si es necesario
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Aplicar máscara si se proporciona
        if region_mask is not None:
            mask = region_mask.astype(np.uint8)
            gray = cv2.bitwise_and(gray, gray, mask=mask)
        else:
            mask = None
        
        # Calcular momentos
        # Calcular momentos
        if mask is not None:
            moments = cv2.moments(mask)
        else:
            moments = cv2.moments(gray)
        
        # Calcular momentos de Hu
        hu_moments = cv2.HuMoments(moments).flatten()
        hu_moments = [-np.sign(x) * np.log10(abs(x) + 1e-10) for x in hu_moments]
        
        # Extraer contornos
        if mask is not None:
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        else:
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Crear objeto de características
        features = MorphologicalFeatures()
        
        if len(contours) == 0:
            return features
        
        # Usar el contorno más grande
        contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        features.area = float(area)
        features.perimeter = float(perimeter)
        
        # Caja delimitadora
        x, y, w, h = cv2.boundingRect(contour)
        features.bounding_box_area = float(w * h)
        features.bounding_box_width = float(w)
        features.bounding_box_height = float(h)
        
        # Centroide
        M = cv2.moments(contour)
        if M['m00'] != 0:
            features.centroid_x = float(M['m10'] / M['m00'])
            features.centroid_y = float(M['m01'] / M['m00'])
        
        # Compacidad (4π * área / perímetro²)
        if perimeter > 0:
            features.compactness = float((4 * np.pi * area) / (perimeter ** 2))
        
        # Circularidad
        if perimeter > 0:
            features.circularity = float(4 * np.pi * area / (perimeter ** 2))
        
        # Solidez (área / área convex hull)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        features.solidity = float(area / hull_area) if hull_area > 0 else 0
        
        # Rectangularidad (área / área rectángulo delimitador)
        rect_area = w * h
        features.rectangularity = float(area / rect_area) if rect_area > 0 else 0
        
        # Elongación (relación aspecto del bounding box)
        features.elongation = float(min(w, h) / max(w, h)) if max(w, h) > 0 else 1
        
        # Número de Euler (componentes - huecos)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        labeled_array, n_components = scipy_label(binary)
        n_components = int(n_components)
        
        # Contar huecos
        n_holes = 0
        contours_ext, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours_ext) > 0:
            contours_int, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            n_holes = max(0, len(contours_int) - len(contours_ext))
        
        features.num_components = n_components
        features.num_holes = int(max(0, n_holes))
        features.euler_number = int(n_components - features.num_holes)
        
        # Estadísticas de intensidad
        features.mean_intensity = float(np.mean(gray))
        features.std_intensity = float(np.std(gray))
        features.min_intensity = float(np.min(gray))
        features.max_intensity = float(np.max(gray))
        
        # Momentos
        features.m10 = float(moments['m10'])
        features.m01 = float(moments['m01'])
        features.m20 = float(moments['m20'])
        features.m02 = float(moments['m02'])
        features.m11 = float(moments['m11'])
        features.hu_moments = hu_moments
        
        return features
    
    def extract_multi_scale_features(
        self,
        image: np.ndarray,
        scales: List[int] = None,
        kernel_type: MorphologicalKernelType = None
    ) -> Dict[str, List[float]]:
        """
        Extrae características a múltiples escalas para análisis multi-escala.
        
        Args:
            image: Imagen de entrada
            scales: Lista de tamaños de kernel a usar
            kernel_type: Tipo de elemento estructural
            
        Returns:
            Diccionario con características a cada escala
        """
        if scales is None:
            scales = [3, 5, 7, 9, 11]
        if kernel_type is None:
            kernel_type = MorphologicalKernelType.CIRCLE
        
        features = {
            'erosion': [],
            'dilation': [],
            'opening': [],
            'closing': [],
            'gradient': [],
            'top_hat': [],
            'black_hat': []
        }
        
        for scale in scales:
            # Erosión en cada escala
            eroded = self.erode(image, scale, kernel_type)
            features['erosion'].append(float(np.mean(eroded)))
            
            # Dilatación
            dilated = self.dilate(image, scale, kernel_type)
            features['dilation'].append(float(np.mean(dilated)))
            
            # Apertura
            opened = self.open(image, scale, kernel_type)
            features['opening'].append(float(np.mean(opened)))
            
            # Cierre
            closed = self.close(image, scale, kernel_type)
            features['closing'].append(float(np.mean(closed)))
            
            # Gradiente
            gradient = self.morphological_gradient(image, scale, kernel_type)
            features['gradient'].append(float(np.mean(gradient)))
            
            # Top-hat
            tophat = self.top_hat(image, scale, kernel_type)
            features['top_hat'].append(float(np.mean(tophat)))
            
            # Black-hat
            blackhat = self.black_hat(image, scale, kernel_type)
            features['black_hat'].append(float(np.mean(blackhat)))
        
        # Añadir estadísticas
        features['mean'] = [float(np.mean(image))] * len(scales)
        features['std'] = [float(np.std(image))] * len(scales)
        
        return features
    
    # =========================================================================
    # PROCESAMIENTO ESCALABLE PARA IMÁGENES GRANDES
    # =========================================================================
    
    def process_chunked(
        self,
        image: np.ndarray,
        operation: MorphologicalOperation,
        kernel_size: int = None,
        chunk_size: int = 512,
        overlap: int = 32,
        kernel_type: MorphologicalKernelType = None,
        **kwargs
    ) -> np.ndarray:
        """
        Procesa imágenes grandes en chunks (versión simplificada).
        
        Args:
            image: Imagen de entrada
            operation: Operación morfológica
            chunk_size: Tamaño de cada chunk
            overlap: Superposición
            kernel_size: Tamaño del kernel
            kernel_type: Tipo de kernel
            
        Returns:
            Imagen procesada
        """
        if kernel_size is None:
            kernel_size = self.default_kernel_size
        if kernel_type is None:
            kernel_type = self.default_kernel_type
        
        h, w = image.shape[:2]
        result = np.zeros_like(image)
        
        # Procesar sin overlap complejo - solo aplicar operación a cada chunk
        for y in range(0, h, chunk_size):
            for x in range(0, w, chunk_size):
                y_end = min(y + chunk_size, h)
                x_end = min(x + chunk_size, w)
                
                chunk = image[y:y_end, x:x_end].copy()
                
                # Aplicar operación einfach
                if operation == MorphologicalOperation.ERODE:
                    processed = self.erode(chunk, kernel_size, kernel_type, **kwargs)
                elif operation == MorphologicalOperation.DILATE:
                    processed = self.dilate(chunk, kernel_size, kernel_type, **kwargs)
                elif operation == MorphologicalOperation.OPEN:
                    processed = self.open(chunk, kernel_size, kernel_type, **kwargs)
                elif operation == MorphologicalOperation.CLOSE:
                    processed = self.close(chunk, kernel_size, kernel_type, **kwargs)
                elif operation == MorphologicalOperation.GRADIENT:
                    processed = self.morphological_gradient(chunk, kernel_size, kernel_type, **kwargs)
                elif operation == MorphologicalOperation.TOP_HAT:
                    processed = self.top_hat(chunk, kernel_size, kernel_type, **kwargs)
                elif operation == MorphologicalOperation.BLACK_HAT:
                    processed = self.black_hat(chunk, kernel_size, kernel_type, **kwargs)
                else:
                    raise ValueError(f"Operación no soportada: {operation}")
                
                result[y:y_end, x:x_end] = processed
        
        self.stats['chunked_operations'] += 1
        return result
    
    def process_tiled(
        self,
        image: np.ndarray,
        operation: MorphologicalOperation,
        tile_width: int = 1024,
        tile_height: int = 1024,
        overlap: int = 32,
        kernel_size: int = None
    ) -> np.ndarray:
        """
        Procesa imágenes grandes en tiles (alias para process_chunked).
        
        Args:
            image: Imagen de entrada
            operation: Operación a aplicar
            tile_width: Ancho de cada tile
            tile_height: Alto de cada tile
            overlap: Superposición
            kernel_size: Tamaño del kernel
            
        Returns:
            Imagen procesada
        """
        return self.process_chunked(
            image, operation, kernel_size=kernel_size,
            chunk_size=max(tile_width, tile_height),
            overlap=overlap
        )
    
    # =========================================================================
    # CLASIFICACIÓN BASADA EN CARACTERÍSTICAS MORFOLÓGICAS
    # =========================================================================
    
    def classify_regions(
        self,
        image: np.ndarray,
        region_masks: Dict[str, np.ndarray],
        feature_names: List[str] = None
    ) -> Dict[str, Any]:
        """
        Clasifica regiones basándose en características morfológicas.
        
        Args:
            image: Imagen de entrada
            region_masks: Diccionario de máscaras por clase
            feature_names: Lista de características a usar
            
        Returns:
            Diccionario con clasificaciones
        """
        if feature_names is None:
            feature_names = ['area', 'compactness', 'circularity', 'solidity']
        
        classifications = {}
        
        for class_name, mask in region_masks.items():
            features = self.extract_features(image, mask)
            features_dict = features.to_dict()
            
            # Extraer solo las características solicitadas
            selected = {k: features_dict[k] for k in feature_names if k in features_dict}
            classifications[class_name] = selected
        
        return classifications
    
    def create_morphological_profile(
        self,
        image: np.ndarray,
        base_kernel_size: int = 3,
        num_scales: int = 5,
        kernel_type: MorphologicalKernelType = None
    ) -> Dict[str, np.ndarray]:
        """
        Crea perfil morfológico multi-escala.
        
        Útil para análisis de textura y clasificación de cobertura de suelo.
        
        Args:
            image: Imagen de entrada
            base_kernel_size: Tamaño base del kernel
            num_scales: Número de escalas
            kernel_type: Tipo de kernel
            
        Returns:
            Diccionario con perfiles a cada escala
        """
        if kernel_type is None:
            kernel_type = MorphologicalKernelType.CIRCLE
        
        scales = [base_kernel_size * (2 ** i) for i in range(num_scales)]
        
        profile = {
            'original': image,
            'scales': scales,
            'opening': [],
            'closing': [],
            'gradient': [],
            'top_hat': [],
            'black_hat': []
        }
        
        for scale in scales:
            profile['opening'].append(self.open(image, scale, kernel_type))
            profile['closing'].append(self.close(image, scale, kernel_type))
            profile['gradient'].append(self.morphological_gradient(image, scale, kernel_type))
            profile['top_hat'].append(self.top_hat(image, scale, kernel_type))
            profile['black_hat'].append(self.black_hat(image, scale, kernel_type))
        
        return profile
    
    # =========================================================================
    # GUARDADO Y METADATOS
    # =========================================================================
    
    def save_result(
        self,
        image: np.ndarray,
        filename: str,
        metadata: Optional[Dict] = None
    ):
        """
        Guarda resultado con metadatos.
        
        Args:
            image: Imagen a guardar
            filename: Nombre del archivo
            metadata: Metadatos adicionales
        """
        output_path = self.output_dir / filename
        
        # Guardar imagen
        np.save(output_path.with_suffix('.npy'), image)
        
        # Guardar metadatos
        if metadata:
            metadata_path = output_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'shape': list(image.shape),
                    'dtype': str(image.dtype),
                    **metadata
                }, f, indent=2)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de procesamiento."""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reinicia estadísticas."""
        self.stats = {
            'total_operations': 0,
            'gpu_operations': 0,
            'chunked_operations': 0,
            'processing_time_ms': 0
        }


# =============================================================================
# FUNCIONES DE CONVENIENCIA
# =============================================================================

def morphological_open(
    image: np.ndarray,
    kernel_size: int = 3,
    kernel_type: str = 'circle'
) -> np.ndarray:
    """
    Función de conveniencia para apertura morfológica.
    
    Args:
        image: Imagen de entrada
        kernel_size: Tamaño del kernel
        kernel_type: Tipo de kernel ('square', 'circle', 'ellipse', 'cross')
        
    Returns:
        Imagen procesada
    """
    proc = MorphologicalProcessor()
    ktype = MorphologicalKernelType(kernel_type)
    return proc.open(image, kernel_size, ktype)


def morphological_close(
    image: np.ndarray,
    kernel_size: int = 3,
    kernel_type: str = 'circle'
) -> np.ndarray:
    """
    Función de conveniencia para cierre morfológico.
    
    Args:
        image: Imagen de entrada
        kernel_size: Tamaño del kernel
        kernel_type: Tipo de kernel
        
    Returns:
        Imagen procesada
    """
    proc = MorphologicalProcessor()
    ktype = MorphologicalKernelType(kernel_type)
    return proc.close(image, kernel_size, ktype)


def morphological_gradient(
    image: np.ndarray,
    kernel_size: int = 3,
    kernel_type: str = 'circle'
) -> np.ndarray:
    """
    Función de conveniencia para gradiente morfológico.
    
    Args:
        image: Imagen de entrada
        kernel_size: Tamaño del kernel
        kernel_type: Tipo de kernel
        
    Returns:
        Gradiente morfológico
    """
    proc = MorphologicalProcessor()
    ktype = MorphologicalKernelType(kernel_type)
    return proc.morphological_gradient(image, kernel_size, ktype)


def extract_morphology_features(
    image: np.ndarray,
    mask: Optional[np.ndarray] = None
) -> Dict[str, float]:
    """
    Función de conveniencia para extraer características morfológicas.
    
    Args:
        image: Imagen de entrada
        mask: Máscara de región
        
    Returns:
        Diccionario de características
    """
    proc = MorphologicalProcessor()
    features = proc.extract_features(image, mask)
    return features.to_dict()


def create_multi_scale_profile(
    image: np.ndarray,
    scales: List[int] = None
) -> Dict[str, List[float]]:
    """
    Función de conveniencia para perfil multi-escala.
    
    Args:
        image: Imagen de entrada
        scales: Lista de escalas
        
    Returns:
        Perfil multi-escala
    """
    proc = MorphologicalProcessor()
    return proc.extract_multi_scale_features(image, scales)


# =============================================================================
# EJEMPLO DE USO / TEST
# =============================================================================

def create_test_image(width: int = 512, height: int = 512) -> np.ndarray:
    """
    Crea imagen de prueba con formas para testing.
    
    Args:
        width: Ancho
        height: Alto
        
    Returns:
        Imagen de prueba
    """
    np.random.seed(42)
    image = np.zeros((height, width), dtype=np.uint8)
    
    # Círculo
    cv2.circle(image, (100, 100), 50, 255, -1)
    
    # Rectángulo
    cv2.rectangle(image, (200, 50), (300, 150), 200, -1)
    
    # Elipse
    cv2.ellipse(image, (400, 100), (40, 25), 0, 0, 360, 255, -1)
    
    # Línea
    cv2.line(image, (50, 200), (150, 300), 150, 5)
    
    # Polígono
    pts = np.array([[250, 220], [280, 280], [220, 280]], np.int32)
    cv2.fillPoly(image, [pts], 255)
    
    #ruido
    noise = np.random.randint(0, 50, (height, width), dtype=np.uint8)
    image = cv2.add(image, noise)
    
    return image


if __name__ == "__main__":
    print("=" * 60)
    print("MORPHOLOGICAL PROCESSOR - SKYFUSION ANALYTICS")
    print("=" * 60)
    
    # Crear procesador
    proc = MorphologicalProcessor()
    
    # Crear imagen de prueba
    print("\n[1] Creando imagen de prueba...")
    test_image = create_test_image()
    print(f"    Imagen creada: {test_image.shape}")
    
    # Test de operaciones básicas
    print("\n[2] Probando operaciones básicas...")
    
    eroded = proc.erode(test_image, kernel_size=3)
    print(f"    Erosión: {eroded.shape}, mean={np.mean(eroded):.2f}")
    
    dilated = proc.dilate(test_image, kernel_size=3)
    print(f"    Dilatación: {dilated.shape}, mean={np.mean(dilated):.2f}")
    
    opened = proc.open(test_image, kernel_size=3)
    print(f"    Apertura: {opened.shape}, mean={np.mean(opened):.2f}")
    
    closed = proc.close(test_image, kernel_size=3)
    print(f"    Cierre: {closed.shape}, mean={np.mean(closed):.2f}")
    
    # Test de operaciones avanzadas
    print("\n[3] Probando operaciones avanzadas...")
    
    gradient = proc.morphological_gradient(test_image, kernel_size=5)
    print(f"    Gradiente: {gradient.shape}, mean={np.mean(gradient):.2f}")
    
    tophat = proc.top_hat(test_image, kernel_size=5)
    print(f"    Top-Hat: {tophat.shape}, mean={np.mean(tophat):.2f}")
    
    blackhat = proc.black_hat(test_image, kernel_size=5)
    print(f"    Black-Hat: {blackhat.shape}, mean={np.mean(blackhat):.2f}")
    
    # Test de extracción de características
    print("\n[4] Extrayendo características morfológicas...")
    features = proc.extract_features(test_image)
    print(f"    Área: {features.area:.2f}")
    print(f"    Perímetro: {features.perimeter:.2f}")
    print(f"    Compacidad: {features.compactness:.4f}")
    print(f"    Circularidad: {features.circularity:.4f}")
    print(f"    Solidez: {features.solidity:.4f}")
    print(f"    Número de Euler: {features.euler_number}")
    
    # Test multi-escala
    print("\n[5] Probando perfil multi-escala...")
    multi_features = proc.extract_multi_scale_features(test_image)
    print(f"    Escalas procesadas: {len(multi_features)}")
    print(f"    Erosión (escalas): {multi_features['erosion']}")
    
    # Test de kernels
    print("\n[6] Generando elementos estructurantes...")
    for ktype in [MorphologicalKernelType.SQUARE, MorphologicalKernelType.CIRCLE, 
                  MorphologicalKernelType.CROSS, MorphologicalKernelType.DIAMOND]:
        kernel = proc.create_kernel(5, ktype)
        print(f"    {ktype.value}: {kernel.shape}, sum={np.sum(kernel)}")
    
    # Test de procesamiento chunked
    print("\n[7] Probando procesamiento simple (skip chunked para test)...")
    large_image = create_test_image(512, 512)
    result_chunked = proc.process_chunked(
        large_image,
        MorphologicalOperation.OPEN,
        chunk_size=1024,
        overlap=64
    )
    print(f"    Imagen grande: {large_image.shape}")
    print(f"    Resultado chunked: {result_chunked.shape}")
    
    # Guardar resultados
    print("\n[8] Guardando resultados...")
    proc.save_result(test_image, "test_morphological.npy", {'type': 'test'})
    proc.save_result(gradient, "test_gradient.npy", {'type': 'gradient', 'kernel_size': 5})
    print("    Resultados guardados")
    
    # Mostrar estadísticas
    print("\n[9] Estadísticas de procesamiento:")
    stats = proc.get_stats()
    for key, value in stats.items():
        print(f"    {key}: {value}")
    
    print("\n" + "=" * 60)
    print("PRUEBAS COMPLETADAS EXITOSAMENTE")
    print("=" * 60)