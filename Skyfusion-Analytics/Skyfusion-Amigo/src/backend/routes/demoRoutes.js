const express = require('express');
const router = express.Router();

router.get('/metrics/:catchmentId', (req, res) => {
    const { catchmentId } = req.params;
    res.json({
        catchment_id: catchmentId,
        timestamp: new Date().toISOString(),
        metrics: {
            caudal: { value: 4.2, unit: 'm³/s', status: 'normal', trend: 'down' },
            precipitacion: { value: 12, unit: 'mm', status: 'normal', trend: 'up' },
            temperatura: { value: 24, unit: '°C', status: 'normal', trend: 'up' },
            humedad: { value: 78, unit: '%', status: 'normal', trend: 'stable' },
            ndvi: { value: 0.65, status: 'healthy', trend: 'stable' },
            ndwi: { value: 0.42, status: 'stable', trend: 'down' }
        }
    });
});

router.get('/stations/:riverId', (req, res) => {
    const { riverId } = req.params;
    const stations = [
        { id: 'ST-001', name: 'Juntas - Parte Alta', lat: 4.548, lng: -75.321, status: 'active', lastReading: 1.2 },
        { id: 'ST-002', name: 'Villarestrepo', lat: 4.512, lng: -75.285, status: 'active', lastReading: 0.9 }
    ];
    res.json(stations);
});

router.get('/alerts/:catchmentId', (req, res) => {
    const alerts = [
        {
            id: 'alert-001',
            catchment_id: 'COMBEIMA',
            severity: 'yellow',
            status: 'active',
            type: 'drought',
            message: 'Sequía leve detectada - Monitoreo recomendado',
            probability: 0.65,
            created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            recommendations: [
                'Activar protocolo de monitoreo intensificado',
                'Notificar a usuarios del sector agropecuario',
                'Revisar estado de reservas hídricas'
            ]
        },
        {
            id: 'alert-002',
            catchment_id: 'COMBEIMA',
            severity: 'orange',
            status: 'active',
            type: 'water_stress',
            message: 'Estrés hídrico moderado - Reducción de caudal: 35%',
            probability: 0.72,
            created_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
            recommendations: [
                'Activación de plan de contingencia',
                'Monitoreo diario de niveles',
                'Coordinar con empresa de agua'
            ]
        }
    ];
    res.json({ alerts, total: alerts.length });
});

router.get('/predictions/:catchmentId', (req, res) => {
    const { catchmentId } = req.params;
    const { horizon = 7 } = req.query;
    
    const predictions = [];
    let caudal = 4.2;
    
    for (let i = 1; i <= parseInt(horizon); i++) {
        caudal = caudal - (Math.random() * 0.15);
        predictions.push({
            day: i,
            date: new Date(Date.now() + i * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            caudal: parseFloat(Math.max(caudal, 1.5).toFixed(2)),
            caudal_unit: 'm³/s',
            flood_probability: parseFloat((Math.random() * 0.25).toFixed(2)),
            drought_probability: parseFloat((0.3 + i * 0.04).toFixed(2)),
            alert_level: caudal < 2 ? 'orange' : caudal < 3 ? 'yellow' : 'green',
            confidence: parseFloat((0.75 + Math.random() * 0.2).toFixed(2))
        });
    }
    
    res.json({
        catchment_id: catchmentId,
        horizon_days: parseInt(horizon),
        generated_at: new Date().toISOString(),
        model_version: '1.0.0',
        predictions
    });
});

router.get('/narrative/:catchmentId', (req, res) => {
    const { catchmentId } = req.params;
    res.json({
        catchment_id: catchmentId,
        generated_at: new Date().toISOString(),
        summary: `El índice NDVI promedio en la cuenca ${catchmentId} es 0.65, indicando vegetación saludable. El NDWI de 0.42 sugiere niveles hídricos estables en cuerpos de agua.`,
        forecast: `Para los próximos 7 días, se anticipa una disminución gradual del caudal debido a la reducción de lluvias previstas. Se recomienda monitoreo activo.`,
        alert: {
            level: 'yellow',
            title: 'Sequía Leve',
            description: 'Probabilidad de condiciones de estrés hídrico: 65%.'
        },
        recommendations: [
            'Activar protocolo de monitoreo intensificado',
            'Notificar a usuarios del sector agropecuario',
            'Revisar estado de reservas hídricas'
        ]
    });
});

router.get('/catchments', (req, res) => {
    res.json({
        catchments: [
            { id: 'COMBEIMA', name: 'Cuenca Río Combeima', area_km2: 342, population: 250000, location: { lat: 4.4389, lon: -75.2094 } },
            { id: 'COELLO', name: 'Cuenca Río Coello', area_km2: 1250, population: 450000, location: { lat: 4.25, lon: -75.15 } },
            { id: 'OPHIR', name: 'Cuenca Río Ophir', area_km2: 180, population: 85000, location: { lat: 4.55, lon: -75.30 } }
        ]
    });
});

router.get('/stations', (req, res) => {
    const stations = [
        { id: 'COMB-001', name: 'Puente Combeima', type: 'caudal', lat: 4.4389, lon: -75.2094, status: 'active' },
        { id: 'COMB-002', name: 'El Carmen', type: 'pluviometro', lat: 4.4567, lon: -75.2234, status: 'active' },
        { id: 'COMB-003', name: 'Buenavista', type: 'caudal', lat: 4.4123, lon: -75.1956, status: 'active' },
        { id: 'COMB-004', name: 'Toche', type: 'meteo', lat: 4.4789, lon: -75.2456, status: 'active' }
    ];
    res.json({ stations });
});

router.get('/indices/:indexName', (req, res) => {
    const { indexName } = req.params;
    const { catchmentId = 'COMBEIMA', date } = req.query;
    
    const indices = {
        ndvi: { name: 'NDVI', description: 'Normalized Difference Vegetation Index', value: 0.65, min: -1, max: 1, interpretation: 'Vegetación saludable', last_update: new Date().toISOString() },
        ndwi: { name: 'NDWI', description: 'Normalized Difference Water Index', value: 0.42, min: -1, max: 1, interpretation: 'Niveles hídricos estables', last_update: new Date().toISOString() }
    };
    
    res.json({ index: indexName, catchment_id: catchmentId, date: date || new Date().toISOString().split('T')[0], data: indices[indexName] || indices.ndvi });
});

module.exports = router;