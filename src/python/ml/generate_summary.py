"""
Script para generar resumen interpretativo de métricas del modelo LSTM
usando un LLM (OpenAI GPT-4).
"""

import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI

MODEL_PATH = Path("src/data/models/caudal_predictor/validation_results.json")
OUTPUT_PATH = Path("docs/analysis_summary.txt")

PROMPT_TEMPLATE = """Eres un experto en hidrología y aprendizaje automático. Analiza los siguientes resultados de un modelo LSTM para predicción de caudales históricos (1969-2023) en la cuenca del río Combeima:

Métricas de validación:
- RMSE: {rmse:.2f} m³/s
- R²: {r2:.4f}
- NSE: {nse:.4f}
- KGE: {kge:.4f}
- MAPE: {mape:.2f}%
- P-Bias: {pbias:.2f}%
- MAE: {mae:.2f} m³/s

Contexto adicional:
- El modelo utiliza secuencias de 30 días de características: caudal histórico, precipitación y anchura del río (generada por Vision Agent)
- Arquitectura: LSTM apilado (2 capas de 64 unidades) con dropout y batch normalization
- Datos: 70% entrenamiento, 15% validación, 15% prueba (división temporal)
- El RMSE de ~5.4 m³/s representa aproximadamente el {rmse_percent:.1f}% del caudal medio característico de la cuenca

Redacta un resumen ejecutivo de 3-4 oraciones que:
1. Interprete qué significan estas métricas para la precisión del modelo
2. Evalúe si el rendimiento es adecuado para aplicaciones prácticas de monitoreo hidrológico
3. Sugiera una dirección futura de mejora basada en los resultados

Usa lenguaje técnico pero accesible para gestores de recursos hídricos.
"""


def load_metrics():
    with open(MODEL_PATH, 'r') as f:
        data = json.load(f)
    return data['metrics']


def generate_summary(metrics):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    prompt = PROMPT_TEMPLATE.format(
        rmse=metrics['rmse'],
        r2=metrics['r2'],
        nse=metrics['nse'],
        kge=metrics['kge'],
        mape=metrics['mape'],
        pbias=metrics['pbias'],
        mae=metrics['mae'],
        rmse_percent=(metrics['rmse'] / 50) * 100
    )
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=200
    )
    
    return response.choices[0].message.content


def save_summary(summary):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(f"# Resumen de Análisis del Modelo LSTM - Caudal Predictor\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Resumen Ejecutivo\n\n")
        f.write(summary)
        f.write("\n\n## Métricas de Validación\n\n")
        f.write(f"| Métrica | Valor |\n")
        f.write(f"|---------|-------|\n")
        
        with open(MODEL_PATH, 'r') as f:
            data = json.load(f)
            metrics = data['metrics']
        
        for key, value in metrics.items():
            if key in ['rmse', 'mae']:
                f.write(f"| {key.upper()} | {value:.4f} m³/s |\n")
            else:
                f.write(f"| {key.upper()} | {value:.4f} |\n")
    
    print(f"Resumen guardado en: {OUTPUT_PATH}")


def main():
    print("=" * 60)
    print("GENERACIÓN DE RESUMEN CON LLM")
    print("=" * 60)
    
    print("\nCargando métricas...")
    metrics = load_metrics()
    
    print(f"RMSE: {metrics['rmse']:.4f}")
    print(f"R²: {metrics['r2']:.4f}")
    print(f"NSE: {metrics['nse']:.4f}")
    print(f"KGE: {metrics['kge']:.4f}")
    
    print("\nGenerando resumen con GPT-4...")
    summary = generate_summary(metrics)
    
    print("\n" + "=" * 60)
    print("RESUMEN GENERADO")
    print("=" * 60)
    print(summary)
    
    save_summary(summary)
    
    print("\n" + "=" * 60)
    print("PROCESO COMPLETADO")
    print("=" * 60)


if __name__ == "__main__":
    main()
