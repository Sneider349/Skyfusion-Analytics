"""
Módulo de Clasificación de Cobertura de Suelo
Skyfusion Analytics - Clasificación usando Operaciones Morfológicas
================================================================

Clasificación de cobertura de suelo usando características morfológicas
derivadas de índices espectrales (NDVI, NDWI, EVI).

Clases de clasificación:
- agua (cuerpos de agua)
- vegetacion_densa (vegetación densa)
- vegetacion_moderada (vegetación moderada)
- vegetacion_escasa (vegetación baja/escasa)
- suelo_desnudo (suelo sin vegetación)
- area_urbana (zonas urbanas)
- otro (otros)

Autor: Skyfusion Analytics Team
Fecha: 2026
"""

import numpy as np
import cv2
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

try:
    from morphological_processor import (
        MorphologicalProcessor,
        MorphologicalKernelType,
        MorphologicalOperation,
        create_test_image as create_morph_test_image
    )
    from indices_processor import EnvironmentalIndexProcessor
    MORPHOLOGICAL_AVAILABLE = True
except ImportError:
    MORPHOLOGICAL_AVAILABLE = False
    print("Advertencia: Procesamiento morfológico no disponible")


class LandCoverClass(Enum):
    """Clases de cobertura de suelo."""
    AGUA = "agua"
    VEGETACION_DENSA = "vegetacion_densa"
    VEGETACION_MODERADA = "vegetacion_moderada"
    VEGETACION_ESCASA = "vegetacion_escasa"
    SUELO_DESNUDO = "suelo_desnudo"
    AREA_URBANA = "area_urbana"
    OTRO = "otro"


@dataclass
class ClassificationResult:
    """Resultado de clasificación."""
    classification_map: np.ndarray
    class_labels: Dict[int, str]
    class_areas: Dict[str, int]
    class_percentages: Dict[str, float]
    confidence_map: Optional[np.ndarray] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'class_labels': self.class_labels,
            'class_areas': self.class_areas,
            'class_percentages': self.class_percentages,
            'total_pixels': int(sum(self.class_areas.values()))
        }


@dataclass
class ClassificationConfig:
    """Configuración para clasificación."""
    # Thresholds NDVI
    ndvi_soil: float = 0.1      # < 0.1 = suelo
    ndvi_sparse: float = 0.3     # 0.1-0.3 = vegetacion escasa
    ndvi_moderate: float = 0.6   # 0.3-0.6 = vegetacion moderada
    ndvi_dense: float = 0.6       # > 0.6 = vegetacion densa
    
    # Thresholds NDWI
    ndwi_water: float = 0.2       # > 0.2 = agua
    
    # Thresholds EVI (opcional)
    evi_soil: float = 0.1
    evi_urban: float = 0.5
    
    # Tamaño de kernel morfológico
    kernel_size: int = 5
    kernel_type: str = "circle"
    
    # Post-procesamiento
    min_region_area: int = 100
    use_morphological_filtering: bool = True
    
    # Resolución espacial (metros por pixel)
    resolution: float = 30.0
    
    def to_dict(self) -> Dict[str, float]:
        """Convierte a diccionario."""
        return {
            'ndvi_soil': self.ndvi_soil,
            'ndvi_sparse': self.ndvi_sparse,
            'ndvi_moderate': self.ndvi_moderate,
            'ndvi_dense': self.ndvi_dense,
            'ndwi_water': self.ndwi_water,
            'kernel_size': self.kernel_size
        }


class LandCoverClassifier:
    """
    Clasificador de cobertura de suelo usando procesamiento morfológico.
    
    Utiliza índices espectrales combinados con operaciones morfológicas
    para clasificación robusta de cobertura de suelo.
    """
    
    # Mapeo de clases a valores
    CLASS_VALUES = {
        0: 'agua',
        1: 'vegetacion_densa',
        2: 'vegetacion_moderada', 
        3: 'vegetacion_escasa',
        4: 'suelo_desnudo',
        5: 'area_urbana',
        6: 'otro'
    }
    
    # Colores para visualización (BGR)
    CLASS_COLORS = {
        'agua': (255, 0, 0),           # Azul
        'vegetacion_densa': (0, 100, 0),  # Verde oscuro
        'vegetacion_moderada': (0, 200, 0), # Verde
        'vegetacion_escasa': (0, 255, 0),   # Verde claro
        'suelo_desnudo': (139, 69, 19),    # Marrón
        'area_urbana': (128, 128, 128),   # Gris
        'otro': (0, 0, 0)            # Negro
    }
    
    def __init__(
        self,
        output_dir: str = "../../data/output/classification",
        config: ClassificationConfig = None
    ):
        """
        Inicializa el clasificador.
        
        Args:
            output_dir: Directorio para guardar resultados
            config: Configuración de clasificación
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = config or ClassificationConfig()
        
        # Inicializar procesadores
        if MORPHOLOGICAL_AVAILABLE:
            self.morph_processor = MorphologicalProcessor()
            self.index_processor = EnvironmentalIndexProcessor()
        else:
            self.morph_processor = None
            self.index_processor = None
    
    def classify(
        self,
        nir_band: np.ndarray,
        red_band: np.ndarray,
        green_band: Optional[np.ndarray] = None,
        blue_band: Optional[np.ndarray] = None
    ) -> ClassificationResult:
        """
        Clasifica cobertura de suelo usando bandas espectrales.
        
        Args:
            nir_band: Banda NIR (infrarrojo cercano)
            red_band: Banda roja
            green_band: Banda verde (opcional)
            blue_band: Banda azul (opcional)
            
        Returns:
            ClassificationResult con mapa de clasificación
        """
        if not MORPHOLOGICAL_AVAILABLE:
            raise RuntimeError("Módulo morfológico no disponible")
        
        # Calcular índices
        ndvi = self.index_processor.calculate_ndvi(nir_band, red_band)
        
        ndwi = None
        if green_band is not None:
            ndwi = self.index_processor.calculate_ndwi(green_band, nir_band)
        
        evi = None
        if green_band is not None and blue_band is not None:
            evi = self.index_processor.calculate_evi(nir_band, red_band, blue_band)
        
        # Aplicar post-procesamiento morfológico si está habilitado
        if self.config.use_morphological_filtering:
            # Suavizar NDVI
            ndvi_smooth = self.index_processor.apply_morphological_smoothing(
                ndvi,
                self.config.kernel_size,
                'both'
            )
            ndvi = (ndvi_smooth.astype(np.float32) / 255) * 2 - 1
        
        # Crear mapa de clasificación
        classification_map = self._create_classification_map(ndvi, ndwi, evi)
        
        # Filtrar regiones pequeñas
        if self.config.use_morphological_filtering:
            classification_map = self._filter_small_regions(classification_map)
        
        # Calcular áreas
        class_areas, class_percentages = self._calculate_class_areas(classification_map)
        
        return ClassificationResult(
            classification_map=classification_map,
            class_labels=self.CLASS_VALUES,
            class_areas=class_areas,
            class_percentages=class_percentages
        )
    
    def classify_from_indices(
        self,
        ndvi: np.ndarray,
        ndwi: Optional[np.ndarray] = None,
        evi: Optional[np.ndarray] = None
    ) -> ClassificationResult:
        """
        Clasifica usando índices pre-calculados.
        
        Args:
            ndvi: Índice NDVI
            ndwi: Índice NDWI (opcional)
            evi: Índice EVI (opcional)
            
        Returns:
            ClassificationResult
        """
        if not MORPHOLOGICAL_AVAILABLE:
            raise RuntimeError("Módulo morfológico no disponible")
        
        # Post-procesamiento morfológico
        if self.config.use_morphological_filtering:
            ndvi_smooth = self.index_processor.apply_morphological_smoothing(
                ndvi,
                self.config.kernel_size,
                'both'
            )
            ndvi = (ndvi_smooth.astype(np.float32) / 255) * 2 - 1
        
        # Clasificar
        classification_map = self._create_classification_map(ndvi, ndwi, evi)
        
        # Filtrar
        if self.config.use_morphological_filtering:
            classification_map = self._filter_small_regions(classification_map)
        
        # Calcular áreas
        class_areas, class_percentages = self._calculate_class_areas(classification_map)
        
        return ClassificationResult(
            classification_map=classification_map,
            class_labels=self.CLASS_VALUES,
            class_areas=class_areas,
            class_percentages=class_percentages
        )
    
    def _create_classification_map(
        self,
        ndvi: np.ndarray,
        ndwi: Optional[np.ndarray],
        evi: Optional[np.ndarray]
    ) -> np.ndarray:
        """
        Crea mapa de clasificación.
        
        Args:
            ndvi: Índice NDVI
            ndwi: Índice NDWI
            evi: Índice EVI
            
        Returns:
            Mapa de clasificación
        """
        h, w = ndvi.shape[:2]
        classification = np.full((h, w), 6, dtype=np.uint8)  # Default: 'otro'
        
        # 1. Agua (NDWI > threshold)
        if ndwi is not None:
            water_mask = ndwi > self.config.ndwi_water
            classification[water_mask] = 0
        
        # 2. Vegetación según NDVI (en áreas no agua)
        ndvi_flat = ndvi.flatten()
        for i in range(len(ndvi_flat)):
            y, x = i // w, i % w
            if classification[y, x] == 0:  # Skip si es agua
                continue
            
            val = ndvi_flat[i]
            if val < self.config.ndvi_soil:
                classification[y, x] = 4  # suelo_desnudo
            elif val < self.config.ndvi_sparse:
                classification[y, x] = 3  # vegetacion_escasa
            elif val < self.config.ndvi_moderate:
                classification[y, x] = 2  # vegetacion_moderada
            else:
                classification[y, x] = 1  # vegetacion_densa
        
        # 3. Detectar áreas urbanas (alto EVI + bajo NDVI)
        if evi is not None:
            urban_mask = (evi > self.config.evi_urban) & (ndvi < self.config.ndvi_soil)
            classification[urban_mask] = 5  # area_urbana
        
        return classification
    
    def _filter_small_regions(self, classification_map: np.ndarray) -> np.ndarray:
        """
        Filtra regiones pequeñas usando attribute filtering.
        
        Args:
            classification_map: Mapa de clasificación
            
        Returns:
            Mapa filtrado
        """
        filtered = classification_map.copy()
        
        for class_value in range(7):
            class_mask = (classification_map == class_value).astype(np.uint8) * 255
            
            # Aplicar attribute filtering
            filtered_class = self.morph_processor.attribute_filtering(
                class_mask,
                min_area=self.config.min_region_area,
                output_value=class_value
            )
            
            filtered[filtered_class == class_value] = class_value
        
        return filtered
    
    def _calculate_class_areas(
        self,
        classification_map: np.ndarray
    ) -> Tuple[Dict[str, int], Dict[str, float]]:
        """
        Calcula áreas de cada clase.
        
        Args:
            classification_map: Mapa de clasificación
            
        Returns:
            Tupla de (áreas en píxeles, porcentajes)
        """
        total_pixels = classification_map.size
        
        class_areas = {}
        class_percentages = {}
        
        for class_id, class_name in self.CLASS_VALUES.items():
            area = int(np.sum(classification_map == class_id))
            class_areas[class_name] = area
            class_percentages[class_name] = float(area / total_pixels * 100)
        
        return class_areas, class_percentages
    
    def create_visualization(
        self,
        classification_result: ClassificationResult
    ) -> np.ndarray:
        """
        Crea imagen de visualización a color.
        
        Args:
            classification_result: Resultado de clasificación
            
        Returns:
            Imagen RGB
        """
        classification_map = classification_result.classification_map
        
        # Crear imagen a color
        h, w = classification_map.shape[:2]
        visualization = np.zeros((h, w, 3), dtype=np.uint8)
        
        for class_id, class_name in self.CLASS_VALUES.items():
            mask = classification_map == class_id
            visualization[mask] = self.CLASS_COLORS[class_name]
        
        return visualization
    
    def extract_class_features(
        self,
        classification_result: ClassificationResult,
        image: np.ndarray
    ) -> Dict[str, Dict[str, float]]:
        """
        Extrae características morfológicas por clase.
        
        Args:
            classification_result: Resultado de clasificación
            image: Imagen original
            
        Returns:
            Características por clase
        """
        features_by_class = {}
        
        for class_id, class_name in self.CLASS_VALUES.items():
            # Crear máscara para esta clase
            mask = (classification_result.classification_map == class_id).astype(np.uint8)
            
            if np.sum(mask) == 0:
                continue
            
            # Extraer características morfológicas
            features = self.morph_processor.extract_features(image, mask)
            features_by_class[class_name] = features.to_dict()
        
        return features_by_class
    
    def detect_change_between(
        self,
        before_result: ClassificationResult,
        after_result: ClassificationResult
    ) -> Dict[str, Any]:
        """
        Detecta cambios entre dos clasificaciones.
        
        Args:
            before_result: Clasificación anterior
            after_result: Clasificación posterior
            
        Returns:
            Diccionario de cambios
        """
        # Calcular transición
        changes = {}
        
        for before_class in self.CLASS_VALUES.values():
            for after_class in self.CLASS_VALUES.values():
                key = f"{before_class}_to_{after_class}"
                
                # Crear máscaras
                before_mask = before_result.classification_map == list(self.CLASS_VALUES.keys())[
                    list(self.CLASS_VALUES.values()).index(before_class)
                ]
                after_mask = after_result.classification_map == list(self.CLASS_VALUES.keys())[
                    list(self.CLASS_VALUES.values()).index(after_class)
                ]
                
                # Calcular área de transición
                transition = np.sum(before_mask & after_mask)
                if transition > 0:
                    changes[key] = int(transition)
        
        # Calcular cambio neto por clase
        net_changes = {}
        for class_name in self.CLASS_VALUES.values():
            before_area = before_result.class_areas.get(class_name, 0)
            after_area = after_result.class_areas.get(class_name, 0)
            net_changes[class_name] = int(after_area - before_area)
        
        return {
            'transitions': changes,
            'net_changes': net_changes,
            'total_changed_pixels': sum(changes.values())
        }
    
    def save_result(
        self,
        result: ClassificationResult,
        filename: str,
        metadata: Optional[Dict] = None
    ):
        """
        Guarda resultado de clasificación.
        
        Args:
            result: ClassificationResult
            filename: Nombre del archivo
            metadata: Metadatos adicionales
        """
        output_path = self.output_dir / filename
        
        np.save(output_path.with_suffix('.npy'), result.classification_map)
        
        if metadata:
            metadata_path = output_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    **result.to_dict(),
                    **metadata
                }, f, indent=2)


# =============================================================================
# CLASIFICADOR ESPECIALIZADO PARA ANÁLISIS DE CAMBIOS
# =============================================================================

class ChangeDetectionClassifier:
    """
    Clasificador especializado para detección de cambios temporales.
    
    Compara clasificaciones en diferentes fechas para detectar
    cambios en la cobertura de suelo.
    """
    
    def __init__(self, classifier: LandCoverClassifier = None):
        """
        Inicializa el detector de cambios.
        
        Args:
            classifier: Clasificador de cobertura (opcional)
        """
        self.classifier = classifier or LandCoverClassifier()
    
    def detect_deforestation(
        self,
        nir_before: np.ndarray,
        red_before: np.ndarray,
        nir_after: np.ndarray,
        red_after: np.ndarray
    ) -> Dict[str, Any]:
        """
        Detecta deforestación entre dos fechas.
        
        Args:
            nir_before: NIR antes
            red_before: Rojo antes
            nir_after: NIR después
            red_after: Rojo después
            
        Returns:
            Resultados de detección
        """
        # Calcular NDVI
        ndvi_before = self.classifier.index_processor.calculate_ndvi(nir_before, red_before)
        ndvi_after = self.classifier.index_processor.calculate_ndvi(nir_after, red_after)
        
        # Usar el procesador morfológico para detección de cambios
        change_result = self.classifier.index_processor.detect_vegetation_change_morphological(
            ndvi_before,
            ndvi_after,
            threshold=0.15  # 15% cambio significativo
        )
        
        return change_result
    
    def detect_urban_expansion(
        self,
        nir_before: np.ndarray,
        red_before: np.ndarray,
        green_before: np.ndarray,
        nir_after: np.ndarray,
        red_after: np.ndarray,
        green_after: np.ndarray
    ) -> Dict[str, Any]:
        """
        Detecta expansión urbana.
        
        Args:
            nir_before, red_before, green_before: Bandas antes
            nir_after, red_after, green_after: Bandas después
            
        Returns:
            Resultados de detección
        """
        # Calcular NDVI y NDWI
        ndvi_before = self.classifier.index_processor.calculate_ndvi(nir_before, red_before)
        ndwi_before = self.classifier.index_processor.calculate_ndwi(green_before, nir_before)
        
        ndvi_after = self.classifier.index_processor.calculate_ndvi(nir_after, red_after)
        ndwi_after = self.classifier.index_processor.calculate_ndwi(green_after, nir_after)
        
        # Detectar áreas que cambiaron de vegetación a urbano
        urban_before = (ndvi_before < 0.2) & (ndwi_before < 0.1)
        urban_after = (ndvi_after < 0.2) & (ndwi_after < 0.1)
        
        expansion = urban_after & ~urban_before
        
        return {
            'urban_expansion_pixels': int(np.sum(expansion)),
            'expansion_percentage': float(np.sum(expansion) / expansion.size * 100),
            'new_urban_area_km2': float(np.sum(expansion) * 30 * 30 / 1e6)  # 30m pixels
        }
    
    def detect_water_body_changes(
        self,
        green_before: np.ndarray,
        nir_before: np.ndarray,
        green_after: np.ndarray,
        nir_after: np.ndarray
    ) -> Dict[str, Any]:
        """
        Detecta cambios en cuerpos de agua.
        
        Args:
            green_before, nir_before: Bandas antes
            green_after, nir_after: Bandas después
            
        Returns:
            Resultados de detección
        """
        # Calcular NDWI
        ndwi_before = self.classifier.index_processor.calculate_ndwi(green_before, nir_before)
        ndwi_after = self.classifier.index_processor.calculate_ndwi(green_after, nir_after)
        
        # Detectar cambios
        water_before = ndwi_before > 0.2
        water_after = ndwi_after > 0.2
        
        water_gain = water_after & ~water_before
        water_loss = water_before & ~water_after
        
        return {
            'water_gain_pixels': int(np.sum(water_gain)),
            'water_loss_pixels': int(np.sum(water_loss)),
            'net_change_pixels': int(np.sum(water_gain) - np.sum(water_loss)),
            'water_gain_km2': float(np.sum(water_gain) * 30 * 30 / 1e6),
            'water_loss_km2': float(np.sum(water_loss) * 30 * 30 / 1e6),
            'net_change_km2': float((np.sum(water_gain) - np.sum(water_loss)) * 30 * 30 / 1e6)
        }


# =============================================================================
# EJEMPLO DE USO
# =============================================================================

def create_sample_classification_data(
    width: int = 512,
    height: int = 512
) -> Dict[str, np.ndarray]:
    """
    Crea datos de ejemplo para clasificación.
    
    Args:
        width: Ancho
        height: Alto
        
    Returns:
        Diccionario con bandas
    """
    np.random.seed(42)
    
    # Crear patrones típicos
    y, x = np.ogrid[:height, :width]
    
    # NIR: más alto en vegetación
    nir = np.random.uniform(2000, 4000, (height, width)).astype(np.float32)
    nir[((x - 200)**2 + (y - 200)**2) < 50**2] = 3500  # Vegetación densa
    nir[((x - 350)**2 + (y - 300)**2) < 80**2] = 3000   # Vegetación moderada
    
    # Red: más bajo en vegetación
    red = np.random.uniform(500, 2000, (height, width)).astype(np.float32)
    red[((x - 200)**2 + (y - 200)**2) < 50**2] = 800   # Vegetación densa
    red[((x - 350)**2 + (y - 300)**2) < 80**2] = 1200  # Vegetación moderada
    
    # Green: alto para agua
    green = np.random.uniform(1000, 3000, (height, width)).astype(np.float32)
    green[((x - 400)**2 + (y - 100)**2) < 40**2] = 3500  # Agua
    
    # Blue
    blue = np.random.uniform(300, 1500, (height, width)).astype(np.float32)
    
    return {
        'nir': nir,
        'red': red,
        'green': green,
        'blue': blue
    }


if __name__ == "__main__":
    print("=" * 60)
    print("CLASIFICADOR DE COBERTURA DE SUELO")
    print("Skyfusion Analytics - Morfological Classification")
    print("=" * 60)
    
    if not MORPHOLOGICAL_AVAILABLE:
        print("ERROR: Módulo morfológico no disponible")
        exit(1)
    
    # Crear clasificador
    classifier = LandCoverClassifier()
    change_detector = ChangeDetectionClassifier(classifier)
    
    # Crear datos de prueba
    print("\n[1] Creando datos de prueba...")
    bands = create_sample_classification_data()
    
    # Clasificar
    print("[2] Clasificando cobertura de suelo...")
    result = classifier.classify(
        bands['nir'],
        bands['red'],
        bands['green'],
        bands['blue']
    )
    
    print("\n[3] Resultados de clasificación:")
    print("    Áreas por clase:")
    for class_name, area in result.class_areas.items():
        pct = result.class_percentages[class_name]
        print(f"        {class_name}: {area} píxeles ({pct:.1f}%)")
    
    # Crear visualización
    print("\n[4] Creando visualización...")
    viz = classifier.create_visualization(result)
    print(f"    Visualización: {viz.shape}")
    
    # Detectar cambios (simulado)
    print("\n[5] Simulando detección de cambios...")
    bands_after = {
        'nir': bands['nir'] * 0.9,  # Reducción simulada
        'red': bands['red'] * 1.1,
        'green': bands['green']
    }
    
    result_after = classifier.classify(
        bands_after['nir'],
        bands_after['red'],
        bands_after['green'],
        bands['blue']
    )
    
    changes = change_detector.detect_deforestation(
        bands['nir'], bands['red'],
        bands_after['nir'], bands_after['red']
    )
    
    print(f"    Vegetación ganada: {changes.get('vegetation_gain', 0):.0f}")
    print(f"    Vegetación perdida: {changes.get('vegetation_loss', 0):.0f}")
    
    # Guardar resultado
    print("\n[6] Guardando resultados...")
    classifier.save_result(result, "classification_sample.npy", {'type': 'sample'})
    print("    Resultados guardados")
    
    print("\n" + "=" * 60)
    print("CLASIFICACIÓN COMPLETADA")
    print("=" * 60)