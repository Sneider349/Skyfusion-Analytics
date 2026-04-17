"""
Procesamiento de datos geoespaciales
====================================

Módulos de procesamiento:
- crs_transformer: Transformación de proyecciones CRS
- geo_metrics_calculator: Cálculo de métricas en metros reales
- morphological_processor: Procesamiento morfológico de imágenes
- indices_processor: Procesamiento de índices (NDVI, NDWI)
- classification_processor: Clasificación de cobertura
"""

from .crs_transformer import (
    CRSTransformer,
    CRSTransformConfig,
    BoundingBox,
    CRSInfo,
    ScaleFactor,
    SubArea,
    ProjectionType,
    create_bbox_from_coords,
    detect_crs_from_metadata,
)

from .geo_metrics_calculator import (
    GeoMorphologicalCalculator,
    GeoMorphologicalMetrics,
    SegmentMetrics,
    calculate_shape_indices,
    convert_pixels_to_meters,
)

__all__ = [
    'CRSTransformer',
    'CRSTransformConfig',
    'BoundingBox',
    'CRSInfo',
    'ScaleFactor',
    'SubArea',
    'ProjectionType',
    'create_bbox_from_coords',
    'detect_crs_from_metadata',
    'GeoMorphologicalCalculator',
    'GeoMorphologicalMetrics',
    'SegmentMetrics',
    'calculate_shape_indices',
    'convert_pixels_to_meters',
]
