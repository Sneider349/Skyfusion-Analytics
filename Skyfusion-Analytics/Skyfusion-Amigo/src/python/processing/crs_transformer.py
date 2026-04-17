"""
Módulo de Transformación de Proyecciones Espaciales (CRS)
==========================================================

Proporciona funcionalidad para transformar coordenadas y datos espaciales
entre diferentes sistemas de referencia de coordenadas (CRS) para asegurar
que las mediciones de métricas morfométricas correspondan a metros reales
sobre el terreno.

Funcionalidades:
- Detección automática del CRS actual
- Selección automática del CRS óptimo para el área de estudio
- Transformación de coordenadas individuales y datasets completos
- Cálculo de factores de escala para conversión precisa de píxeles a metros
- División de áreas extensas en sub-zonas con CRS apropiado

Autor: Skyfusion Analytics Team
Fecha: 2026
"""

from __future__ import annotations

import math
import json
import warnings
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any, Union
from datetime import datetime

import numpy as np

PYPROJ_AVAILABLE = False
try:
    from pyproj import CRS, Transformer, Proj
    PYPROJ_AVAILABLE = True
    try:
        from pyproj.aoi import AreaOfInterest
    except ImportError:
        AreaOfInterest = None
    try:
        from pyproj.database import query_utm_crs
    except ImportError:
        query_utm_crs = None
except ImportError as e:
    print(f"[DEBUG] pyproj import error: {e}")
    warnings.warn(
        "pyproj no está instalado. Install with: pip install pyproj",
        ImportWarning
    )


class ProjectionType(Enum):
    """Tipos de proyecciones espacials."""
    GEOGRAPHIC = "geographic"
    UTM = "utm"
    EQUAL_AREA = "equal_area"
    CUSTOM = "custom"


@dataclass
class BoundingBox:
    """Caja delimitadora en coordenadas geográficas."""
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float
    
    @property
    def center_lon(self) -> float:
        return (self.min_lon + self.max_lon) / 2
    
    @property
    def center_lat(self) -> float:
        return (self.min_lat + self.max_lat) / 2
    
    @property
    def width_deg(self) -> float:
        return abs(self.max_lon - self.min_lon)
    
    @property
    def height_deg(self) -> float:
        return abs(self.max_lat - self.min_lat)
    
    @property
    def area_deg2(self) -> float:
        return self.width_deg * self.height_deg
    
    def intersects(self, other: BoundingBox) -> bool:
        return not (
            self.max_lon < other.min_lon or
            self.min_lon > other.max_lon or
            self.max_lat < other.min_lat or
            self.min_lat > other.max_lat
        )
    
    def contains(self, lon: float, lat: float) -> bool:
        return (self.min_lon <= lon <= self.max_lon and
                self.min_lat <= lat <= self.max_lat)
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'min_lon': self.min_lon,
            'min_lat': self.min_lat,
            'max_lon': self.max_lon,
            'max_lat': self.max_lat,
            'center_lon': self.center_lon,
            'center_lat': self.center_lat,
            'width_deg': self.width_deg,
            'height_deg': self.height_deg
        }


@dataclass
class CRSTransformConfig:
    """Configuración para transformación de CRS."""
    source_crs: str = "EPSG:4326"
    target_crs: Optional[str] = None
    transformation_method: str = "auto"
    allow_multipart: bool = True
    max_zone_width_deg: float = 6.0
    hemisphere: str = "auto"
    utm_zone_params: Optional[Dict[str, Any]] = None
    
    def validate(self) -> bool:
        if self.source_crs is None or self.source_crs == "":
            raise ValueError("CRS fuente no puede estar vacío")
        if self.transformation_method not in ["auto", "precise", "fast"]:
            raise ValueError(f"Método de transformación no válido: {self.transformation_method}")
        return True


@dataclass
class CRSInfo:
    """Información sobre un CRS."""
    epsg: Optional[str]
    name: str
    projection_type: ProjectionType
    units: str
    zone: Optional[int] = None
    hemisphere: Optional[str] = None
    area_extent: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'epsg': self.epsg,
            'name': self.name,
            'projection_type': self.projection_type.value,
            'units': self.units,
        }
        if self.zone is not None:
            result['zone'] = self.zone
        if self.hemisphere is not None:
            result['hemisphere'] = self.hemisphere
        return result


@dataclass
class ScaleFactor:
    """Factor de escala para conversión de píxeles a metros."""
    x_scale: float
    y_scale: float
    pixel_area_m2: float
    crs_info: Optional[Dict[str, Any]] = None
    
    @property
    def x_resolution_m(self) -> float:
        return abs(self.x_scale)
    
    @property
    def y_resolution_m(self) -> float:
        return abs(self.y_scale)
    
    @property
    def mean_resolution_m(self) -> float:
        return (abs(self.x_scale) + abs(self.y_scale)) / 2


@dataclass
class SubArea:
    """Sub-área para procesamiento con CRS individual."""
    id: str
    bbox: BoundingBox
    crs: str
    crs_info: CRSInfo
    zone_number: Optional[int] = None
    zone_letter: Optional[str] = None
    center_lat: float = 0.0
    center_lon: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'bbox': self.bbox.to_dict(),
            'crs': self.crs,
            'crs_info': self.crs_info.to_dict(),
            'zone_number': self.zone_number,
            'zone_letter': self.zone_letter,
            'center_lat': self.center_lat,
            'center_lon': self.center_lon
        }


class CRSTransformer:
    """
    Transformador de proyecciones espaciales para Skyfusion Analytics.
    
    Proporciona métodos para:
    - Detectar y seleccionar CRS óptimos
    - Transformar coordenadas entre CRS
    - Manejar áreas extensas dividiendo en sub-zonas
    - Calcular factores de escala para conversión a metros
    
    Attributes:
        config: Configuración de transformación
        transformer: Transformer de pyproj para transformaciones
        scale_factors: Factores de escala calculados
    """
    
    WGS84_GEOGRAPHIC = "EPSG:4326"
    WGS84_UTM_NORTH = "EPSG:32600"
    WGS84_UTM_SOUTH = "EPSG:32700"
    
    def __init__(
        self,
        config: Optional[CRSTransformConfig] = None,
        output_dir: Optional[str] = None
    ):
        """
        Inicializa el transformador CRS.
        
        Args:
            config: Configuración de transformación
            output_dir: Directorio para guardar resultados
        """
        self.config = config or CRSTransformConfig()
        self.config.validate()
        
        self.output_dir = Path(output_dir) if output_dir else None
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._transformer: Optional[Transformer] = None
        self._source_crs: Optional[CRS] = None
        self._target_crs: Optional[CRS] = None
        self._current_source: Optional[str] = None
        self._current_target: Optional[str] = None
        self._scale_factors: Optional[ScaleFactor] = None
        
        self.stats = {
            'transformations_count': 0,
            'sub_areas_created': 0,
            'coordinate_transformations': 0,
            'pixel_to_meter_conversions': 0
        }
    
    @property
    def scale_factor(self) -> Optional[ScaleFactor]:
        return self._scale_factors
    
    def _init_transformer(
        self,
        source_crs: str,
        target_crs: str
    ) -> Transformer:
        """Inicializa el transformador de pyproj."""
        if not PYPROJ_AVAILABLE:
            raise RuntimeError(
                "pyproj es requerido para transformaciones CRS. "
                "Instale con: pip install pyproj"
            )
        
        cache_key = f"{source_crs}->{target_crs}"
        if (self._current_source == source_crs and 
            self._current_target == target_crs and 
            self._transformer is not None):
            return self._transformer
        
        src_crs = CRS.from_string(source_crs)
        dst_crs = CRS.from_string(target_crs)
        
        self._transformer = Transformer.from_crs(
            src_crs, dst_crs, always_xy=True
        )
        
        self._source_crs = src_crs
        self._target_crs = dst_crs
        self._current_source = source_crs
        self._current_target = target_crs
        
        return self._transformer
    
    def detect_crs_type(self, crs_string: str) -> CRSInfo:
        """
        Detecta el tipo de CRS a partir de una cadena.
        
        Args:
            crs_string: Código EPSG o cadena WKT
            
        Returns:
            Información del CRS detectado
        """
        if not PYPROJ_AVAILABLE:
            raise RuntimeError("pyproj es requerido")
        
        try:
            crs = CRS.from_string(crs_string)
        except Exception as e:
            raise ValueError(f"CRS inválido: {crs_string}. Error: {e}")
        
        projection_type = ProjectionType.GEOGRAPHIC
        
        if crs.is_geographic:
            projection_type = ProjectionType.GEOGRAPHIC
            units = "degrees"
        elif crs.is_projected:
            name_lower = crs.name.lower()
            if 'utm' in name_lower:
                projection_type = ProjectionType.UTM
            elif 'equal area' in name_lower or 'equalarea' in name_lower:
                projection_type = ProjectionType.EQUAL_AREA
            else:
                projection_type = ProjectionType.CUSTOM
            try:
                units = crs.axis_info[0].unit.name if crs.axis_info else "unknown"
            except AttributeError:
                units = "meters" if crs.is_projected else "unknown"
        else:
            projection_type = ProjectionType.CUSTOM
            units = "unknown"
        
        zone = None
        hemisphere = None
        
        if projection_type == ProjectionType.UTM:
            try:
                if 'zone' in crs.name.lower():
                    parts = crs.name.split()
                    for part in parts:
                        if part.lower().startswith('zone'):
                            zone = int(''.join(filter(str.isdigit, part)))
                        if 'north' in part.lower():
                            hemisphere = 'N'
                        elif 'south' in part.lower():
                            hemisphere = 'S'
            except Exception:
                pass
        
        return CRSInfo(
            epsg=crs_string if crs_string.startswith("EPSG") else None,
            name=crs.name,
            projection_type=projection_type,
            units=units,
            zone=zone,
            hemisphere=hemisphere
        )
    
    def calculate_utm_zone(self, lon: float, lat: float) -> Tuple[int, str]:
        """
        Calcula la zona UTM para una coordenada.
        
        Args:
            lon: Longitud
            lat: Latitud
            
        Returns:
            Tupla (zona, hemisferio)
        """
        zone_number = int((lon + 180) / 6) + 1
        
        if lat >= 0:
            hemisphere = 'N'
        else:
            hemisphere = 'S'
            if zone_number == 32 and lon >= 3:
                zone_number = 32
            elif zone_number == 32 and lon < 3:
                zone_number = 31
        
        return zone_number, hemisphere
    
    def get_utm_crs_for_location(
        self,
        lon: float,
        lat: float,
        force_zone: Optional[int] = None
    ) -> str:
        """
        Obtiene el código EPSG de la zona UTM para una ubicación.
        
        Args:
            lon: Longitud
            lat: Latitud
            force_zone: Forzar zona específica (opcional)
            
        Returns:
            Código EPSG de la zona UTM
        """
        if not PYPROJ_AVAILABLE:
            zone, hem = self.calculate_utm_zone(lon, lat)
            base = 32600 if hem == 'N' else 32700
            return f"EPSG:{base + zone}"
        
        zone_number, hemisphere = self.calculate_utm_zone(lon, lat)
        
        if force_zone is not None:
            zone_number = force_zone
        
        min_lon_zone = (zone_number - 1) * 6 - 180
        max_lon_zone = zone_number * 6 - 180
        
        try:
            if query_utm_crs is not None:
                utm_crs_list = query_utm_crs(
                    location=(lon, lat),
                    approximate_best_guess=True
                )
                
                if len(utm_crs_list) > 0:
                    best = utm_crs_list[0]
                    return f"EPSG:{best}"
        except Exception:
            pass
        
        if hemisphere == 'N':
            return f"EPSG:326{zone_number:02d}"
        else:
            return f"EPSG:327{zone_number:02d}"
    
    def select_optimal_crs(
        self,
        bbox: BoundingBox,
        prefer_equal_area: bool = False
    ) -> str:
        """
        Selecciona el CRS óptimo para un área de estudio.
        
        Args:
            bbox: Caja delimitadora del área de estudio
            prefer_equal_area: Preferir proyecciones de igual área
            
        Returns:
            Código EPSG del CRS óptimo
        """
        center_lon = bbox.center_lon
        center_lat = bbox.center_lat
        
        if bbox.width_deg > self.config.max_zone_width_deg and not prefer_equal_area:
            warnings.warn(
                f"El área es muy extensa ({bbox.width_deg:.1f}°). "
                f"Considere usar sub-áreas o una proyección de igual área.",
                UserWarning
            )
        
        if prefer_equal_area:
            if center_lat > 0:
                return "EPSG:6933"
            else:
                return "EPSG:6933"
        
        utm_crs = self.get_utm_crs_for_location(center_lon, center_lat)
        
        return utm_crs
    
    def split_area_into_sub_zones(
        self,
        bbox: BoundingBox,
        max_width_deg: Optional[float] = None
    ) -> List[SubArea]:
        """
        Divide un área extensa en sub-zonas con CRS apropiado.
        
        Args:
            bbox: Caja delimitadora del área
            max_width_deg: Ancho máximo de cada sub-zona en grados
            
        Returns:
            Lista de sub-áreas con CRS individuales
        """
        if max_width_deg is None:
            max_width_deg = self.config.max_zone_width_deg
        
        sub_areas: List[SubArea] = []
        zone_number, hemisphere = self.calculate_utm_zone(bbox.center_lon, bbox.center_lat)
        
        if bbox.width_deg <= max_width_deg:
            utm_crs = self.get_utm_crs_for_location(bbox.center_lon, bbox.center_lat)
            crs_info = self.detect_crs_type(utm_crs)
            
            sub_areas.append(SubArea(
                id="main_zone",
                bbox=bbox,
                crs=utm_crs,
                crs_info=crs_info,
                zone_number=zone_number,
                zone_letter=hemisphere,
                center_lat=bbox.center_lat,
                center_lon=bbox.center_lon
            ))
        else:
            num_zones = math.ceil(bbox.width_deg / max_width_deg)
            
            for i in range(num_zones):
                sub_min_lon = bbox.min_lon + i * max_width_deg
                sub_max_lon = min(sub_min_lon + max_width_deg, bbox.max_lon)
                
                sub_center_lon = (sub_min_lon + sub_max_lon) / 2
                sub_center_lat = bbox.center_lat
                
                sub_utm_crs = self.get_utm_crs_for_location(
                    sub_center_lon, sub_center_lat
                )
                sub_crs_info = self.detect_crs_type(sub_utm_crs)
                sub_zone, sub_hem = self.calculate_utm_zone(
                    sub_center_lon, sub_center_lat
                )
                
                sub_bbox = BoundingBox(
                    min_lon=sub_min_lon,
                    min_lat=bbox.min_lat,
                    max_lon=sub_max_lon,
                    max_lat=bbox.max_lat
                )
                
                sub_areas.append(SubArea(
                    id=f"zone_{i+1}",
                    bbox=sub_bbox,
                    crs=sub_utm_crs,
                    crs_info=sub_crs_info,
                    zone_number=sub_zone,
                    zone_letter=sub_hem,
                    center_lat=sub_center_lat,
                    center_lon=sub_center_lon
                ))
        
        self.stats['sub_areas_created'] = len(sub_areas)
        return sub_areas
    
    def transform_coordinates(
        self,
        coordinates: Union[List[Tuple[float, float]], np.ndarray],
        source_crs: Optional[str] = None,
        target_crs: Optional[str] = None
    ) -> np.ndarray:
        """
        Transforma coordenadas entre CRS.
        
        Args:
            coordinates: Lista de coordenadas (lon, lat) o ndarray
            source_crs: CRS origen (usa config si es None)
            target_crs: CRS destino (usa config si es None)
            
        Returns:
            Array numpy con coordenadas transformadas
        """
        src = source_crs or self.config.source_crs
        dst = target_crs or self.config.target_crs
        
        if dst is None:
            raise ValueError(
                "CRS destino no especificado. "
                "Configure config.target_crs o proporcione target_crs."
            )
        
        transformer = self._init_transformer(src, dst)
        
        if isinstance(coordinates, list):
            coords = np.array(coordinates)
        else:
            coords = coordinates
        
        if coords.ndim == 1:
            coords = coords.reshape(1, -1)
        
        if coords.shape[1] < 2:
            raise ValueError("Coordenadas deben tener al menos (lon, lat)")
        
        lon_coords = coords[:, 0]
        lat_coords = coords[:, 1]
        
        x_transformed, y_transformed = transformer.transform(
            lon_coords, lat_coords
        )
        
        if coords.shape[1] == 2:
            result = np.column_stack([x_transformed, y_transformed])
        else:
            result = np.zeros((len(lon_coords), coords.shape[1]))
            result[:, 0] = x_transformed
            result[:, 1] = y_transformed
            if coords.shape[1] > 2:
                result[:, 2:] = coords[:, 2:]
        
        self.stats['coordinate_transformations'] += len(lon_coords)
        return result
    
    def transform_bbox(
        self,
        bbox: BoundingBox,
        target_crs: Optional[str] = None
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Transforma una caja delimitadora a otro CRS.
        
        Args:
            bbox: Caja delimitadora a transformar
            target_crs: CRS destino
            
        Returns:
            Esquinas transformadas ((x_min, y_min), (x_max, y_max))
        """
        dst = target_crs or self.config.target_crs
        if dst is None:
            raise ValueError("CRS destino no especificado")
        
        corners = np.array([
            [bbox.min_lon, bbox.min_lat],
            [bbox.max_lon, bbox.min_lat],
            [bbox.max_lon, bbox.max_lat],
            [bbox.min_lon, bbox.max_lat]
        ])
        
        transformed = self.transform_coordinates(corners, target_crs=dst)
        
        x_min, y_min = transformed.min(axis=0)
        x_max, y_max = transformed.max(axis=0)
        
        return (x_min, y_min), (x_max, y_max)
    
    def calculate_scale_factors(
        self,
        bbox: BoundingBox,
        target_crs: Optional[str] = None,
        pixel_size_deg: Optional[float] = None
    ) -> ScaleFactor:
        """
        Calcula factores de escala para convertir píxeles a metros.
        
        Args:
            bbox: Caja delimitadora
            target_crs: CRS destino
            pixel_size_deg: Tamaño de píxel en grados (opcional)
            
        Returns:
            Factor de escala
        """
        dst = target_crs or self.config.target_crs
        if dst is None:
            raise ValueError("CRS destino no especificado")
        
        if PYPROJ_AVAILABLE:
            src_crs = CRS.from_string(self.config.source_crs)
            dst_crs_obj = CRS.from_string(dst)
            
            transformer = Transformer.from_crs(
                src_crs, dst_crs_obj, always_xy=True
            )
            
            center_lon = bbox.center_lon
            center_lat = bbox.center_lat
            
            px, py = transformer.transform(center_lon, center_lat)
            
            px_dx, py_dy = transformer.transform(
                center_lon + (pixel_size_deg or 0.0001),
                center_lat + (pixel_size_deg or 0.0001)
            )
            
            x_scale = abs(px_dx - px)
            y_scale = abs(py_dy - py)
            
            if pixel_size_deg:
                x_scale = x_scale / pixel_size_deg * 0.0001
                y_scale = y_scale / pixel_size_deg * 0.0001
        else:
            lat_rad = math.radians(bbox.center_lat)
            meters_per_deg_lon = 111320 * math.cos(lat_rad)
            meters_per_deg_lat = 110540
            
            x_scale = meters_per_deg_lon
            y_scale = meters_per_deg_lat
            
            if pixel_size_deg:
                x_scale *= pixel_size_deg
                y_scale *= pixel_size_deg
        
        crs_info = self.detect_crs_type(dst).to_dict()
        
        scale = ScaleFactor(
            x_scale=x_scale,
            y_scale=y_scale,
            pixel_area_m2=abs(x_scale * y_scale),
            crs_info=crs_info
        )
        
        self._scale_factors = scale
        self.stats['pixel_to_meter_conversions'] += 1
        
        return scale
    
    def set_target_crs(self, target_crs: str) -> None:
        """Establece el CRS destino."""
        self.config.target_crs = target_crs
        self._transformer = None
        self._current_target = None
    
    def reproject_polygon_coordinates(
        self,
        polygon_coords: List[List[float]],
        target_crs: Optional[str] = None
    ) -> List[List[float]]:
        """
        Reproyecta coordenadas de un polígono.
        
        Args:
            polygon_coords: Coordenadas del polígono [[lon1, lat1], [lon2, lat2], ...]
            target_crs: CRS destino
            
        Returns:
            Coordenadas reproyectadas
        """
        coords_array = np.array(polygon_coords)
        transformed = self.transform_coordinates(
            coords_array, target_crs=target_crs
        )
        return transformed.tolist()
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de transformación."""
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """Reinicia estadísticas."""
        self.stats = {
            'transformations_count': 0,
            'sub_areas_created': 0,
            'coordinate_transformations': 0,
            'pixel_to_meter_conversions': 0
        }
    
    def save_transform_info(
        self,
        bbox: BoundingBox,
        target_crs: Optional[str] = None,
        filename: str = "transform_info.json"
    ) -> None:
        """
        Guarda información de transformación a archivo JSON.
        
        Args:
            bbox: Caja delimitadora usada
            target_crs: CRS destino
            filename: Nombre del archivo
        """
        if self.output_dir is None:
            raise ValueError("output_dir no configurado")
        
        dst = target_crs or self.config.target_crs
        crs_info = self.detect_crs_type(dst).to_dict() if dst else None
        
        info = {
            'timestamp': datetime.utcnow().isoformat(),
            'source_crs': self.config.source_crs,
            'target_crs': dst,
            'bbox': bbox.to_dict(),
            'crs_info': crs_info,
            'stats': self.stats
        }
        
        if self._scale_factors:
            info['scale_factors'] = {
                'x_scale_m': self._scale_factors.x_scale,
                'y_scale_m': self._scale_factors.y_scale,
                'pixel_area_m2': self._scale_factors.pixel_area_m2
            }
        
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False)


def detect_crs_from_metadata(metadata: Dict[str, Any]) -> Optional[str]:
    """
    Detecta el CRS a partir de metadatos de archivo.
    
    Args:
        metadata: Metadatos del archivo (puede incluir proj4, wkt, epsg)
        
    Returns:
        Código EPSG detectado o None
    """
    if 'epsg' in metadata:
        return f"EPSG:{metadata['epsg']}"
    
    if 'crs' in metadata:
        return metadata['crs']
    
    if 'projection' in metadata:
        proj = metadata['projection'].lower()
        if 'utm' in proj:
            zone = metadata.get('zone', 18)
            if 'south' in proj:
                return f"EPSG:327{zone:02d}"
            return f"EPSG:326{zone:02d}"
    
    return None


def get_crs_from_epsg(epsg_code: int) -> str:
    """Convierte código EPSG a string."""
    return f"EPSG:{epsg_code}"


def create_bbox_from_coords(
    coordinates: Union[List[List[float]], np.ndarray]
) -> BoundingBox:
    """
    Crea una caja delimitadora a partir de coordenadas.
    
    Args:
        coordinates: Lista de coordenadas [lon, lat]
        
    Returns:
        BoundingBox
    """
    coords = np.array(coordinates)
    
    lons = coords[:, 0]
    lats = coords[:, 1]
    
    return BoundingBox(
        min_lon=float(np.min(lons)),
        min_lat=float(np.min(lats)),
        max_lon=float(np.max(lons)),
        max_lat=float(np.max(lats))
    )


if __name__ == "__main__":
    print("=" * 60)
    print("CRS TRANSFORMER - SKYFUSION ANALYTICS")
    print("=" * 60)
    
    if not PYPROJ_AVAILABLE:
        print("\n[AVISO] pyproj no está instalado. Funciones limitadas.")
        print("Instale con: pip install pyproj")
    
    transformer = CRSTransformer()
    
    print("\n[1] Detectando tipo de CRS...")
    crs_info = transformer.detect_crs_type("EPSG:4326")
    print(f"    EPSG:4326 - {crs_info.name}")
    print(f"    Tipo: {crs_info.projection_type.value}")
    print(f"    Unidades: {crs_info.units}")
    
    print("\n[2] Calculando zona UTM...")
    zone, hem = transformer.calculate_utm_zone(-75.2, 4.5)
    print(f"    Lon=-75.2, Lat=4.5 -> Zona {zone}{hem}")
    
    print("\n[3] Seleccionando CRS óptimo...")
    bbox = BoundingBox(
        min_lon=-75.5, min_lat=4.0,
        max_lon=-74.8, max_lat=5.0
    )
    print(f"    BBox: {bbox.min_lon}°, {bbox.min_lat}° a {bbox.max_lon}°, {bbox.max_lat}°")
    
    if PYPROJ_AVAILABLE:
        optimal_crs = transformer.select_optimal_crs(bbox)
        print(f"    CRS óptimo: {optimal_crs}")
    
    print("\n[4] Dividiendo área en sub-zonas...")
    sub_zones = transformer.split_area_into_sub_zones(bbox)
    print(f"    Sub-zonas creadas: {len(sub_zones)}")
    for zone in sub_zones:
        print(f"      - {zone.id}: {zone.crs}")
    
    print("\n[5] Calculando factores de escala...")
    if PYPROJ_AVAILABLE:
        utm_crs = transformer.select_optimal_crs(bbox)
        transformer.set_target_crs(utm_crs)
        scale = transformer.calculate_scale_factors(bbox)
        print(f"    X Scale: {scale.x_scale:.2f} m/deg")
        print(f"    Y Scale: {scale.y_scale:.2f} m/deg")
        print(f"    Área por grado²: {scale.pixel_area_m2:.2f} m²")
    
    print("\n[6] Estadísticas:")
    stats = transformer.get_stats()
    for key, value in stats.items():
        print(f"    {key}: {value}")
    
    print("\n" + "=" * 60)
    print("PRUEBAS COMPLETADAS")
    print("=" * 60)
