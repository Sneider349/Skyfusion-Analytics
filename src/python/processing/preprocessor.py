"""
Preprocessor de Línea Base Histórica Satelital
===============================================
Skyfusion Analytics - Data Engineering Pipeline

Script para ingestión automática de imágenes satelitales históricas
(1969-2023) de la cuenca del río Combeima desde Google Earth Engine.

Colecciones procesadas:
- Landsat MSS (1972-1983)
- Landsat TM (1984-2012)
- Landsat OLI/TIRS (2013-presente)
- Sentinel-2 MSI (2015-presente)

Autor: Skyfusion Analytics - Geospatial Agent
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import time

os.environ.setdefault('EE_AUTHENTICATION_MODE', 'SA_KEY')
os.environ.setdefault('GOOGLE_APPLICATION_CREDENTIALS', os.getenv('GEE_SERVICE_ACCOUNT_KEY', ''))

import ee
import pika
import redis

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Config:
    """Configuración centralizada del preprocessor"""
    
    PROJECT_ID = os.getenv('GEE_PROJECT_ID', 'skyfusion-analytics')
    ASSET_BASE_PATH = f'projects/{PROJECT_ID}/assets/combeima_historico'
    
    EVENT_BUS_TYPE = os.getenv('EVENT_BUS_TYPE', 'rabbitmq')
    EVENT_EXCHANGE = os.getenv('EVENT_EXCHANGE', 'geo_events')
    EVENT_ROUTING_KEY = 'imagenes.historicas.listas'
    EVENT_QUEUE = 'historico_queue'
    
    RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    CLOUD_COVER_THRESHOLD = float(os.getenv('CLOUD_COVER_THRESHOLD', '15'))
    
    DATE_RANGE = {
        'start': '1969-01-01',
        'end': '2023-12-31'
    }


class CuencaCombeima:
    """Definición geoespacial de la cuenca del río Combeima"""
    
    COORDENADAS_POLIGONO = [
        [-75.39860512458093, 4.626781362858553],
        [-75.36561705270782, 4.44414396728246],
        [-75.22767063344737, 4.459521688554666],
        [-75.28433707660506, 4.639038110771378],
        [-75.39860512458093, 4.626781362858553]
    ]
    
    BBOX = {
        'lon_min': -75.39860512458093,
        'lat_min': 4.44414396728246,
        'lon_max': -75.22767063344737,
        'lat_max': 4.639038110771378
    }
    
    @classmethod
    def get_geometry(cls) -> ee.Geometry:
        """Retorna la geometría de la cuenca como polígono ee.Geometry"""
        return ee.Geometry.Polygon(cls.COORDENADAS_POLIGONO)
    
    @classmethod
    def get_bbox(cls) -> List[float]:
        """Retorna bounding box [lon_min, lat_min, lon_max, lat_max]"""
        return [
            cls.BBOX['lon_min'],
            cls.BBOX['lat_min'],
            cls.BBOX['lon_max'],
            cls.BBOX['lat_max']
        ]


class ColeccionesSatelitales:
    """Definición de colecciones satelitales de Google Earth Engine"""
    
    LANDSAT_MSS = {
        'id': 'LANDSAT/LM01/C01/T1',
        'name': 'LANDSAT_MSS',
        'display_name': 'Landsat 1-3 Multispectral Scanner',
        'date_start': '1972-01-01',
        'date_end': '1983-12-31',
        'cloud_property': 'CLOUD_COVER',
        'resolution': 60,
        'bands': ['B4', 'B5', 'B6', 'B7']
    }
    
    LANDSAT_TM = {
        'id': 'LANDSAT/LT04/C01/T1',
        'name': 'LANDSAT_TM',
        'display_name': 'Landsat 4-5 Thematic Mapper',
        'date_start': '1984-01-01',
        'date_end': '2012-12-31',
        'cloud_property': 'CLOUD_COVER',
        'resolution': 30,
        'bands': ['B1', 'B2', 'B3', 'B4', 'B5', 'B7']
    }
    
    LANDSAT_OLI = {
        'id': 'LANDSAT/LC08/C01/T1_TOA',
        'name': 'LANDSAT_OLI',
        'display_name': 'Landsat 8-9 OLI/TIRS',
        'date_start': '2013-04-01',
        'date_end': '2023-12-31',
        'cloud_property': 'CLOUD_COVER',
        'resolution': 30,
        'bands': ['B2', 'B3', 'B4', 'B5', 'B6', 'B7']
    }
    
    SENTINEL2 = {
        'id': 'COPERNICUS/S2_SR',
        'name': 'SENTINEL2_SR',
        'display_name': 'Sentinel-2 MSI',
        'date_start': '2015-06-01',
        'date_end': '2023-12-31',
        'cloud_property': 'CLOUDY_PIXEL_PERCENTAGE',
        'resolution': 10,
        'bands': ['B2', 'B3', 'B4', 'B8', 'B11', 'B12']
    }
    
    COLECCIONES = [LANDSAT_MSS, LANDSAT_TM, LANDSAT_OLI, SENTINEL2]


class EventBusPublisher:
    """Publicador de eventos para RabbitMQ o Redis"""
    
    def __init__(self, config: Config):
        self.config = config
        self.connection = None
        self.channel = None
        self.redis_client = None
    
    def connect(self):
        """Establece conexión con el bus de eventos"""
        if self.config.EVENT_BUS_TYPE == 'rabbitmq':
            self._connect_rabbitmq()
        elif self.config.EVENT_BUS_TYPE == 'redis':
            self._connect_redis()
        else:
            raise ValueError(f"Tipo de bus de eventos no soportado: {self.config.EVENT_BUS_TYPE}")
    
    def _connect_rabbitmq(self):
        """Conexión a RabbitMQ"""
        try:
            params = pika.URLParameters(self.config.RABBITMQ_URL)
            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()
            
            self.channel.exchange_declare(
                exchange=self.config.EVENT_EXCHANGE,
                exchange_type='topic',
                durable=True
            )
            
            self.channel.queue_declare(queue=self.config.EVENT_QUEUE, durable=True)
            self.channel.queue_bind(
                exchange=self.config.EVENT_EXCHANGE,
                queue=self.config.EVENT_QUEUE,
                routing_key=self.config.EVENT_ROUTING_KEY
            )
            
            logger.info("Conexión establecida con RabbitMQ")
        except Exception as e:
            logger.error(f"Error conectando a RabbitMQ: {e}")
            raise
    
    def _connect_redis(self):
        """Conexión a Redis Pub/Sub"""
        try:
            self.redis_client = redis.from_url(
                self.config.REDIS_URL,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Conexión establecida con Redis")
        except Exception as e:
            logger.error(f"Error conectando a Redis: {e}")
            raise
    
    def publish(self, payload: Dict[str, Any]):
        """Publica el payload en el bus de eventos"""
        message = json.dumps(payload, default=str)
        
        if self.config.EVENT_BUS_TYPE == 'rabbitmq':
            self.channel.basic_publish(
                exchange=self.config.EVENT_EXCHANGE,
                routing_key=self.config.EVENT_ROUTING_KEY,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json',
                    timestamp=int(time.time())
                )
            )
        elif self.config.EVENT_BUS_TYPE == 'redis':
            self.redis_client.publish(self.config.EVENT_ROUTING_KEY, message)
        
        logger.info(f"Evento publicado: {self.config.EVENT_ROUTING_KEY}")
    
    def close(self):
        """Cierra conexiones"""
        if self.connection and self.connection.is_open:
            self.connection.close()
        if self.redis_client:
            self.redis_client.close()


class GEEPreprocessor:
    """Preprocessor principal para Google Earth Engine"""
    
    def __init__(self, config: Config):
        self.config = config
        self.geometria = CuencaCombeima.get_geometry()
        self.reporte = self._inicializar_reporte()
    
    def _inicializar_reporte(self) -> Dict[str, Any]:
        """Inicializa el reporte de procesamiento"""
        return {
            'cuenca': 'Combeima',
            'geometria': {
                'tipo': 'Polígono',
                'coordenadas': CuencaCombeima.COORDENADAS_POLIGONO,
                'bbox': CuencaCombeima.get_bbox()
            },
            'rango_fechas': self.config.DATE_RANGE,
            'umbral_nubosidad': self.config.CLOUD_COVER_THRESHOLD,
            'colecciones': {},
            'total_imagenes_encontradas': 0,
            'total_imagenes_validas': 0,
            'assets_creados': [],
            'errores': [],
            'timestamp_inicio': datetime.now().isoformat(),
            'timestamp_fin': None
        }
    
    def inicializar_gee(self):
        """Autentica e inicializa Google Earth Engine"""
        try:
            if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                credentials = ee.ServiceAccountCredentials(
                    None,
                    os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                )
                ee.Initialize(credentials, project=self.config.PROJECT_ID)
            else:
                ee.Initialize(project=self.config.PROJECT_ID)
            
            logger.info("Google Earth Engine inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando GEE: {e}")
            raise
    
    def procesar_coleccion(self, coleccion: Dict) -> List[Dict]:
        """Procesa una colección satelital individual"""
        logger.info(f"Procesando colección: {coleccion['display_name']}")
        
        try:
            dataset = ee.ImageCollection(coleccion['id'])
            
            fecha_inicio = max(coleccion['date_start'], self.config.DATE_RANGE['start'])
            fecha_fin = min(coleccion['date_end'], self.config.DATE_RANGE['end'])
            
            filtered = (
                dataset
                .filterDate(fecha_inicio, fecha_fin)
                .filterBounds(self.geometria)
                .filter(ee.Filter.lt(coleccion['cloud_property'], self.config.CLOUD_COVER_THRESHOLD))
            )
            
            count = filtered.size().getInfo()
            logger.info(f"  Imágenes encontradas: {count} (nubosidad < {self.config.CLOUD_COVER_THRESHOLD}%)")
            
            if count == 0:
                self.reporte['colecciones'][coleccion['name']] = {
                    'encontradas': 0,
                    'validas': 0,
                    'rango_fechas': {'inicio': fecha_inicio, 'fin': fecha_fin}
                }
                return []
            
            image_list = filtered.toList(count)
            imagenes_validas = []
            
            for i in range(count):
                try:
                    img = ee.Image(image_list.get(i))
                    img_id = img.get('system:index').getInfo()
                    fecha = img.get('system:time_start').getInfo()
                    cloud_cover = img.get(coleccion['cloud_property']).getInfo()
                    
                    asset_id = f"{self.config.ASSET_BASE_PATH}/{coleccion['name']}/{img_id}"
                    
                    imagen_info = {
                        'id': img_id,
                        'asset_id': asset_id,
                        'fecha': datetime.fromtimestamp(fecha / 1000).strftime('%Y-%m-%d'),
                        'nubosidad': cloud_cover,
                        'coleccion': coleccion['name'],
                        'resolution': coleccion['resolution']
                    }
                    
                    self._exportar_asset(img, asset_id, coleccion)
                    imagenes_validas.append(imagen_info)
                    self.reporte['assets_creados'].append(asset_id)
                    
                except Exception as e:
                    error_msg = f"Error procesando imagen {i} en {coleccion['name']}: {str(e)}"
                    logger.warning(error_msg)
                    self.reporte['errores'].append(error_msg)
            
            self.reporte['colecciones'][coleccion['name']] = {
                'display_name': coleccion['display_name'],
                'id_gee': coleccion['id'],
                'encontradas': count,
                'validas': len(imagenes_validas),
                'rango_fechas': {'inicio': fecha_inicio, 'fin': fecha_fin}
            }
            
            self.reporte['total_imagenes_encontradas'] += count
            self.reporte['total_imagenes_validas'] += len(imagenes_validas)
            
            return imagenes_validas
            
        except Exception as e:
            error_msg = f"Error en colección {coleccion['name']}: {str(e)}"
            logger.error(error_msg)
            self.reporte['errores'].append(error_msg)
            return []
    
    def _exportar_asset(self, imagen: ee.Image, asset_id: str, coleccion: Dict):
        """Exporta una imagen como asset en GEE"""
        task_config = {
            'description': f'Combeima_{coleccion["name"]}_{asset_id.split("/")[-1]}',
            'assetId': asset_id,
            'pyramidingPolicy': {'*.': 'mean'},
            'dimensions': None,
            'region': self.geometria,
            'scale': coleccion['resolution'],
            'maxPixels': 1e10,
            'crs': 'EPSG:4326'
        }
        
        task = ee.batch.Export.image.toAsset(image=imagen, **task_config)
        task.start()
        
        logger.debug(f"Export iniciada: {asset_id}")
    
    def ejecutar_pipeline(self, colecciones: List[Dict] = None) -> Dict[str, Any]:
        """Ejecuta el pipeline completo de procesamiento"""
        logger.info("=" * 60)
        logger.info("INICIANDO PIPELINE DE PREPROCESAMIENTO SATELITAL")
        logger.info("=" * 60)
        
        if colecciones is None:
            colecciones = ColeccionesSatelitales.COLECCIONES
        
        self.inicializar_gee()
        
        todas_imagenes = []
        for coleccion in colecciones:
            imagenes = self.procesar_coleccion(coleccion)
            todas_imagenes.extend(imagenes)
        
        self.reporte['timestamp_fin'] = datetime.now().isoformat()
        self.reporte['total_imagenes_procesadas'] = len(todas_imagenes)
        
        logger.info("=" * 60)
        logger.info("RESUMEN DEL PROCESAMIENTO")
        logger.info("=" * 60)
        logger.info(f"Total imágenes encontradas: {self.reporte['total_imagenes_encontradas']}")
        logger.info(f"Total imágenes válidas: {self.reporte['total_imagenes_validas']}")
        logger.info(f"Assets creados: {len(self.reporte['assets_creados'])}")
        logger.info(f"Errores: {len(self.reporte['errores'])}")
        
        return self.reporte
    
    def guardar_reporte(self, output_path: str = None):
        """Guarda el reporte en un archivo JSON"""
        if output_path is None:
            output_path = f"data/output/reporte_historico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.reporte, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Reporte guardado en: {output_path}")
        return output_path


class PipelineCoordinator:
    """Coordinador principal del pipeline"""
    
    def __init__(self):
        self.config = Config()
        self.preprocessor = GEEPreprocessor(self.config)
        self.publisher = EventBusPublisher(self.config)
    
    def ejecutar(self):
        """Ejecuta el pipeline completo y emite el evento"""
        try:
            reporte = self.preprocessor.ejecutar_pipeline()
            
            reporte_path = self.preprocessor.guardar_reporte()
            reporte['reporte_path'] = reporte_path
            
            self.publisher.connect()
            self.publisher.publish(reporte)
            
            logger.info("=" * 60)
            logger.info("EVENTO IMAGENES_HISTORICAS_LISTAS EMITIDO")
            logger.info(f"Tipo de bus: {self.config.EVENT_BUS_TYPE}")
            logger.info(f"Exchange/Canal: {self.config.EVENT_EXCHANGE}/{self.config.EVENT_ROUTING_KEY}")
            logger.info("=" * 60)
            
            return reporte
            
        except Exception as e:
            logger.error(f"Error en el pipeline: {e}")
            raise
        finally:
            self.publisher.close()


def main():
    """Función principal de ejecución"""
    coordinator = PipelineCoordinator()
    reporte = coordinator.ejecutar()
    
    print("\n" + "=" * 60)
    print("REPORTE FINAL DE PROCESAMIENTO")
    print("=" * 60)
    print(json.dumps(reporte, indent=2, default=str))
    
    return reporte


if __name__ == '__main__':
    main()
