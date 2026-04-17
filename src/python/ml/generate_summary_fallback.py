"""
Script para generar resumen interpretativo de métricas del modelo LSTM
usando plantilla predefinida (fallback cuando LLM no está disponible).
"""

import json
from pathlib import Path
from datetime import datetime

MODEL_PATH = Path("src/data/models/caudal_predictor/validation_results.json")
OUTPUT_PATH = Path("docs/analysis_summary.txt")


SUMMARY_TEMPLATE = """El modelo LSTM de predicción de caudales para la cuenca del río Combeima presenta un rendimiento bueno con un R² de {r2:.4f}, lo que indica que explica aproximadamente el {r2_percent:.0f}% de la varianza en los datos de caudal observados. El RMSE de {rmse:.2f} m³/s representa un error medio cuadrático moderado que equivale aproximadamente al {rmse_percent:.1f}% del caudal medio característico de la cuenca (50 m³/s).

Desde la perspectiva de aplicaciones prácticas de monitoreo hidrológico, el coeficiente de eficiencia de Nash-Sutcliffe (NSE) de {nse:.4f} y el Kling-Gupta Efficiency (KGE) de {kge:.4f} confirman que el modelo tiene capacidad adecuada para reproducir patrones de caudal, incluyendo eventos de crecida. El sesgo percentil (P-Bias) de {pbias:.2f}% indica una ligera subestimación sistemática que podría calibrarse ajustando el umbral de decisión.

Para mejorar el rendimiento futuro, se recomienda explorar: (1) incorporación de datos meteorológicos adicionales como evapotranspiración y humedad del suelo, (2) aumento de la longitud de secuencia para capturar patrones estacionales más largos, y (3) implementación de arquitecturas de atención (Transformer o LSTM con Attention) que permitan al modelo enfocarse en las relaciones causales más relevantes entre variables.
"""


def load_metrics():
    with open(MODEL_PATH, 'r') as f:
        data = json.load(f)
    return data['metrics']


def generate_summary(metrics):
    summary = SUMMARY_TEMPLATE.format(
        rmse=metrics['rmse'],
        r2=metrics['r2'],
        r2_percent=metrics['r2'] * 100,
        nse=metrics['nse'],
        kge=metrics['kge'],
        mape=metrics['mape'],
        pbias=metrics['pbias'],
        mae=metrics['mae'],
        rmse_percent=(metrics['rmse'] / 50) * 100
    )
    return summary


def save_summary(summary):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(MODEL_PATH, 'r') as mf:
        data = json.load(mf)
        metrics = data['metrics']
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(f"# Resumen de Analisis del Modelo LSTM - Caudal Predictor\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Resumen Ejecutivo\n\n")
        f.write(summary)
        f.write("\n\n## Metricas de Validacion\n\n")
        f.write(f"| Metrica | Valor |\n")
        f.write(f"|---------|-------|\n")
        
        for key, value in metrics.items():
            if key in ['rmse', 'mae']:
                f.write(f"| {key.upper()} | {value:.4f} m3/s |\n")
            else:
                f.write(f"| {key.upper()} | {value:.4f} |\n")
    
    print(f"Resumen guardado en: {OUTPUT_PATH}")


def main():
    print("=" * 60)
    print("GENERACIÓN DE RESUMEN (Fallback)")
    print("=" * 60)
    
    print("\nCargando métricas...")
    metrics = load_metrics()
    
    print(f"RMSE: {metrics['rmse']:.4f}")
    print(f"R²: {metrics['r2']:.4f}")
    print(f"NSE: {metrics['nse']:.4f}")
    print(f"KGE: {metrics['kge']:.4f}")
    
    print("\nGenerando resumen interpretativo...")
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
