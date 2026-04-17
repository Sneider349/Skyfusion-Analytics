"""
Módulo de Cálculo de Métricas Morfométricas Georreferenciadas
=============================================================

Proporciona funcionalidad para calcular métricas morfométricas (área, perímetro,
índices de forma) en metros reales sobre el terreno, transformando datos
espaciales al CRS apropiado.

Este módulo complementa el morphological_processor.py existente añadiendo:
- Integración con transformación de proyecciones CRS
- Conversión precisa de píxeles a metros
- Manejo de sub-zonas para áreas extensas
- Validación de unidades de salida

Autor: Skyfusion Analytics Team
Fecha: 2026
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime

import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from scipy.ndimage import label as scipy_label

from crs_transformer import (
    CRSTransformer,
    CRSTransformConfig,
    BoundingBox,
    ScaleFactor,
    SubArea,
    create_bbox_from_coords,
)


@dataclass
class GeoMorphologicalMetrics:
    """Métricas morfométricas con unidades geoespaciales."""
    area_m2: float = 0.0
    area_km2: float = 0.0
    area_ha: float = 0.0
    perimeter_m: float = 0.0
    perimeter_km: float = 0.0
    compactness_index: float = 0.0
    circularity_index: float = 0.0
    rectangularity_index: float = 0.0
    elongation_index: float = 0.0
    solidity: float = 0.0
    eccentricity: float = 0.0
    
    bounding_box_m: Optional[Tuple[float, float]] = None
    centroid_m: Optional[Tuple[float, float]] = None
    
    crs_used: Optional[str] = None
    scale_factor_m_per_px: Optional[float] = None
    source_bbox: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'area_m2': round(self.area_m2, 4),
            'area_km2': round(self.area_km2, 4),
            'area_ha': round(self.area_ha, 4),
            'perimeter_m': round(self.perimeter_m, 4),
            'perimeter_km': round(self.perimeter_km, 4),
            'compactness_index': round(self.compactness_index, 6),
            'circularity_index': round(self.circularity_index, 6),
            'rectangularity_index': round(self.rectangularity_index, 6),
            'elongation_index': round(self.elongation_index, 6),
            'solidity': round(self.solidity, 6),
            'eccentricity': round(self.eccentricity, 6),
            'bounding_box_m': self.bounding_box_m,
            'centroid_m': self.centroid_m,
            'crs_used': self.crs_used,
            'scale_factor_m_per_px': self.scale_factor_m_per_px,
            'source_bbox': self.source_bbox
        }


@dataclass
class SegmentMetrics:
    """Métricas para un segmento individual."""
    label: int
    area_m2: float
    perimeter_m: float
    centroid_m: Tuple[float, float]
    bbox_m: Tuple[float, float, float, float]
    compactness: float
    solidity: float
    is_valid: bool = True
    error_message: Optional[str] = None


class GeoMorphologicalCalculator:
    """
    Calculador de métricas morfométricas georreferenciadas.
    
    Calcula métricas morfométricas en metros reales sobre el terreno
    usando transformación CRS y factores de escala.
    
    Attributes:
        crs_transformer: Transformador CRS para reproyecciones
        scale_factor: Factor de escala actual
        config: Configuración de transformación
    """
    
    def __init__(
        self,
        config: Optional[CRSTransformConfig] = None,
        output_dir: Optional[str] = None
    ):
        """
        Inicializa el calculador georreferenciado.
        
        Args:
            config: Configuración de transformación CRS
            output_dir: Directorio para guardar resultados
        """
        self.crs_transformer = CRSTransformer(
            config=config,
            output_dir=output_dir
        )
        self.scale_factor: Optional[ScaleFactor] = None
        self.config = config or CRSTransformConfig()
        self._current_sub_area: Optional[SubArea] = None
        self._segment_cache: Dict[int, np.ndarray] = {}
    
    def setup_crs(
        self,
        bbox: Union[BoundingBox, List[float]],
        pixel_resolution_deg: Optional[float] = None,
        prefer_equal_area: bool = False
    ) -> str:
        """
        Configura el CRS óptimo para el área de estudio.
        
        Args:
            bbox: Caja delimitadora o [min_lon, min_lat, max_lon, max_lat]
            pixel_resolution_deg: Resolución de píxel en grados
            prefer_equal_area: Usar proyección de igual área
            
        Returns:
            Código EPSG del CRS configurado
        """
        if isinstance(bbox, list):
            bbox = BoundingBox(
                min_lon=bbox[0],
                min_lat=bbox[1],
                max_lon=bbox[2],
                max_lat=bbox[3]
            )
        
        optimal_crs = self.crs_transformer.select_optimal_crs(
            bbox, prefer_equal_area
        )
        
        self.crs_transformer.set_target_crs(optimal_crs)
        self.scale_factor = self.crs_transformer.calculate_scale_factors(
            bbox,
            optimal_crs,
            pixel_resolution_deg
        )
        
        return optimal_crs
    
    def setup_for_sub_area(self, sub_area: SubArea) -> None:
        """
        Configura el CRS para una sub-área específica.
        
        Args:
            sub_area: Sub-área con CRS configurado
        """
        self._current_sub_area = sub_area
        self.crs_transformer.set_target_crs(sub_area.crs)
        self.scale_factor = self.crs_transformer.calculate_scale_factors(
            sub_area.bbox,
            sub_area.crs
        )
    
    def _get_scale(self) -> float:
        """Obtiene el factor de escala promedio."""
        if self.scale_factor is None:
            raise ValueError(
                "CRS no configurado. Llame setup_crs() o setup_for_sub_area() primero."
            )
        return self.scale_factor.mean_resolution_m
    
    def _calculate_moments_geo(
        self,
        contour_points: np.ndarray,
        scale_m_per_px: float
    ) -> Dict[str, float]:
        """
        Calcula momentos espaciales con escala.
        
        Args:
            contour_points: Puntos del contorno en píxeles
            scale_m_per_px: Factor de escala metros/píxel
            
        Returns:
            Diccionario con momentos escalados
        """
        if not CV2_AVAILABLE:
            return self._calculate_moments_fallback(contour_points, scale_m_per_px)
        
        moments = cv2.moments(contour_points)
        
        m00 = moments['m00']
        
        if m00 > 0:
            cx = moments['m10'] / m00 * scale_m_per_px
            cy = moments['m01'] / m00 * scale_m_per_px
            m00_scaled = m00 * (scale_m_per_px ** 2)
        else:
            cx, cy = 0.0, 0.0
            m00_scaled = 0.0
        
        return {
            'm00': m00_scaled,
            'm10': moments.get('m10', 0) * scale_m_per_px,
            'm01': moments.get('m01', 0) * scale_m_per_px,
            'centroid_x': cx,
            'centroid_y': cy
        }
    
    def _calculate_moments_fallback(
        self,
        contour_points: np.ndarray,
        scale_m_per_px: float
    ) -> Dict[str, float]:
        """Cálculo de momentos sin OpenCV."""
        scaled = contour_points.astype(np.float64) * scale_m_per_px
        
        n = len(scaled)
        if n == 0:
            return {'m00': 0, 'm10': 0, 'm01': 0, 'centroid_x': 0, 'centroid_y': 0}
        
        m00 = cv2.contourArea(scaled) if CV2_AVAILABLE else 0.0
        cx = np.mean(scaled[:, 0, 0])
        cy = np.mean(scaled[:, 0, 1])
        
        return {
            'm00': m00 or np.sum(np.ones(n)),
            'm10': np.sum(scaled[:, 0, 0]),
            'm01': np.sum(scaled[:, 0, 1]),
            'centroid_x': cx,
            'centroid_y': cy
        }
    
    def calculate_metrics_from_binary_mask(
        self,
        mask: np.ndarray,
        crs_used: Optional[str] = None
    ) -> GeoMorphologicalMetrics:
        """
        Calcula métricas morfométricas desde una máscara binaria.
        
        Args:
            mask: Máscara binaria (0/1 o 0/255)
            crs_used: CRS usado para la transformación
            
        Returns:
            Métricas en metros reales
        """
        if not CV2_AVAILABLE:
            raise RuntimeError("OpenCV es requerido para calcular métricas.")
        
        scale = self._get_scale()
        
        binary = (mask > 0).astype(np.uint8)
        
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        if len(contours) == 0:
            return self._empty_metrics(crs_used)
        
        contour = max(contours, key=cv2.contourArea)
        
        contour_scaled = contour.astype(np.float64) * scale
        
        area_px = cv2.contourArea(contour)
        perimeter_px = cv2.arcLength(contour, True)
        
        area_m2 = area_px * (scale ** 2)
        perimeter_m = perimeter_px * scale
        
        x, y, w, h = cv2.boundingRect(contour)
        bbox_m = (w * scale, h * scale)
        
        moments = self._calculate_moments_geo(contour, scale)
        
        hull = cv2.convexHull(contour_scaled.astype(np.float32))
        hull_area = cv2.contourArea(hull)
        
        compactness = 0.0
        if perimeter_m > 0:
            compactness = (4 * np.pi * area_m2) / (perimeter_m ** 2)
        
        circularity = compactness
        
        rect_area = bbox_m[0] * bbox_m[1]
        rectangularity = area_m2 / rect_area if rect_area > 0 else 0
        
        elongation = min(bbox_m) / max(bbox_m) if max(bbox_m) > 0 else 1
        
        solidity = area_m2 / hull_area if hull_area > 0 else 0
        
        try:
            (cx, cy), (ma, MA), angle = cv2.fitEllipse(contour_scaled)
            eccentricity = ma / MA if MA > 0 else 0
        except Exception:
            eccentricity = 0
        
        metrics = GeoMorphologicalMetrics(
            area_m2=area_m2,
            area_km2=area_m2 / 1_000_000,
            area_ha=area_m2 / 10_000,
            perimeter_m=perimeter_m,
            perimeter_km=perimeter_m / 1000,
            compactness_index=compactness,
            circularity_index=circularity,
            rectangularity_index=rectangularity,
            elongation_index=elongation,
            solidity=solidity,
            eccentricity=eccentricity,
            bounding_box_m=bbox_m,
            centroid_m=(moments['centroid_x'], moments['centroid_y']),
            crs_used=crs_used or self.config.target_crs,
            scale_factor_m_per_px=scale,
            source_bbox=self._current_sub_area.bbox.to_dict() if self._current_sub_area else None
        )
        
        return metrics
    
    def calculate_metrics_from_polygon(
        self,
        polygon_coords: List[List[float]],
        source_crs: Optional[str] = None,
        target_crs: Optional[str] = None
    ) -> GeoMorphologicalMetrics:
        """
        Calcula métricas desde coordenadas de polígono.
        
        Args:
            polygon_coords: Coordenadas del polígono [lon, lat]
            source_crs: CRS origen
            target_crs: CRS destino
            
        Returns:
            Métricas en metros reales
        """
        if not CV2_AVAILABLE:
            raise RuntimeError("OpenCV es requerido para calcular métricas.")
        
        src = source_crs or self.config.source_crs
        dst = target_crs or self.config.target_crs
        
        if dst is None:
            bbox = create_bbox_from_coords(polygon_coords)
            dst = self.setup_crs(bbox)
        
        transformed = self.crs_transformer.transform_coordinates(
            polygon_coords, src, dst
        )
        
        coords_array = np.array(transformed, dtype=np.float64)
        coords_shaped = coords_array.reshape(-1, 1, 2).astype(np.int32)
        
        area_m2 = abs(cv2.contourArea(coords_shaped))
        perimeter_m = cv2.arcLength(coords_shaped, True)
        
        x, y, w, h = cv2.boundingRect(coords_shaped)
        bbox_m = (float(w), float(h))
        
        moments = cv2.moments(coords_shaped)
        m00 = moments['m00']
        cx = moments['m10'] / m00 if m00 > 0 else 0
        cy = moments['m01'] / m00 if m00 > 0 else 0
        
        hull = cv2.convexHull(coords_shaped)
        hull_area = cv2.contourArea(hull)
        
        compactness = 0.0
        if perimeter_m > 0:
            compactness = (4 * np.pi * area_m2) / (perimeter_m ** 2)
        
        rect_area = w * h
        rectangularity = area_m2 / rect_area if rect_area > 0 else 0
        
        elongation = min(w, h) / max(w, h) if max(w, h) > 0 else 1
        
        solidity = area_m2 / hull_area if hull_area > 0 else 0
        
        try:
            (cx_fit, cy_fit), (ma, MA), _ = cv2.fitEllipse(coords_shaped)
            eccentricity = ma / MA if MA > 0 else 0
        except Exception:
            eccentricity = 0
        
        return GeoMorphologicalMetrics(
            area_m2=area_m2,
            area_km2=area_m2 / 1_000_000,
            area_ha=area_m2 / 10_000,
            perimeter_m=perimeter_m,
            perimeter_km=perimeter_m / 1000,
            compactness_index=compactness,
            circularity_index=compactness,
            rectangularity_index=rectangularity,
            elongation_index=elongation,
            solidity=solidity,
            eccentricity=eccentricity,
            bounding_box_m=bbox_m,
            centroid_m=(cx, cy),
            crs_used=dst,
            source_bbox=create_bbox_from_coords(polygon_coords).to_dict()
        )
    
    def calculate_segment_metrics(
        self,
        labeled_array: np.ndarray,
        pixel_area_m2: Optional[float] = None
    ) -> List[SegmentMetrics]:
        """
        Calcula métricas para múltiples segmentos.
        
        Args:
            labeled_array: Array con etiquetas de segmentos
            pixel_area_m2: Área por píxel en m² (calcula si es None)
            
        Returns:
            Lista de métricas por segmento
        """
        if not CV2_AVAILABLE:
            raise RuntimeError("OpenCV es requerido.")
        
        if pixel_area_m2 is None:
            scale = self._get_scale()
            pixel_area_m2 = scale ** 2
        
        labels = np.unique(labeled_array)
        labels = labels[labels > 0]
        
        segments: List[SegmentMetrics] = []
        
        for label in labels:
            mask = (labeled_array == label).astype(np.uint8)
            
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            if len(contours) == 0:
                continue
            
            contour = max(contours, key=cv2.contourArea)
            
            try:
                area_px = cv2.contourArea(contour)
                perimeter_px = cv2.arcLength(contour, True)
                
                area_m2 = area_px * pixel_area_m2
                perimeter_m = perimeter_px * math.sqrt(pixel_area_m2)
                
                x, y, w, h = cv2.boundingRect(contour)
                
                moments = cv2.moments(contour)
                m00 = moments['m00']
                cx = (moments['m10'] / m00) * math.sqrt(pixel_area_m2) if m00 > 0 else 0
                cy = (moments['m01'] / m00) * math.sqrt(pixel_area_m2) if m00 > 0 else 0
                
                hull = cv2.convexHull(contour)
                hull_area = cv2.contourArea(hull)
                
                compactness = 0.0
                if perimeter_m > 0:
                    compactness = (4 * np.pi * area_m2) / (perimeter_m ** 2)
                
                solidity = area_m2 / (hull_area * pixel_area_m2) if hull_area > 0 else 0
                
                segments.append(SegmentMetrics(
                    label=int(label),
                    area_m2=area_m2,
                    perimeter_m=perimeter_m,
                    centroid_m=(cx, cy),
                    bbox_m=(float(w), float(h), float(x), float(y)),
                    compactness=compactness,
                    solidity=solidity,
                    is_valid=True
                ))
                
            except Exception as e:
                segments.append(SegmentMetrics(
                    label=int(label),
                    area_m2=0,
                    perimeter_m=0,
                    centroid_m=(0, 0),
                    bbox_m=(0, 0, 0, 0),
                    compactness=0,
                    solidity=0,
                    is_valid=False,
                    error_message=str(e)
                ))
        
        return segments
    
    def calculate_basin_metrics(
        self,
        basin_boundary: List[List[float]],
        outlet_point: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Calcula métricas completas para una cuenca hidrográfica.
        
        Args:
            basin_boundary: Coordenadas del límite de la cuenca
            outlet_point: Coordenadas del punto de salida
            
        Returns:
            Diccionario con métricas completas
        """
        basin_metrics = self.calculate_metrics_from_polygon(basin_boundary)
        
        result = {
            'basin_metrics': basin_metrics.to_dict(),
            'timestamp': datetime.utcnow().isoformat(),
            'total_segments': 1
        }
        
        if outlet_point:
            result['outlet'] = {
                'coordinates': outlet_point,
                'crs': self.config.target_crs
            }
        
        return result
    
    def _empty_metrics(self, crs_used: Optional[str] = None) -> GeoMorphologicalMetrics:
        """Retorna métricas vacías."""
        return GeoMorphologicalMetrics(
            crs_used=crs_used or self.config.target_crs,
            scale_factor_m_per_px=self._get_scale() if self.scale_factor else None
        )
    
    def save_metrics(
        self,
        metrics: Union[GeoMorphologicalMetrics, List[SegmentMetrics], Dict],
        filename: str = "geo_metrics.json"
    ) -> None:
        """Guarda métricas a archivo JSON."""
        if self.crs_transformer.output_dir is None:
            raise ValueError("output_dir no configurado")
        
        output_path = self.crs_transformer.output_dir / filename
        
        if isinstance(metrics, GeoMorphologicalMetrics):
            data = metrics.to_dict()
        elif isinstance(metrics, list):
            data = [seg.__dict__ for seg in metrics]
        else:
            data = metrics
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de procesamiento."""
        return self.crs_transformer.get_stats()


import math


def convert_pixels_to_meters(
    value_px: float,
    scale_factor: float,
    per_axis: bool = False,
    scale_x: Optional[float] = None,
    scale_y: Optional[float] = None
) -> Union[float, Tuple[float, float]]:
    """
    Convierte valores de píxeles a metros.
    
    Args:
        value_px: Valor en píxeles
        scale_factor: Factor de escala único (m/px)
        per_axis: Si True, retorna (x, y) por separado
        scale_x: Factor de escala en X (sobreescribe scale_factor)
        scale_y: Factor de escala en Y (sobreescribe scale_factor)
        
    Returns:
        Valor en metros o tupla (x_m, y_m)
    """
    if per_axis and scale_x is not None and scale_y is not None:
        return value_px * scale_x, value_px * scale_y
    
    return value_px * scale_factor


def calculate_shape_indices(
    area_m2: float,
    perimeter_m: float,
    bbox_width_m: Optional[float] = None,
    bbox_height_m: Optional[float] = None
) -> Dict[str, float]:
    """
    Calcula índices de forma.
    
    Args:
        area_m2: Área en m²
        perimeter_m: Perímetro en m
        bbox_width_m: Ancho de caja delimitadora en m
        bbox_height_m: Alto de caja delimitadora en m
        
    Returns:
        Diccionario con índices calculados
    """
    indices = {}
    
    if perimeter_m > 0:
        indices['compactness'] = (4 * np.pi * area_m2) / (perimeter_m ** 2)
        indices['circularity'] = (4 * np.pi * area_m2) / (perimeter_m ** 2)
    else:
        indices['compactness'] = 0.0
        indices['circularity'] = 0.0
    
    if bbox_width_m is not None and bbox_height_m is not None:
        rect_area = bbox_width_m * bbox_height_m
        indices['rectangularity'] = area_m2 / rect_area if rect_area > 0 else 0
        
        major = max(bbox_width_m, bbox_height_m)
        minor = min(bbox_width_m, bbox_height_m)
        indices['elongation'] = minor / major if major > 0 else 1
    else:
        indices['rectangularity'] = 0.0
        indices['elongation'] = 1.0
    
    return indices


def estimate_area_from_latitude(
    area_deg2: float,
    center_latitude: float
) -> float:
    """
    Estima área en m² a partir de grados² usando latitud.
    
    Args:
        area_deg2: Área en grados cuadrados
        center_latitude: Latitud central en grados
            
    Returns:
        Área estimada en m²
    """
    lat_rad = math.radians(center_latitude)
    
    m_per_deg_lon = 111320 * math.cos(lat_rad)
    m_per_deg_lat = 110540
    
    m2_per_deg2 = m_per_deg_lon * m_per_deg_lat
    
    return area_deg2 * m2_per_deg2


if __name__ == "__main__":
    import math
    
    print("=" * 60)
    print("GEO-MORPHOLOGICAL CALCULATOR - SKYFUSION ANALYTICS")
    print("=" * 60)
    
    if not CV2_AVAILABLE:
        print("\n[AVISO] OpenCV no está instalado. Funciones limitadas.")
    
    calculator = GeoMorphologicalCalculator(output_dir="../../data/output")
    
    print("\n[1] Configurando CRS para área de prueba...")
    bbox = BoundingBox(
        min_lon=-75.5, min_lat=4.0,
        max_lon=-74.8, max_lat=5.0
    )
    print(f"    BBox: {bbox.min_lon}°, {bbox.min_lat}° a {bbox.max_lon}°, {bbox.max_lat}°")
    
    try:
        crs = calculator.setup_crs(bbox, pixel_resolution_deg=0.0001)
        print(f"    CRS configurado: {crs}")
        print(f"    Factor de escala: {calculator._get_scale():.4f} m/píxel")
        
        print("\n[2] Creando máscara de prueba...")
        mask = np.zeros((500, 500), dtype=np.uint8)
        cv2.circle(mask, (250, 250), 100, 255, -1)
        print(f"    Máscara creada: {mask.shape}")
        
        print("\n[3] Calculando métricas...")
        metrics = calculator.calculate_metrics_from_binary_mask(mask, crs)
        print(f"    Área: {metrics.area_m2:.2f} m² ({metrics.area_ha:.4f} ha)")
        print(f"    Perímetro: {metrics.perimeter_m:.2f} m")
        print(f"    Compacidad: {metrics.compactness_index:.6f}")
        
        print("\n[4] Calculando métricas desde polígono...")
        polygon = [
            [-75.3, 4.3], [-75.1, 4.3], [-75.1, 4.6], [-75.3, 4.6]
        ]
        poly_metrics = calculator.calculate_metrics_from_polygon(polygon)
        print(f"    Área: {poly_metrics.area_m2:.2f} m² ({poly_metrics.area_km2:.4f} km²)")
        print(f"    Perímetro: {poly_metrics.perimeter_m:.2f} m")
        
        print("\n[5] Guardando resultados...")
        calculator.save_metrics(metrics, "test_geo_metrics.json")
        print("    Guardado en test_geo_metrics.json")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
    
    print("\n" + "=" * 60)
    print("PRUEBAS COMPLETADAS")
    print("=" * 60)
