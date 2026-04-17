/**
 * Rutas de Narrativa (IA Generativa)
 */

const express = require('express');
const router = express.Router();

router.get('/:catchment', async (req, res, next) => {
    try {
        const { catchment } = req.params;
        const { type = 'summary' } = req.query;

        const narratives = {
            summary: {
                catchment_id: catchment,
                type: 'summary',
                generated_at: new Date().toISOString(),
                content: `El índice NDVI promedio en la cuenca ${catchment} es 0.65, indicando vegetación saludable. El NDWI de 0.42 sugiere niveles hídricos estables en cuerpos de agua. El caudal actual de 4.2 m³/s se encuentra 15% por encima del promedio histórico para este período.`,
                metrics_summary: {
                    ndvi: { value: 0.65, status: 'healthy' },
                    ndwi: { value: 0.42, status: 'stable' },
                    caudal: { value: 4.2, status: 'above_average' }
                }
            },
            forecast: {
                catchment_id: catchment,
                type: 'forecast',
                generated_at: new Date().toISOString(),
                content: `Para los próximos 7 días, se anticipa una disminución gradual del caudal debido a la reducción de lluvias previstas. Se recomienda monitorear activamente los niveles en la zona baja de la cuenca. La probabilidad de condiciones de estrés hídrico es del 65%.`,
                forecast_summary: {
                    trend: 'decreasing',
                    confidence: 0.78,
                    key_factors: ['baja precipitación prevista', 'temperaturas en aumento']
                }
            },
            alert: {
                catchment_id: catchment,
                type: 'alert',
                generated_at: new Date().toISOString(),
                severity: 'yellow',
                content: `⚠️ NIVEL AMARILLO - Sequía Leve\n\nProbabilidad de condiciones de estrés hídrico: 65%\n\nAcciones recomendadas:\n• Activar protocolo de monitoreo intensificado\n• Notificar a usuarios del sector agropecuario\n• Revisar estado de reservas hídricas`,
                alert_details: {
                    probability: 0.65,
                    affected_areas: ['zona_baja', 'sector_agricola'],
                    recommendations: [
                        'Activar protocolo de monitoreo intensificado',
                        'Notificar a usuarios del sector agropecuario',
                        'Revisar estado de reservas hídricas'
                    ]
                }
            }
        };

        res.json(narratives[type] || narratives.summary);
    } catch (error) {
        next(error);
    }
});

module.exports = router;
