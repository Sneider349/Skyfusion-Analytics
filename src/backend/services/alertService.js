/**
 * Servicio de Alertas
 */

const { getDriver } = require('../config/neo4j');
const { logger } = require('../config/logger');

const SEVERITY_LEVELS = {
    green: 0,
    yellow: 1,
    orange: 2,
    red: 3
};

async function checkAlerts(io) {
    try {
        logger.info('Checking alerts');

        const alerts = await evaluateConditions();

        for (const alert of alerts) {
            await emitAlert(alert, io);
        }

        logger.info('Alert check completed');
    } catch (error) {
        logger.error('Alert check failed:', error);
    }
}

async function evaluateConditions() {
    const alerts = [];

    const caudal = 3.8;
    const ndvi = 0.45;
    const precipProbability = 0.1;

    if (caudal < 1.5) {
        alerts.push({
            severity: 'red',
            type: 'flood',
            probability: 0.85,
            message: 'Riesgo alto de inundación - Acción inmediata requerida'
        });
    } else if (caudal < 2.5) {
        alerts.push({
            severity: 'orange',
            type: 'flood',
            probability: 0.65,
            message: 'Alerta de inundación - Precaución recomendada'
        });
    }

    if (caudal < 3.0 && precipProbability < 0.2) {
        alerts.push({
            severity: 'yellow',
            type: 'drought',
            probability: 0.55,
            message: 'Sequía leve detectada - Monitoreo recomendado'
        });
    }

    if (ndvi < 0.3) {
        alerts.push({
            severity: 'orange',
            type: 'vegetation_stress',
            probability: 0.70,
            message: 'Estrés hídrico en vegetación - Revisar reservas'
        });
    }

    if (alerts.length === 0) {
        alerts.push({
            severity: 'green',
            type: 'normal',
            probability: 0.95,
            message: 'Condiciones normales - Sin alertas activas'
        });
    }

    return alerts;
}

async function emitAlert(alert, io) {
    const driver = getDriver();
    const session = driver.session({ database: 'neo4j' });

    try {
        await session.run(`
            CREATE (a:Alert {
                id: 'alert-' + toString(rand()),
                severity: $severity,
                type: $type,
                message: $message,
                probability: $probability,
                status: 'active',
                created_at: datetime()
            })
        `, {
            severity: alert.severity,
            type: alert.type,
            message: alert.message,
            probability: alert.probability
        });
    } finally {
        await session.close();
    }

    io.emit('alert', {
        ...alert,
        generated_at: new Date().toISOString()
    });
}

module.exports = { checkAlerts };
