"""
Script de Inferencia para Predicción de Extensión de Agua
Skyfusion Analytics - CNN-LSTM-Attention

Este script carga el modelo entrenado y realiza predicciones.
"""

import os
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from water_extension_model import WaterExtensionModel
from data_generator import WaterDatasetGenerator


def load_model_and_predict(input_data, model_name='water_extension_model'):
    """
    Carga el modelo y realiza predicción.
    
    Args:
        input_data: Diccionario con datos de entrada
        model_name: Nombre del modelo
        
    Returns:
        Diccionario con predicciones
    """
    model_path = Path(__file__).parent.parent.parent / 'data' / 'models'
    
    model = WaterExtensionModel(
        sequence_length=input_data.get('sequence_length', 10),
        patch_size=input_data.get('patch_size', 64),
        model_path=str(model_path)
    )
    
    try:
        model.load_model(model_name)
        print(f'Modelo {model_name} cargado exitosamente', file=sys.stderr)
    except Exception as e:
        print(f'Error cargando modelo: {e}', file=sys.stderr)
        print('Generando predicción con datos de entrada...', file=sys.stderr)
        
        return generate_simple_prediction(input_data)
    
    X = {
        'satellite_input': np.array(input_data['satellite_sequence']),
        'climate_input': np.array(input_data['climate_sequence']),
        'static_input': np.array(input_data['static_features']),
        'horizon_input': np.array([[input_data.get('horizon_idx', 0)]] * len(input_data['satellite_sequence']))
    }
    
    predictions = model.predict(X, threshold=0.5)
    
    return {
        'probabilities': predictions['probabilities'].tolist(),
        'water_area_ratio': predictions['water_area_ratio'].tolist(),
        'confidence': predictions['confidence'].tolist(),
        'horizon': input_data.get('horizon', 7)
    }


def generate_simple_prediction(input_data):
    """
    Genera predicción simple basada en heurísticas cuando el modelo no está disponible.
    
    Args:
        input_data: Datos de entrada
        
    Returns:
        Predicción heurística
    """
    sequence = input_data.get('satellite_sequence', [])
    
    if len(sequence) > 0:
        avg_ndwi = np.mean([s.get('ndwi', 0.3) for s in sequence])
        avg_ndvi = np.mean([s.get('ndvi', 0.5) for s in sequence])
    else:
        avg_ndwi = 0.3
        avg_ndvi = 0.5
    
    water_probability = max(0.1, min(0.9, (avg_ndwi + 0.5) / 2))
    
    patch_size = input_data.get('patch_size', 64)
    
    prob_map = np.full((1, patch_size, patch_size, 1), water_probability * 0.3)
    
    return {
        'probabilities': prob_map.tolist(),
        'water_area_ratio': [water_probability * 0.3],
        'confidence': [0.5],
        'horizon': input_data.get('horizon', 7),
        'fallback': True
    }


def main():
    parser = argparse.ArgumentParser(description='Inferencia de extensión de agua')
    parser.add_argument('--input', type=str, help='Archivo JSON de entrada')
    parser.add_argument('--model', type=str, default='water_extension_model', help='Nombre del modelo')
    parser.add_argument('--horizon', type=int, default=7, help='Horizonte de predicción')
    
    args = parser.parse_args()
    
    if args.input:
        with open(args.input, 'r') as f:
            input_data = json.load(f)
    else:
        input_text = sys.stdin.read()
        input_data = json.loads(input_text)
    
    result = load_model_and_predict(input_data, args.model)
    
    print(json.dumps(result))


if __name__ == '__main__':
    main()
