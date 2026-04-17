/**
 * Servicio de Inteligencia Artificial (OpenAI GPT-4)
 * Genera análisis contextual y recomendaciones basadas en datos GEE
 */

const OpenAI = require('openai');
const { logger } = require('../config/logger');

let openai = null;

function initializeAI() {
    if (openai) return openai;

    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
        logger.warn('OPENAI_API_KEY not configured');
        return null;
    }

    openai = new OpenAI({ apiKey });
    logger.info('OpenAI client initialized');
    return openai;
}

async function analizarDatosAmbientales(datosGEE) {
    const client = initializeAI();
    if (!client) {
        return generarAnalisisDemo(datosGEE);
    }

    const prompt = `
Eres un analista ambiental experto en gestión de recursos hídricos y SIG (Sistemas de Información Geográfica).

Analiza los siguientes datos satelitales para la cuenca del Río Combeima, Ibagué, Colombia:

DATOS SATELITALES:
- NDVI (Índice de Vegetación): ${datosGEE.ndvi?.valor || 'N/A'}
- NDWI (Índice de Agua): ${datosGEE.ndwi?.valor || 'N/A'}
- Temperatura Superficial: ${datosGEE.temperatura?.valor || 'N/A'} °C
- Coordenadas: Latitud ${datosGEE.latitud}, Longitud ${datosGEE.longitud}

Basado en estos datos, genera:

1. **DIAGNÓSTICO**: Una descripción breve del estado actual del área analizada (máximo 2 oraciones).

2. **ALERTAS**: Nivel de alerta (verde, amarillo, naranja, rojo) con justificación técnica.

3. **RECOMENDACIONES**: 3-5 recomendaciones concretas de acción para autoridades ambientales.

4. **DASHBOARD_SUGERIDO**: Estructura JSON para visualizar estos datos:
   - tipo: "indicador" | "grafico" | "alerta"
   - titulo: título del widget
   - valor: valor numérico o texto
   - color: color hexadecimal para el semáforo

Responde en formato JSON válido con esta estructura exacta:
{
  "diagnostico": "...",
  "alerta": { "nivel": "...", "mensaje": "..." },
  "recomendaciones": ["...", "..."],
  "dashboard": {
    "widgets": [
      { "tipo": "...", "titulo": "...", "valor": ..., "color": "..." }
    ]
  }
}`;

    try {
        const response = await client.chat.completions.create({
            model: 'gpt-4o',
            messages: [
                {
                    role: 'system',
                    content: 'Eres un analista ambiental experto. Respondes siempre en JSON válido.'
                },
                {
                    role: 'user',
                    content: prompt
                }
            ],
            temperature: 0.7,
            max_tokens: 2000
        });

        const contenido = response.choices[0].message.content;
        
        try {
            const resultado = JSON.parse(contenido);
            logger.info('Análisis de IA generado exitosamente');
            return resultado;
        } catch (parseError) {
            logger.warn('Error parsing AI response, using fallback');
            return generarAnalisisDemo(datosGEE);
        }
    } catch (error) {
        logger.error('Error calling OpenAI:', error);
        return generarAnalisisDemo(datosGEE);
    }
}

function generarAnalisisDemo(datosGEE) {
    const ndvi = datosGEE.ndvi?.valor || 0.65;
    const ndwi = datosGEE.ndwi?.valor || 0.42;
    const temp = datosGEE.temperatura?.valor || 24;

    let nivelAlerta = 'verde';
    let mensajeAlerta = 'Condiciones normales';
    let colorAlerta = '#22c55e';

    if (ndvi < 0.3 || temp > 28) {
        nivelAlerta = 'amarillo';
        mensajeAlerta = 'Estrés hídrico moderado detectado';
        colorAlerta = '#f59e0b';
    }
    if (ndvi < 0.2 || temp > 32) {
        nivelAlerta = 'naranja';
        mensajeAlerta = 'Alerta de sequía prolongada';
        colorAlerta = '#f97316';
    }
    if (ndvi < 0.1) {
        nivelAlerta = 'rojo';
        mensajeAlerta = 'Emergencia ambiental';
        colorAlerta = '#ef4444';
    }

    return {
        diagnostico: `El área analizada presenta NDVI de ${ndvi} y NDWI de ${ndwi}. La temperatura superficial es de ${temp}°C. La vegetación muestra ${ndvi > 0.5 ? 'buenas condiciones' : 'signos de estrés'} hídrico.`,
        alerta: {
            nivel: nivelAlerta,
            mensaje: mensajeAlerta,
            color: colorAlerta
        },
        recomendaciones: [
            'Monitoreo continuo de niveles de agua',
            'Revisar estado de reservas hídricas',
            'Coordinar con CRQ para planificación',
            'Notificar al sector agropecuario',
            'Activar protocolo de contingencia si es necesario'
        ],
        dashboard: {
            widgets: [
                { tipo: 'indicador', titulo: 'NDVI Actual', valor: ndvi.toFixed(2), color: ndvi > 0.5 ? '#22c55e' : '#f59e0b' },
                { tipo: 'indicador', titulo: 'NDWI Actual', valor: ndwi.toFixed(2), color: ndwi > 0.3 ? '#0ea5e9' : '#f59e0b' },
                { tipo: 'indicador', titulo: 'Temperatura', valor: `${temp}°C`, color: temp > 28 ? '#ef4444' : '#22c55e' },
                { tipo: 'grafico', titulo: 'Histórico NDVI', valor: 'linea', color: '#22c55e' }
            ]
        }
    };
}

async function generarNarrativaProyecto(proyecto, metricas) {
    const client = initializeAI();
    if (!client) {
        return generarNarrativaDemo(proyecto, metricas);
    }

    const prompt = `
Genera un informe narrativo para el proyecto "${proyecto.nombre}" en la cuenca del Río Combeima.

MÉTRICAS ACTUALES:
- Progreso: ${proyecto.progreso}%
- Estado: ${proyecto.estado}
- NDVI promedio: ${metricas.ndvi}
- Alertas activas: ${metricas.alertas}

Escribe un informe profesional que incluya:
1. Resumen ejecutivo (2-3 oraciones)
2. Hallazgos principales
3. Recomendaciones para siguientes pasos

Formato: Markdown profesional.
`;

    try {
        const response = await client.chat.completions.create({
            model: 'gpt-4o',
            messages: [
                { role: 'system', content: 'Eres un escritor técnico ambiental profesional.' },
                { role: 'user', content: prompt }
            ],
            temperature: 0.5,
            max_tokens: 1000
        });

        return response.choices[0].message.content;
    } catch (error) {
        logger.error('Error generating narrative:', error);
        return generarNarrativaDemo(proyecto, metricas);
    }
}

function generarNarrativaDemo(proyecto, metricas) {
    return `# Informe del Proyecto: ${proyecto.nombre}

## Resumen Ejecutivo
El proyecto "${proyecto.nombre}" presenta un avance del ${proyecto.progreso}% con estado "${proyecto.estado}". 
El análisis satelital actual muestra condiciones ${metricas.ndvi > 0.5 ? 'favorables' : 'de atención'} para la vegetación en la zona de estudio.

## Hallazgos Principales
- El índice NDVI promedio se mantiene en ${metricas.ndvi}, indicando ${metricas.ndvi > 0.5 ? 'vegetación saludable' : 'vegetación con estrés hídrico'}
- Se han detectado ${metricas.alertas} alertas activas en el período de análisis
- La coordinación con autoridades locales está activa

## Recomendaciones
1. Continuar con el monitoreo satelital mensual
2. Revisar protocolos de contingencia
3. Coordinar con la CRQ para validación de datos en campo
`;
}

async function predecirProyecciones(datosHistoricos) {
    const client = initializeAI();
    
    const prompt = `
Basado en los siguientes datos históricos de la cuenca del Río Combeima, genera una predicción para los próximos 6 meses:

${JSON.stringify(datosHistoricos)}

Para cada mes预测 (nombre del mes y valor esperado), considera:
- Tendencia actual (aumentando/disminuyendo/estable)
- Estacionalidad (temporada de lluvias/seca)
- Factores de cambio climático (El Niño/La Niña)

Responde en JSON:
{
  "predicciones": [
    { "mes": "Mayo 2026", "valor": 3.8, "tendencia": "estable" },
    ...
  ],
  "resumen": "Descripción breve de la tendencia"
}`;

    try {
        const response = await client.chat.completions.create({
            model: 'gpt-4o',
            messages: [
                { role: 'system', content: 'Eres un científico de datos especializado en hidrología.' },
                { role: 'user', content: prompt }
            ],
            temperature: 0.5,
            max_tokens: 800
        });

        return JSON.parse(response.choices[0].message.content);
    } catch (error) {
        logger.error('Error generating predictions:', error);
        return generarProyeccionesDemo();
    }
}

function generarProyeccionesDemo() {
    const meses = ['Mayo 2026', 'Junio 2026', 'Julio 2026', 'Agosto 2026', 'Septiembre 2026', 'Octubre 2026'];
    const valores = [3.8, 3.5, 3.2, 2.9, 2.7, 3.0];
    
    return {
        predicciones: meses.map((mes, i) => ({
            mes,
            valor: valores[i],
            tendencia: i < 4 ? 'decreciente' : 'estable'
        })),
        resumen: 'Se anticipa una disminución gradual del caudal para los próximos meses debido a la temporada seca, con recuperación esperada para octubre.'
    };
}

module.exports = {
    initializeAI,
    analizarDatosAmbientales,
    generarNarrativaProyecto,
    predecirProyecciones
};
