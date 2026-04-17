"""
Tests para el módulo de transformación CRS
=========================================

Tests unitarios para crs_transformer.py y geo_metrics_calculator.py
"""

import sys
import os
import unittest
import math
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'python', 'processing'))

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from crs_transformer import (
        BoundingBox,
        CRSTransformConfig,
        CRSTransformer,
        ProjectionType,
        SubArea,
        create_bbox_from_coords,
        detect_crs_from_metadata,
    )
    CRS_MODULE_AVAILABLE = True
except ImportError as e:
    print(f"[DEBUG] Import error: {e}")
    CRS_MODULE_AVAILABLE = False

try:
    from geo_metrics_calculator import (
        GeoMorphologicalCalculator,
        calculate_shape_indices,
    )
    GEO_CALC_AVAILABLE = True
except ImportError as e:
    print(f"[DEBUG] geo_metrics_calculator import error: {e}")
    GEO_CALC_AVAILABLE = False


class TestBoundingBox(unittest.TestCase):
    """Tests para la clase BoundingBox."""
    
    def test_create_bbox(self):
        bbox = BoundingBox(
            min_lon=-75.5,
            min_lat=4.0,
            max_lon=-74.8,
            max_lat=5.0
        )
        
        self.assertEqual(bbox.min_lon, -75.5)
        self.assertEqual(bbox.min_lat, 4.0)
        self.assertEqual(bbox.max_lon, -74.8)
        self.assertEqual(bbox.max_lat, 5.0)
    
    def test_center_calculation(self):
        bbox = BoundingBox(
            min_lon=-75.5,
            min_lat=4.0,
            max_lon=-74.8,
            max_lat=5.0
        )
        
        self.assertAlmostEqual(bbox.center_lon, -75.15, places=2)
        self.assertAlmostEqual(bbox.center_lat, 4.5, places=2)
    
    def test_dimensions(self):
        bbox = BoundingBox(
            min_lon=-75.5,
            min_lat=4.0,
            max_lon=-74.8,
            max_lat=5.0
        )
        
        self.assertAlmostEqual(bbox.width_deg, 0.7, places=2)
        self.assertAlmostEqual(bbox.height_deg, 1.0, places=2)
    
    def test_intersects(self):
        bbox1 = BoundingBox(-75.5, 4.0, -74.8, 5.0)
        bbox2 = BoundingBox(-75.0, 4.5, -74.5, 5.5)
        
        self.assertTrue(bbox1.intersects(bbox2))
    
    def test_no_intersect(self):
        bbox1 = BoundingBox(-75.5, 4.0, -74.8, 5.0)
        bbox2 = BoundingBox(-74.0, 5.5, -73.5, 6.0)
        
        self.assertFalse(bbox1.intersects(bbox2))
    
    def test_contains_point(self):
        bbox = BoundingBox(-75.5, 4.0, -74.8, 5.0)
        
        self.assertTrue(bbox.contains(-75.0, 4.5))
        self.assertFalse(bbox.contains(-76.0, 4.5))
    
    def test_to_dict(self):
        bbox = BoundingBox(-75.5, 4.0, -74.8, 5.0)
        d = bbox.to_dict()
        
        self.assertIn('min_lon', d)
        self.assertIn('center_lon', d)
        self.assertIn('width_deg', d)


class TestCRSTransformConfig(unittest.TestCase):
    """Tests para la clase CRSTransformConfig."""
    
    def test_default_config(self):
        config = CRSTransformConfig()
        
        self.assertEqual(config.source_crs, "EPSG:4326")
        self.assertIsNone(config.target_crs)
        self.assertEqual(config.transformation_method, "auto")
    
    def test_custom_config(self):
        config = CRSTransformConfig(
            source_crs="EPSG:4326",
            target_crs="EPSG:32618",
            max_zone_width_deg=3.0
        )
        
        self.assertEqual(config.source_crs, "EPSG:4326")
        self.assertEqual(config.target_crs, "EPSG:32618")
        self.assertEqual(config.max_zone_width_deg, 3.0)
    
    def test_validation_empty_crs(self):
        config = CRSTransformConfig(source_crs="")
        
        with self.assertRaises(ValueError):
            config.validate()
    
    def test_validation_invalid_method(self):
        config = CRSTransformConfig(transformation_method="invalid")
        
        with self.assertRaises(ValueError):
            config.validate()


class TestCRSTransformer(unittest.TestCase):
    """Tests para la clase CRSTransformer."""
    
    def test_init(self):
        transformer = CRSTransformer()
        
        self.assertIsNotNone(transformer.config)
        self.assertIsNone(transformer.scale_factor)
        self.assertEqual(transformer.stats['sub_areas_created'], 0)
    
    def test_calculate_utm_zone_north(self):
        transformer = CRSTransformer()
        
        zone, hem = transformer.calculate_utm_zone(-75.2, 4.5)
        
        self.assertEqual(zone, 18)
        self.assertEqual(hem, 'N')
    
    def test_calculate_utm_zone_south(self):
        transformer = CRSTransformer()
        
        zone, hem = transformer.calculate_utm_zone(-75.2, -15.0)
        
        self.assertEqual(zone, 18)
        self.assertEqual(hem, 'S')
    
    def test_split_area_small(self):
        transformer = CRSTransformer()
        bbox = BoundingBox(-75.5, 4.0, -74.8, 5.0)
        
        sub_areas = transformer.split_area_into_sub_zones(bbox, max_width_deg=6.0)
        
        self.assertEqual(len(sub_areas), 1)
        self.assertEqual(sub_areas[0].id, "main_zone")
    
    def test_split_area_large(self):
        transformer = CRSTransformer()
        bbox = BoundingBox(-80.0, 0.0, -70.0, 5.0)
        
        sub_areas = transformer.split_area_into_sub_zones(bbox, max_width_deg=6.0)
        
        self.assertGreater(len(sub_areas), 1)
        self.assertTrue(all(area.crs.startswith("EPSG:326") for area in sub_areas))
    
    def test_reset_stats(self):
        transformer = CRSTransformer()
        transformer.stats['sub_areas_created'] = 5
        
        transformer.reset_stats()
        
        self.assertEqual(transformer.stats['sub_areas_created'], 0)


class TestCreateBboxFromCoords(unittest.TestCase):
    """Tests para la función create_bbox_from_coords."""
    
    def test_from_list(self):
        coords = [[-75.5, 4.0], [-74.8, 5.0], [-75.0, 4.5]]
        
        bbox = create_bbox_from_coords(coords)
        
        self.assertAlmostEqual(bbox.min_lon, -75.5, places=4)
        self.assertAlmostEqual(bbox.min_lat, 4.0, places=4)
        self.assertAlmostEqual(bbox.max_lon, -74.8, places=4)
        self.assertAlmostEqual(bbox.max_lat, 5.0, places=4)
    
    def test_from_array(self):
        if not NUMPY_AVAILABLE:
            self.skipTest("numpy not available")
        
        coords = np.array([[-75.5, 4.0], [-74.8, 5.0]])
        
        bbox = create_bbox_from_coords(coords)
        
        self.assertAlmostEqual(bbox.min_lon, -75.5, places=4)
        self.assertAlmostEqual(bbox.max_lon, -74.8, places=4)


class TestDetectCRSFromMetadata(unittest.TestCase):
    """Tests para la función detect_crs_from_metadata."""
    
    def test_from_epsg(self):
        metadata = {'epsg': 4326}
        
        result = detect_crs_from_metadata(metadata)
        
        self.assertEqual(result, "EPSG:4326")
    
    def test_from_crs(self):
        metadata = {'crs': "EPSG:32618"}
        
        result = detect_crs_from_metadata(metadata)
        
        self.assertEqual(result, "EPSG:32618")
    
    def test_from_projection_utm_north(self):
        metadata = {'projection': 'UTM', 'zone': 18}
        
        result = detect_crs_from_metadata(metadata)
        
        self.assertEqual(result, "EPSG:32618")
    
    def test_from_projection_utm_south(self):
        metadata = {'projection': 'UTM south', 'zone': 18}
        
        result = detect_crs_from_metadata(metadata)
        
        self.assertEqual(result, "EPSG:32718")
    
    def test_no_crs(self):
        metadata = {'other': 'data'}
        
        result = detect_crs_from_metadata(metadata)
        
        self.assertIsNone(result)


class TestGeoMetricsCalculator(unittest.TestCase):
    """Tests para la clase GeoMorphologicalCalculator."""
    
    def setUp(self):
        if GEO_CALC_AVAILABLE:
            self.calculator = GeoMorphologicalCalculator()
        else:
            self.skipTest("geo_metrics_calculator not available")
    
    def test_init(self):
        self.assertIsNotNone(self.calculator.crs_transformer)
        self.assertIsNone(self.calculator.scale_factor)
    
    def test_setup_crs(self):
        bbox = BoundingBox(-75.5, 4.0, -74.8, 5.0)
        
        crs = self.calculator.setup_crs(bbox)
        
        self.assertIsNotNone(crs)
        self.assertTrue(crs.startswith("EPSG:"))
        self.assertIsNotNone(self.calculator.scale_factor)
    
    def test_setup_without_scale_fails(self):
        mask = [[1, 0], [0, 1]]
        
        with self.assertRaises(ValueError):
            self.calculator.calculate_metrics_from_binary_mask(mask)


class TestShapeIndices(unittest.TestCase):
    """Tests para funciones de índices de forma."""
    
    def test_compactness_circle(self):
        if CRS_MODULE_AVAILABLE:
            from geo_metrics_calculator import calculate_shape_indices
            
            r = 100
            area = math.pi * r ** 2
            perimeter = 2 * math.pi * r
            
            indices = calculate_shape_indices(area, perimeter)
            
            self.assertAlmostEqual(indices['compactness'], 1.0, places=5)
            self.assertAlmostEqual(indices['circularity'], 1.0, places=5)
    
    def test_elongation_square(self):
        if CRS_MODULE_AVAILABLE:
            from geo_metrics_calculator import calculate_shape_indices
            
            indices = calculate_shape_indices(
                area_m2=10000,
                perimeter_m=400,
                bbox_width_m=100,
                bbox_height_m=100
            )
            
            self.assertAlmostEqual(indices['elongation'], 1.0, places=5)
    
    def test_elongation_rectangle(self):
        if CRS_MODULE_AVAILABLE:
            from geo_metrics_calculator import calculate_shape_indices
            
            indices = calculate_shape_indices(
                area_m2=10000,
                perimeter_m=460,
                bbox_width_m=200,
                bbox_height_m=50
            )
            
            self.assertAlmostEqual(indices['elongation'], 0.25, places=5)


if __name__ == '__main__':
    unittest.main()
