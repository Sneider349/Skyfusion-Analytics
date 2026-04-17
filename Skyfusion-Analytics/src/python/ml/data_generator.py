"""
Generador de Dataset para Predicción de Extensión de Agua
Skyfusion Analytics - CNN-LSTM-Attention Pipeline

Este módulo extrae y prepara secuencias de parches espaciales
para entrenamiento del modelo de predicción de extensión de agua.
"""

import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import ee
from tqdm import tqdm

try:
    import cv2
except ImportError:
    cv2 = None


@dataclass
class CatchmentConfig:
    name: str
    bounds: Tuple[float, float, float, float]
    resolution_m: int = 30
    patch_size: int = 64
    collection: str = 'LANDSAT/LC08/C02/T1_L2'


@dataclass
class DatasetConfig:
    sequence_length: int = 10
    horizons: List[int] = field(default_factory=lambda: [7, 14, 30])
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    min_water_coverage: float = 0.01
    max_cloud_cover: float = 0.3
    temporal_gap_days: int = 8


COMBEIMA_CONFIG = CatchmentConfig(
    name='Combeima',
    bounds=(-75.30, 4.35, -75.10, 4.55),
    resolution_m=30,
    patch_size=64
)


class WaterDatasetGenerator:
    """
    Generador de dataset para predicción de extensión de agua.
    Extrae parches espaciales de GEE con series temporales de índices.
    """
    
    def __init__(
        self,
        catchment: CatchmentConfig = COMBEIMA_CONFIG,
        config: DatasetConfig = None,
        output_dir: str = '../../data/datasets'
    ):
        self.catchment = catchment
        self.config = config or DatasetConfig()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.ee_initialized = False
        self._stats_cache = {}
        
    def initialize_gee(self, service_account: str = None, private_key: str = None) -> bool:
        """
        Inicializa Google Earth Engine.
        
        Args:
            service_account: Email de cuenta de servicio
            private_key: Clave privada JSON
            
        Returns:
            True si la inicialización fue exitosa
        """
        try:
            if service_account and private_key:
                credentials = ee.ServiceAccountCredentials(
                    service_account,
                    private_key
                )
                ee.Initialize(credentials)
            else:
                ee.Initialize()
            
            self.ee_initialized = True
            print(f'GEE inicializado para cuenca {self.catchment.name}')
            return True
            
        except Exception as e:
            print(f'Error inicializando GEE: {e}')
            return False
    
    def _get_geometry(self) -> ee.Geometry:
        """Obtiene geometría de la cuenca."""
        min_lon, min_lat, max_lon, max_lat = self.catchment.bounds
        return ee.Geometry.BBox(min_lon, min_lat, max_lon, max_lat)
    
    def _create_image_collection(
        self,
        start_date: str,
        end_date: str
    ) -> ee.ImageCollection:
        """
        Crea colección de imágenes filtrada.
        
        Args:
            start_date: Fecha de inicio (YYYY-MM-DD)
            end_date: Fecha de fin (YYYY-MM-DD)
            
        Returns:
            ImageCollection filtrada
        """
        collection = ee.ImageCollection(self.catchment.collection) \
            .filterDate(start_date, end_date) \
            .filterBounds(self._get_geometry()) \
            .filter(ee.Filter.lt('CLOUD_COVER', self.config.max_cloud_cover * 100)) \
            .sort('system:time_start')
        
        return collection
    
    def _calculate_indices(self, image: ee.Image) -> ee.Image:
        """
        Calcula índices espectrales para una imagen.
        
        Args:
            image: Imagen de Landsat/Sentinel
            
        Returns:
            Imagen con índices calculados
        """
        nir = image.select('SR_B5').float()
        red = image.select('SR_B4').float()
        green = image.select('SR_B3').float()
        swir1 = image.select('SR_B6').float()
        blue = image.select('SR_B2').float()
        
        ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
        ndwi = green.subtract(nir).divide(green.add(nir)).rename('NDWI')
        
        evi = ee.Image(2.5).multiply(
            nir.subtract(red)
        ).divide(
            nir.add(red.multiply(6)).subtract(swir1.multiply(7.5)).add(1)
        ).rename('EVI')
        
        mndwi = green.subtract(swir1).divide(green.add(swir1)).rename('MNDWI')
        
        return image.addBands([ndvi, ndwi, evi, mndwi])
    
    def extract_time_series(
        self,
        start_date: str,
        end_date: str,
        target_date: str = None
    ) -> Dict[str, np.ndarray]:
        """
        Extrae serie temporal de índices para la cuenca.
        
        Args:
            start_date: Fecha inicio extracción
            end_date: Fecha fin extracción
            target_date: Fecha objetivo (para labels)
            
        Returns:
            Diccionario con arrays de cada índice por fecha
        """
        if not self.ee_initialized:
            raise RuntimeError('GEE no inicializado. Llama initialize_gee() primero.')
        
        collection = self._create_image_collection(start_date, end_date)
        indexed = collection.map(self._calculate_indices)
        
        indices = ['NDVI', 'NDWI', 'EVI', 'MNDWI']
        dates = indexed.aggregate_array('system:time_start').getInfo()
        
        results = {idx: [] for idx in indices}
        results['dates'] = []
        results['metadata'] = []
        
        for i, date_ms in enumerate(tqdm(dates, desc='Extrayendo imágenes')):
            try:
                img = ee.Image(indexed.toList(indexed.size()).get(i))
                
                img_data = img.select(indices).sample(
                    region=self._get_geometry(),
                    scale=self.catchment.resolution_m,
                    numPixels=1000
                ).getInfo()
                
                if img_data['features']:
                    values = {idx: [] for idx in indices}
                    for feat in img_data['features']:
                        props = feat['properties']
                        for idx in indices:
                            if idx in props and props[idx] is not None:
                                values[idx].append(props[idx])
                    
                    for idx in indices:
                        if values[idx]:
                            results[idx].append(np.mean(values[idx]))
                        else:
                            results[idx].append(np.nan)
                    
                    results['dates'].append(
                        datetime.fromtimestamp(date_ms / 1000).strftime('%Y-%m-%d')
                    )
                    results['metadata'].append({
                        'cloud_cover': img.get('CLOUD_COVER').getInfo(),
                        'date': results['dates'][-1]
                    })
                    
            except Exception as e:
                print(f'Error procesando imagen {i}: {e}')
                continue
        
        for idx in indices:
            results[idx] = np.array(results[idx])
        
        return results
    
    def extract_spatial_patches(
        self,
        date: str,
        patch_size: int = None
    ) -> Optional[Dict[str, np.ndarray]]:
        """
        Extrae parches espaciales para una fecha específica.
        
        Args:
            date: Fecha de extracción (YYYY-MM-DD)
            patch_size: Tamaño del parche en píxeles
            
        Returns:
            Diccionario con parches espaciales de cada índice
        """
        if not self.ee_initialized:
            raise RuntimeError('GEE no inicializado')
        
        patch_size = patch_size or self.catchment.patch_size
        
        start = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
        end = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
        
        collection = self._create_image_collection(start, end)
        indexed = collection.map(self._calculate_indices)
        
        image = indexed.median()
        
        bands = ['NDVI', 'NDWI', 'EVI', 'MNDWI']
        
        try:
            url = image.select(bands).getDownloadURL({
                'region': self._get_geometry().bounds().getInfo(),
                'scale': self.catchment.resolution_m,
                'crs': 'EPSG:4326'
            })
            
            import urllib.request
            import zipfile
            import io
            
            response = urllib.request.urlopen(url, timeout=60)
            zip_data = io.BytesIO(response.read())
            
            with zipfile.ZipFile(zip_data) as zf:
                for band in bands:
                    if f'{band}.tif' in zf.namelist():
                        pass
            
            return {'url': url, 'bands': bands}
            
        except Exception as e:
            print(f'Error extrayendo parches: {e}')
            return None
    
    def generate_synthetic_dataset(
        self,
        n_samples: int = 1000,
        seed: int = 42
    ) -> Dict[str, np.ndarray]:
        """
        Genera dataset sintético para pruebas/validación del pipeline.
        
        Args:
            n_samples: Número de muestras a generar
            seed: Semilla aleatoria
            
        Returns:
            Diccionario con datos de entrenamiento
        """
        np.random.seed(seed)
        
        n_timesteps = self.config.sequence_length + max(self.config.horizons)
        patch_size = self.catchment.patch_size
        
        indices = ['NDVI', 'NDWI', 'EVI', 'MNDWI']
        climate_vars = ['precipitation', 'temperature', 'humidity']
        
        data = {
            'X_satellite': [],
            'X_climate': [],
            'X_static': [],
            'y_water_mask': [],
            'metadata': []
        }
        
        print(f'Generando {n_samples} muestras sintéticas...')
        
        for i in tqdm(range(n_samples)):
            base_ndwi = np.random.uniform(-0.2, 0.5)
            has_water = base_ndwi > 0.0
            
            sat_seq = []
            for t in range(n_timesteps):
                temporal_factor = np.sin(2 * np.pi * t / 365) if t < 365 else 0
                noise = np.random.normal(0, 0.1, (patch_size, patch_size))
                
                ndwi_map = base_ndwi + temporal_factor * 0.1 + noise
                
                if has_water and t > self.config.sequence_length:
                    water_mask = ndwi_map > 0
                    ndwi_map[water_mask] += np.random.uniform(0.05, 0.2)
                
                ndvi_map = 0.3 + temporal_factor * 0.1 + np.random.normal(0, 0.05, (patch_size, patch_size))
                ndvi_map = np.clip(ndvi_map, -1, 1)
                
                evi_map = 0.4 + temporal_factor * 0.1 + np.random.normal(0, 0.05, (patch_size, patch_size))
                evi_map = np.clip(evi_map, -1, 1)
                
                mndwi_map = ndwi_map * 0.95 + np.random.normal(0, 0.02, (patch_size, patch_size))
                mndwi_map = np.clip(mndwi_map, -1, 1)
                
                sat_seq.append(np.stack([ndvi_map, ndwi_map, evi_map, mndwi_map], axis=-1))
            
            sat_seq = np.array(sat_seq)
            
            climate_seq = []
            for t in range(n_timesteps):
                precip = np.random.exponential(5) if temporal_factor > 0 else np.random.exponential(2)
                temp = 22 + 5 * np.sin(2 * np.pi * t / 365) + np.random.normal(0, 2)
                humidity = 70 + 15 * np.sin(2 * np.pi * t / 365) + np.random.normal(0, 5)
                humidity = np.clip(humidity, 30, 100)
                climate_seq.append([precip, temp, humidity])
            climate_seq = np.array(climate_seq)
            
            static_features = np.array([
                np.random.uniform(500, 3000),
                np.random.uniform(5, 30),
                np.random.uniform(0.1, 0.5),
                patch_size // 2,
                patch_size // 2
            ])
            
            future_ndwi = sat_seq[self.config.sequence_length + self.config.horizons[0] - 1, :, :, 1]
            water_mask = (future_ndwi > 0.1).astype(np.float32)
            
            data['X_satellite'].append(sat_seq[:self.config.sequence_length])
            data['X_climate'].append(climate_seq[:self.config.sequence_length])
            data['X_static'].append(static_features)
            data['y_water_mask'].append(water_mask)
            data['metadata'].append({
                'sample_id': i,
                'base_ndwi': float(base_ndwi),
                'has_water': bool(has_water)
            })
        
        return {
            'X_satellite': np.array(data['X_satellite']),
            'X_climate': np.array(data['X_climate']),
            'X_static': np.array(data['X_static']),
            'y_water_mask': np.array(data['y_water_mask']),
            'metadata': data['metadata']
        }
    
    def prepare_sequences(
        self,
        data: Dict[str, np.ndarray],
        horizon: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepara secuencias de entrenamiento para un horizonte específico.
        
        Args:
            data: Diccionario con datos
            horizon: Horizonte de predicción en días
            
        Returns:
            Tuple de (X, y) listos para entrenamiento
        """
        idx = self.config.horizons.index(horizon)
        offset = horizon
        
        X_sat = data['X_satellite'][:, :self.config.sequence_length]
        X_clim = data['X_climate'][:, :self.config.sequence_length]
        X_static = data['X_static']
        
        future_ndwis = []
        for i in range(len(data['y_water_mask'])):
            future_idx = self.config.sequence_length + offset - self.config.horizons[0]
            if future_idx < len(data['X_satellite'][i]):
                future_ndwi = data['X_satellite'][i, future_idx, :, :, 1]
            else:
                future_ndwi = data['y_water_mask'][i]
            future_ndwis.append(future_ndwi)
        
        y = np.array([
            (ndwi > 0.1).astype(np.float32) 
            for ndwi in future_ndwis
        ])
        
        horizon_map = {7: 0, 14: 1, 30: 2}
        horizon_idx = horizon_map.get(horizon, 0)
        
        X = {
            'satellite_input': X_sat,
            'climate_input': X_clim,
            'static_input': X_static,
            'horizon_input': np.full(len(X_sat), horizon_idx)
        }
        
        return X, y
    
    def split_dataset(
        self,
        X: Dict[str, np.ndarray],
        y: np.ndarray
    ) -> Tuple[Dict, Dict, Dict, np.ndarray, np.ndarray, np.ndarray]:
        """
        Divide dataset en train/val/test siguiendo orden temporal.
        
        Args:
            X: Datos de entrada
            y: Labels
            
        Returns:
            Tupla de (X_train, X_val, X_test, y_train, y_val, y_test)
        """
        n_samples = len(y)
        train_end = int(n_samples * self.config.train_ratio)
        val_end = int(n_samples * (self.config.train_ratio + self.config.val_ratio))
        
        def subset_X(X_dict, start, end):
            return {k: v[start:end] for k, v in X_dict.items()}
        
        return (
            subset_X(X, 0, train_end),
            subset_X(X, train_end, val_end),
            subset_X(X, val_end, n_samples),
            y[0:train_end],
            y[train_end:val_end],
            y[val_end:n_samples]
        )
    
    def save_dataset(
        self,
        data: Dict[str, np.ndarray],
        name: str = 'water_extension_dataset'
    ):
        """
        Guarda dataset en disco.
        
        Args:
            data: Diccionario con datos
            name: Nombre del dataset
        """
        dataset_path = self.output_dir / name
        dataset_path.mkdir(parents=True, exist_ok=True)
        
        np.savez_compressed(
            dataset_path / 'satellite_data.npz',
            **{k: v for k, v in data.items() if k == 'X_satellite'}
        )
        
        np.savez_compressed(
            dataset_path / 'climate_data.npz',
            **{k: v for k, v in data.items() if k == 'X_climate'}
        )
        
        np.save(
            dataset_path / 'static_features.npy',
            data['X_static']
        )
        
        np.save(
            dataset_path / 'water_masks.npy',
            data['y_water_mask']
        )
        
        with open(dataset_path / 'metadata.json', 'w') as f:
            json.dump({
                'created_at': datetime.now().isoformat(),
                'catchment': self.catchment.name,
                'config': {
                    'sequence_length': self.config.sequence_length,
                    'horizons': self.config.horizons,
                    'patch_size': self.catchment.patch_size
                },
                'metadata': data.get('metadata', [])
            }, f, indent=2)
        
        print(f'Dataset guardado en {dataset_path}')
    
    def load_dataset(self, name: str = 'water_extension_dataset') -> Dict[str, np.ndarray]:
        """
        Carga dataset desde disco.
        
        Args:
            name: Nombre del dataset
            
        Returns:
            Diccionario con datos cargados
        """
        dataset_path = self.output_dir / name
        
        satellite_data = np.load(dataset_path / 'satellite_data.npz')
        climate_data = np.load(dataset_path / 'climate_data.npz')
        static_features = np.load(dataset_path / 'static_features.npy')
        water_masks = np.load(dataset_path / 'water_masks.npy')
        
        with open(dataset_path / 'metadata.json', 'r') as f:
            metadata = json.load(f)
        
        return {
            'X_satellite': satellite_data['X_satellite'],
            'X_climate': climate_data['X_climate'],
            'X_static': static_features,
            'y_water_mask': water_masks,
            'metadata': metadata['metadata']
        }


def download_jrc_water_classification(
    start_date: str,
    end_date: str,
    geometry: ee.Geometry,
    scale: int = 30
) -> ee.ImageCollection:
    """
    Descarga datos de clasificación de agua JRC para labels.
    
    Args:
        start_date: Fecha inicio
        end_date: Fecha fin
        geometry: Geometría de la cuenca
        scale: Resolución espacial
        
    Returns:
        ImageCollection con máscaras de agua
    """
    jrc_collection = ee.ImageCollection('JRC/GSW1_3/YearlyHistory') \
        .filterDate(start_date, end_date) \
        .filterBounds(geometry)
    
    return jrc_collection


if __name__ == '__main__':
    generator = WaterDatasetGenerator()
    
    print('Generando dataset sintético para validación...')
    data = generator.generate_synthetic_dataset(n_samples=500)
    
    print('\nPreparando secuencias para horizonte 7 días...')
    X, y = generator.prepare_sequences(data, horizon=7)
    
    print(f'X_satellite shape: {X["satellite_input"].shape}')
    print(f'X_climate shape: {X["climate_input"].shape}')
    print(f'X_static shape: {X["static_input"].shape}')
    print(f'y shape: {y.shape}')
    
    print('\nDiviendo dataset...')
    X_train, X_val, X_test, y_train, y_val, y_test = generator.split_dataset(X, y)
    
    print(f'Train: {len(y_train)}, Val: {len(y_val)}, Test: {len(y_test)}')
    
    print('\nGuardando dataset...')
    generator.save_dataset(data)
    
    print('Dataset preparado exitosamente!')
