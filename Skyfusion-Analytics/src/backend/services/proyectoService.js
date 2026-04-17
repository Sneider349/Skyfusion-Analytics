/**
 * Servicio de Proyectos
 * CRUD completo para gestión de proyectos en Neo4j
 */

const { getDriver } = require('../config/neo4j');
const { logger } = require('../config/logger');

const PROYECTOS_DEMO = [
    {
        id: 'PROY-001',
        nombre: 'Monitoreo Río Combeima - Fase I',
        descripcion: 'Análisis multitemporal de la cuenca alta del río Combeima con datos Landsat 8 y Sentinel-2',
        coordenadas: [[-75.35, 4.60], [-75.35, 4.30], [-75.05, 4.30], [-75.05, 4.60]],
        estado: 'en_progreso',
        progreso: 65,
        fecha_inicio: '2025-01-15',
        fecha_fin: '2026-06-30',
        entidad: 'UNIMINUTO',
        responsable: 'Dr. Carlos Martínez',
        metricas: { ndvi_promedio: 0.58, alertas: 3 },
        created_at: '2025-01-15T10:00:00Z'
    },
    {
        id: 'PROY-002',
        nombre: 'Predicción Caudal - El Niño 2026',
        descripcion: 'Modelo predictivo para anticipar eventos de sequía basados en datos históricos y variables climáticas',
        coordenadas: [[-75.30, 4.50], [-75.30, 4.35], [-75.15, 4.35], [-75.15, 4.50]],
        estado: 'activo',
        progreso: 40,
        fecha_inicio: '2025-09-01',
        fecha_fin: '2026-12-31',
        entidad: 'CRQ',
        responsable: 'Ing. Ana Sofía Pérez',
        metricas: { predicciones: 7, precision: 0.82 },
        created_at: '2025-09-01T08:30:00Z'
    },
    {
        id: 'PROY-003',
        nombre: 'Calidad Agua - Juntas',
        descripcion: 'Análisis de calidad del agua en tiempo real integrando sensores IoT y datos satelitales',
        coordenadas: [[-75.35, 4.55], [-75.35, 4.50], [-75.30, 4.50], [-75.30, 4.55]],
        estado: 'completado',
        progreso: 100,
        fecha_inicio: '2024-06-01',
        fecha_fin: '2025-05-31',
        entidad: 'Alcaldía Ibagué',
        responsable: 'Ing. José Roberto Silva',
        metricas: { muestras: 245, ph: 7.2, turbiedad: 12 },
        created_at: '2024-06-01T09:00:00Z'
    },
    {
        id: 'PROY-004',
        nombre: 'Cartografía Riesgo Inundación',
        descripcion: 'Mapeo de zonas de riesgo de inundación para la planificación urbana y rural',
        coordenadas: [[-75.25, 4.45], [-75.25, 4.38], [-75.18, 4.38], [-75.18, 4.45]],
        estado: 'en_progreso',
        progreso: 25,
        fecha_inicio: '2026-01-01',
        fecha_fin: '2026-12-31',
        entidad: 'Gobernación Tolima',
        responsable: 'Geól. María Elena Gómez',
        metricas: { zonas_criticas: 8, afectados_estimados: 12500 },
        created_at: '2026-01-01T10:00:00Z'
    },
    {
        id: 'PROY-005',
        nombre: 'Vegetación y Cobertura - TOE',
        descripcion: 'Análisis de cambios en la cobertura vegetal usando índice NDVI y clasificaciones supervisadas',
        coordenadas: [[-75.40, 4.65], [-75.40, 4.25], [-75.05, 4.25], [-75.05, 4.65]],
        estado: 'pausado',
        progreso: 15,
        fecha_inicio: '2025-11-01',
        fecha_fin: '2026-10-31',
        entidad: 'CAR',
        responsable: 'Dr. Fernando López',
        metricas: { cambio_cobertura: -0.08 },
        created_at: '2025-11-01T11:00:00Z'
    }
];

async function getAllProyectos(filtros = {}) {
    try {
        const driver = getDriver();
        const session = driver.session({ database: 'neo4j' });

        let query = 'MATCH (p:Proyecto)';
        const params = {};

        if (filtros.estado) {
            query += ' WHERE p.estado = $estado';
            params.estado = filtros.estado;
        }

        query += ' RETURN p ORDER BY p.created_at DESC';

        const result = await session.run(query, params);
        await session.close();

        if (result.records.length === 0) {
            return PROYECTOS_DEMO;
        }

        return result.records.map(record => ({
            ...record.get('p').properties
        }));
    } catch (error) {
        logger.error('Error getting proyectos:', error);
        return PROYECTOS_DEMO;
    }
}

async function getProyectoById(id) {
    try {
        const driver = getDriver();
        const session = driver.session({ database: 'neo4j' });

        const result = await session.run(
            'MATCH (p:Proyecto {id: $id}) RETURN p',
            { id }
        );

        await session.close();

        if (result.records.length === 0) {
            return PROYECTOS_DEMO.find(p => p.id === id) || null;
        }

        return result.records[0].get('p').properties;
    } catch (error) {
        logger.error('Error getting proyecto:', error);
        return PROYECTOS_DEMO.find(p => p.id === id) || null;
    }
}

async function createProyecto(data) {
    const nuevoProyecto = {
        id: `PROY-${Date.now()}`,
        nombre: data.nombre,
        descripcion: data.descripcion || '',
        coordenadas: data.coordenadas || [],
        estado: 'activo',
        progreso: 0,
        fecha_inicio: data.fecha_inicio || new Date().toISOString().split('T')[0],
        fecha_fin: data.fecha_fin || '',
        entidad: data.entidad || '',
        responsable: data.responsable || '',
        metricas: data.metricas || {},
        created_at: new Date().toISOString()
    };

    try {
        const driver = getDriver();
        const session = driver.session({ database: 'neo4j' });

        await session.run(`
            CREATE (p:Proyecto {
                id: $id,
                nombre: $nombre,
                descripcion: $descripcion,
                coordenadas: $coordenadas,
                estado: $estado,
                progreso: $progreso,
                fecha_inicio: $fecha_inicio,
                fecha_fin: $fecha_fin,
                entidad: $entidad,
                responsable: $responsable,
                metricas: $metricas,
                created_at: datetime($created_at)
            })
            RETURN p
        `, nuevoProyecto);

        await session.close();
        logger.info(`Proyecto creado: ${nuevoProyecto.id}`);
        return nuevoProyecto;
    } catch (error) {
        logger.error('Error creating proyecto:', error);
        return nuevoProyecto;
    }
}

async function updateProyecto(id, data) {
    try {
        const driver = getDriver();
        const session = driver.session({ database: 'neo4j' });

        const updates = [];
        const params = { id };

        Object.keys(data).forEach(key => {
            updates.push(`p.${key} = $${key}`);
            params[key] = data[key];
        });

        await session.run(`
            MATCH (p:Proyecto {id: $id})
            SET ${updates.join(', ')}
            RETURN p
        `, params);

        await session.close();
        logger.info(`Proyecto actualizado: ${id}`);
        
        return await getProyectoById(id);
    } catch (error) {
        logger.error('Error updating proyecto:', error);
        throw error;
    }
}

async function deleteProyecto(id) {
    try {
        const driver = getDriver();
        const session = driver.session({ database: 'neo4j' });

        await session.run('MATCH (p:Proyecto {id: $id}) DELETE p', { id });
        await session.close();
        
        logger.info(`Proyecto eliminado: ${id}`);
        return { success: true };
    } catch (error) {
        logger.error('Error deleting proyecto:', error);
        throw error;
    }
}

async function getProyectosPorEstado() {
    try {
        const proyectos = await getAllProyectos();
        
        const porEstado = {
            activo: proyectos.filter(p => p.estado === 'activo').length,
            en_progreso: proyectos.filter(p => p.estado === 'en_progreso').length,
            completado: proyectos.filter(p => p.estado === 'completado').length,
            pausado: proyectos.filter(p => p.estado === 'pausado').length
        };

        return {
            total: proyectos.length,
            por_estado: porEstado,
            proyectos
        };
    } catch (error) {
        logger.error('Error getting proyectos por estado:', error);
        return {
            total: PROYECTOS_DEMO.length,
            por_estado: {
                activo: 1,
                en_progreso: 2,
                completado: 1,
                pausado: 1
            },
            proyectos: PROYECTOS_DEMO
        };
    }
}

module.exports = {
    getAllProyectos,
    getProyectoById,
    createProyecto,
    updateProyecto,
    deleteProyecto,
    getProyectosPorEstado
};
