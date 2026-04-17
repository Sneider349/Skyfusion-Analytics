"""
Script para generar datos sintéticos de demostración
para el modelo de predicción de caudales.
"""

import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

dates = pd.date_range(start='1969-01-01', end='2023-12-31', freq='D')
n = len(dates)

base_caudal = 50.0
seasonal = 20.0 * np.sin(2 * np.pi * np.arange(n) / 365)
trend = np.linspace(0, 10, n)
noise = np.random.normal(0, 5, n)

caudal = base_caudal + seasonal + trend + noise
caudal = np.clip(caudal, 5, 150)

precipitation = np.random.exponential(10, n)
precipitation = np.clip(precipitation, 0, 100)

river_width = 15.0 + 5.0 * np.sin(2 * np.pi * np.arange(n) / 365) + \
             0.3 * (caudal - base_caudal) + np.random.normal(0, 2, n)
river_width = np.clip(river_width, 5, 50)

df_caudal = pd.DataFrame({
    'date': dates,
    'caudal': caudal
})

df_precip = pd.DataFrame({
    'date': dates,
    'precipitation': precipitation
})

df_width = pd.DataFrame({
    'date': dates,
    'width': river_width
})

output_dir = Path(__file__).parent.parent.parent / 'data' / 'historical'
output_dir.mkdir(parents=True, exist_ok=True)

df_caudal.to_csv(output_dir / 'streamflow.csv', index=False)
df_precip.to_csv(output_dir / 'precipitation.csv', index=False)
df_width.to_csv(output_dir / 'river_width.csv', index=False)

print(f"Datos sintéticos generados:")
print(f"  - streamflow.csv: {len(df_caudal)} registros")
print(f"  - precipitation.csv: {len(df_precip)} registros")
print(f"  - river_width.csv: {len(df_width)} registros")
print(f"  - Ubicación: {output_dir}")
