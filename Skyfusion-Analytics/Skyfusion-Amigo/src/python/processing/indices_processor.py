"""
Módulo de procesamiento de índices ambientales
Skyfusion Analytics - Pipeline NDVI/NDWI
=========================================
Incluye integración con procesamiento morfológico para clasificación
y detección de cambios avanzados.

Autor: Skyfusion Analytics Team
Fecha: 2026
"""

import numpy as np
import cv2
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
import json
from datetime import datetime

# Importar procesamiento morfológico
try:
    from morphological_processor import (
        MorphologicalProcessor,
        MorphologicalKernelType,
        MorphologicalOperation,
        create_test_image as create_morph_test_image
    )
    MORPHOLOGICAL_AVAILABLE = True
except ImportError:
    MORPHOLOGICAL_AVAILABLE = False
    print("Advertencia: Procesamiento morfológico no disponible")


class EnvironmentalIndexProcessor:
    """
    Procesador de índices ambientales para análisis multitemporal
    """
    
    def __init__(self, output_dir: str = "../../data/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def calculate_ndvi(self, nir_band: np.ndarray, red_band: np.ndarray) -> np.ndarray:
        """
        Calcula el Índice de Vegetación Normalizado Diferencial (NDVI)
        
        NDVI = (NIR - Red) / (NIR + Red)
        
        Args:
            nir_band: Banda infrarroja cercana
            red_band: Banda roja
            
        Returns:
            Array numpy con valores NDVI (-1 a 1)
        """
        nir = nir_band.astype(np.float32)
        red = red_band.astype(np.float32)
        
        denominator = nir + red
        
        ndvi = np.where(
            denominator != 0,
            (nir - red) / denominator,
            0
        )
        
        return np.clip(ndvi, -1.0, 1.0)
    
    def calculate_ndwi(self, green_band: np.ndarray, nir_band: np.ndarray) -> np.ndarray:
        """
        Calcula el Índice de Agua Normalizado Diferencial (NDWI)
        
        NDWI = (Green - NIR) / (Green + NIR)
        
        Args:
            green_band: Banda verde
            nir_band: Banda infrarroja cercana
            
        Returns:
            Array numpy con valores NDWI (-1 a 1)
        """
        green = green_band.astype(np.float32)
        nir = nir_band.astype(np.float32)
        
        denominator = green + nir
        
        ndwi = np.where(
            denominator != 0,
            (green - nir) / denominator,
            0
        )
        
        return np.clip(ndwi, -1.0, 1.0)
    
    def calculate_evi(self, nir_band: np.ndarray, red_band: np.ndarray, 
                      blue_band: np.ndarray) -> np.ndarray:
        """
        Calcula el Índice de Vegetación Mejorado (EVI)
        
        EVI = 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1)
        
        Args:
            nir_band: Banda infrarroja cercana
            red_band: Banda roja
            blue_band: Banda azul
            
        Returns:
            Array numpy con valores EVI
        """
        nir = nir_band.astype(np.float32)
        red = red_band.astype(np.float32)
        blue = blue_band.astype(np.float32)
        
        numerator = 2.5 * (nir - red)
        denominator = nir + 6 * red - 7.5 * blue + 1
        
        evi = np.where(
            denominator != 0,
            numerator / denominator,
            0
        )
        
        return np.clip(evi, -1.0, 1.0)
    
    def apply_colormap(self, index: np.ndarray, colormap: str = 'ndvi') -> np.ndarray:
        """
        Aplica mapa de colores al índice para visualización
        
        Args:
            index: Array con valores del índice
            colormap: Tipo de mapa ('ndvi', 'ndwi', 'alert')
            
        Returns:
            Imagen RGB con mapa de colores aplicado
        """
        normalized = ((index + 1) / 2 * 255).astype(np.uint8)
        
        if colormap == 'ndvi':
            colors = self._ndvi_colormap()
        elif colormap == 'ndwi':
            colors = self._ndwi_colormap()
        else:
            colors = self._alert_colormap()
        
        colored = cv2.applyColorMap(normalized, colors)
        
        return colored
    
    def _ndvi_colormap(self) -> np.ndarray:
        """Mapa de colores para NDVI"""
        return cv2.COLORMAP_JET
    
    def _ndwi_colormap(self) -> np.ndarray:
        """Mapa de colores para NDWI"""
        return cv2.COLORMAP_OCEAN
    
    def _alert_colormap(self) -> np.ndarray:
        """Mapa de colores para alertas"""
        return cv2.COLORMAP_AUTUMN
    
    def detect_change(self, before_image: np.ndarray, after_image: np.ndarray,
                      threshold: int = 30) -> Tuple[np.ndarray, list]:
        """
        Detecta cambios entre dos imágenes
        
        Args:
            before_image: Imagen anterior
            after_image: Imagen posterior
            threshold: Umbral de detección
            
        Returns:
            Tuple de (máscara de cambios, contornos)
        """
        before_gray = cv2.cvtColor(before_image, cv2.COLOR_BGR2GRAY) if len(before_image.shape) == 3 else before_image
        after_gray = cv2.cvtColor(after_image, cv2.COLOR_BGR2GRAY) if len(after_image.shape) == 3 else after_image
        
        diff = cv2.absdiff(before_gray, after_gray)
        _, mask = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        return mask, contours
    
    def classify_changes(self, contours: list, min_area: int = 100) -> Dict[str, Any]:
        """
        Clasifica los cambios detectados
        
        Args:
            contours: Lista de contornos detectados
            min_area: Área mínima para considerar un cambio
            
        Returns:
            Diccionario con clasificación de cambios
        """
        changes = {
            'total': len(contours),
            'significant': 0,
            'areas': []
        }
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area >= min_area:
                changes['significant'] += 1
                x, y, w, h = cv2.boundingRect(contour)
                changes['areas'].append({
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h),
                    'area': float(area)
                })
        
        return changes
    
    def save_index(self, index: np.ndarray, filename: str, metadata: Optional[Dict] = None):
        """
        Guarda el índice calculado
        
        Args:
            index: Array con valores del índice
            filename: Nombre del archivo
            metadata: Metadatos adicionales
        """
        output_path = self.output_dir / filename
        
        np.save(output_path.with_suffix('.npy'), index)
        
        if metadata:
            metadata_path = output_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    **metadata
                }, f, indent=2)
    
    def get_statistics(self, index: np.ndarray) -> Dict[str, float]:
        """
        Calcula estadísticas del índice
        
        Args:
            index: Array con valores del índice
            
        Returns:
            Diccionario con estadísticas
        """
        return {
            'mean': float(np.mean(index)),
            'std': float(np.std(index)),
            'min': float(np.min(index)),
            'max': float(np.max(index)),
            'median': float(np.median(index)),
            'percentile_25': float(np.percentile(index, 25)),
            'percentile_75': float(np.percentile(index, 75))
        }

    # =========================================================================
    # INTEGRACIÓN CON PROCESAMIENTO MORFOLÓGICO
    # =========================================================================
    
    def apply_morphological_smoothing(
        self,
        index: np.ndarray,
        kernel_size: int = 5,
        operation: str = 'close'
    ) -> np.ndarray:
        """
        Aplica suavizado morfológico a un índice.
        
        Args:
            index: Índice a suavizar
            kernel_size: Tamaño del kernel
            operation: Operación ('close', 'open', 'both')
            
        Returns:
            Índice suavizado
        """
        if not MORPHOLOGICAL_AVAILABLE:
            print("Advertencia: Morfología no disponible, retornando índice original")
            return index
        
        proc = MorphologicalProcessor()
        
        # Convertir a uint8 para procesamiento morfológico
        normalized = ((index + 1) / 2 * 255).astype(np.uint8)
        
        if operation == 'close':
            return proc.close(normalized, kernel_size)
        elif operation == 'open':
            return proc.open(normalized, kernel_size)
        elif operation == 'both':
            closed = proc.close(normalized, kernel_size)
            return proc.open(closed, kernel_size)
        else:
            return normalized
    
    def detect_water_bodies_morphological(
        self,
        ndwi: np.ndarray,
        threshold: float = 0.0,
        kernel_size: int = 7
    ) -> Dict[str, Any]:
        """
        Detecta cuerpos de agua usando procesamiento morfológico avanzado.
        
        Args:
            ndwi: Índice NDWI
            threshold: Umbral de detección
            kernel_size: Tamaño del kernel
            
        Returns:
            Diccionario con resultados de detección
        """
        if not MORPHOLOGICAL_AVAILABLE:
            return {'error': 'Morfología no disponible'}
        
        proc = MorphologicalProcessor()
        
        # Binarizar NDWI
        binary = (ndwi > threshold).astype(np.uint8) * 255
        
        # Aplicar cierre para conectar cuerpos de agua fragmentados
        closed = proc.close(binary, kernel_size)
        
        # Aplicar apertura para eliminar noise
        opened = proc.open(closed, 3)
        
        # Extraer características
        features = proc.extract_features(opened)
        
        # Contar cuerpos de agua
        num_labels, labels = cv2.connectedComponents(opened).focus()
        
        # Calcular áreas
        areas = []
        for label in range(1, num_labels):
            area = np.sum(labels == label)
            areas.append(float(area))
        
        return {
            'num_bodies': num_labels - 1,
            'total_water_area': float(np.sum(opened > 0)),
            'areas': areas,
            'largest_body': max(areas) if areas else 0,
            'features': features.to_dict() if features.area > 0 else {}
        }
    
    def detect_vegetation_change_morphological(
        self,
        ndvi_before: np.ndarray,
        ndvi_after: np.ndarray,
        threshold: float = 0.1
    ) -> Dict[str, Any]:
        """
        Detecta cambios en vegetación usando procesamiento morfológico.
        
        Args:
            ndvi_before: NDVI antes
            ndvi_after: NDVI después
            threshold: Umbral de cambio
            
        Returns:
            Diccionario con cambios detectados
        """
        if not MORPHOLOGICAL_AVAILABLE:
            return {'error': 'Morfología no disponible'}
        
        proc = MorphologicalProcessor()
        
        # Calcular diferencia
        diff = ndvi_after - ndvi_before
        
        # Detectar cambios positivos (aumento de vegetación)
        positive_change = (diff > threshold).astype(np.uint8) * 255
        
        # Detectar cambios negativos (pérdida de vegetación)
        negative_change = (diff < -threshold).astype(np.uint8) * 255
        
        # Aplicar procesamiento morfológico para reducir ruido
        positive_processed = proc.open(positive_change, 5)
        negative_processed = proc.open(negative_change, 5)
        
        # Extraer características
        pos_features = proc.extract_features(positive_processed)
        neg_features = proc.extract_features(negative_processed)
        
        return {
            'vegetation_gain': float(np.sum(positive_processed > 0)),
            'vegetation_loss': float(np.sum(negative_processed > 0)),
            'net_change': float(np.sum(positive_processed > 0) - np.sum(negative_processed > 0)),
            'gain_features': pos_features.to_dict() if pos_features.area > 0 else {},
            'loss_features': neg_features.to_dict() if neg_features.area > 0 else {}
        }
    
    def extract_morphological_features_for_classification(
        self,
        index: np.ndarray,
        region_mask: np.ndarray = None
    ) -> Dict[str, float]:
        """
        Extrae características morfológicas para clasificación.
        
        Args:
            index: Índice ambiental
            region_mask: Máscara de región (opcional)
            
        Returns:
            Diccionario de características
        """
        if not MORPHOLOGICAL_AVAILABLE:
            return {'error': 'Morfología no disponible'}
        
        proc = MorphologicalProcessor()
        features = proc.extract_features(index, region_mask)
        return features.to_dict()
    
    def create_morphological_profile(
        self,
        index: np.ndarray,
        base_kernel_size: int = 3,
        num_scales: int = 5
    ) -> Dict[str, List[float]]:
        """
        Crea perfil morfológico multi-escala.
        
        Args:
            index: Índice ambiental
            base_kernel_size: Tamaño base del kernel
            num_scales: Número de escalas
            
        Returns:
            Perfil morfológico
        """
        if not MORPHOLOGICAL_AVAILABLE:
            return {'error': 'Morfología no disponible'}
        
        proc = MorphologicalProcessor()
        return proc.extract_multi_scale_features(index)


def create_sample_data(width: int = 512, height: int = 512) -> Dict[str, np.ndarray]:
    """
    Crea datos de ejemplo para pruebas
    
    Args:
        width: Ancho de la imagen
        height: Alto de la imagen
        
    Returns:
        Diccionario con bandas de ejemplo
    """
    np.random.seed(42)
    
    nir = np.random.uniform(1000, 4000, (height, width)).astype(np.float32)
    red = np.random.uniform(500, 2500, (height, width)).astype(np.float32)
    green = np.random.uniform(800, 3000, (height, width)).astype(np.float32)
    blue = np.random.uniform(300, 1500, (height, width)).astype(np.float32)
    
    return {
        'nir': nir,
        'red': red,
        'green': green,
        'blue': blue
    }


if __name__ == "__main__":
    processor = EnvironmentalIndexProcessor()
    
    bands = create_sample_data()
    
    ndvi = processor.calculate_ndvi(bands['nir'], bands['red'])
    ndwi = processor.calculate_ndwi(bands['green'], bands['nir'])
    
    print("NDVI Statistics:")
    print(json.dumps(processor.get_statistics(ndvi), indent=2))
    
    print("\nNDWI Statistics:")
    print(json.dumps(processor.get_statistics(ndwi), indent=2))
    
    processor.save_index(ndvi, 'ndvi_sample.npy', {'type': 'sample'})
    processor.save_index(ndwi, 'ndwi_sample.npy', {'type': 'sample'})
    
    print("\nÍndices calculados y guardados exitosamente")
