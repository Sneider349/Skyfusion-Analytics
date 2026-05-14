# Resumen Comparativo de Experimentos - Modelo LSTM Caudal Predictor

Fecha: 2026-04-16

## Modelos Evaluados

| Modelo | RMSE | R² | NSE | KGE | Observación |
|--------|------|----|-----|-----|-------------|
| **Baseline (Stacked LSTM, seq=30)** | **5.4462** | **0.8698** | **0.8698** | **0.8325** | **MEJOR** |
| Seq 60 días | 6.1278 | 0.8351 | 0.8351 | 0.7372 | Peor (+12.5% RMSE) |
| Features Adicionales (ET+SM) | Falló | - | - | - | Datos sintéticos inconsistentes |
| LSTM + Attention | 8.5740 | 0.6774 | 0.6774 | 0.6153 | Mucho peor (+57% RMSE) |

## Análisis de Resultados

### Prueba 1: Longitud de Secuencia 60 días
- **Resultado**: PEOR que baseline
- **Causa probable**: Más días de secuencia introducen más ruido y reducen la cantidad de datos de entrenamiento efectivos
- **Recomendación**: Mantener secuencia de 30 días para este dataset

### Prueba 2: Features Adicionales (Evapotranspiración + Humedad del Suelo)
- **Resultado**: FALLÓ
- **Causa**: Los datos sintéticos de evapotranspiración y humedad del suelo no están correlacionados correctamente con los datos reales de caudal
- **Recomendación**: Necesita datos reales de ET y humedad del suelo obtenidos de estaciones meteorológicas o modelos hidrológicos

### Prueba 3: Arquitectura LSTM con Attention
- **Resultado**: MUY PEOR que baseline
- **Causa probable**: Early stopping occurred demasiado temprano (epoch 5) y el modelo no convergió adecuadamente
- **Recomendación**: La arquitectura stacked LSTM simple funciona mejor para este problema de series temporales hidrológicas

## Conclusiones

1. **El modelo baseline (LSTM Stacked, seq=30) es el MEJOR** con:
   - RMSE: 5.45 m³/s (10.9% del caudal medio)
   - R²: 0.87 (explica 87% de la varianza)

2. **Las mejoras sugeridas no funcionaron** porque:
   - Secuencias más largas introducen más ruido
   - Datos sintéticos de features adicionales no son útiles
   - Atención prematura causa sub-entrenamiento

3. **Para mejorar el modelo baseline** se recomienda:
   - Obtener datos reales de evapotranspiración y humedad del suelo
   - Aumentar la cantidad de datos de entrenamiento
   - Ajustar hiperparámetros (dropout, learning rate)
   - Probar normalización de datos por temporada

## Métricas del Mejor Modelo (Baseline)

| Métrica | Valor |
|---------|-------|
| RMSE | 5.4462 m³/s |
| MAE | 4.3515 m³/s |
| R² | 0.8698 |
| MAPE | 7.84% |
| NSE | 0.8698 |
| P-Bias | -1.64% |
| KGE | 0.8325 |
