import React, { useState, useEffect } from 'react';
import ProjectCard from '../components/ProjectCard';

function ProjectsPage() {
  const [proyectos, setProyectos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filtro, setFiltro] = useState('todos');
  const [selectedProyecto, setSelectedProyecto] = useState(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    fetchProyectos();
  }, [filtro]);

  const fetchProyectos = async () => {
    setLoading(true);
    try {
      const url = filtro === 'todos' 
        ? 'http://localhost:3001/api/v1/proyectos'
        : `http://localhost:3001/api/v1/proyectos?estado=${filtro}`;
      
      const response = await fetch(url);
      const data = await response.json();
      setProyectos(data.proyectos || []);
    } catch (error) {
      console.error('Error fetching proyectos:', error);
      setProyectos([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('¿Estás seguro de eliminar este proyecto?')) return;
    
    try {
      await fetch(`http://localhost:3001/api/v1/proyectos/${id}`, {
        method: 'DELETE'
      });
      fetchProyectos();
    } catch (error) {
      console.error('Error deleting proyecto:', error);
    }
  };

  const estados = [
    { key: 'todos', label: 'Todos', count: proyectos.length },
    { key: 'activo', label: 'Activos', count: proyectos.filter(p => p.estado === 'activo').length },
    { key: 'en_progreso', label: 'En Progreso', count: proyectos.filter(p => p.estado === 'en_progreso').length },
    { key: 'completado', label: 'Completados', count: proyectos.filter(p => p.estado === 'completado').length },
    { key: 'pausado', label: 'Pausados', count: proyectos.filter(p => p.estado === 'pausado').length }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">
              Gestión de Proyectos
            </h1>
            <p className="text-slate-400">
              Administra y monitorea los proyectos de análisis ambiental
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>Nuevo Proyecto</span>
          </button>
        </div>

        <div className="flex items-center space-x-2 mb-6 overflow-x-auto pb-2">
          {estados.map(estado => (
            <button
              key={estado.key}
              onClick={() => setFiltro(estado.key)}
              className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                filtro === estado.key
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white/10 text-slate-400 hover:bg-white/20'
              }`}
            >
              {estado.label}
              <span className="ml-2 px-2 py-0.5 bg-black/20 rounded-full text-xs">
                {estado.count}
              </span>
            </button>
          ))}
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map(i => (
              <div key={i} className="bg-slate-800/50 rounded-xl h-64 animate-pulse"></div>
            ))}
          </div>
        ) : proyectos.length === 0 ? (
          <div className="text-center py-20">
            <div className="w-20 h-20 bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-10 h-10 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">No hay proyectos</h3>
            <p className="text-slate-400 mb-6">Crea tu primer proyecto para comenzar</p>
            <button
              onClick={() => setShowModal(true)}
              className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
            >
              Crear Proyecto
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {proyectos.map(proyecto => (
              <ProjectCard
                key={proyecto.id}
                proyecto={proyecto}
                onClick={setSelectedProyecto}
                onEdit={setSelectedProyecto}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </div>

      {selectedProyecto && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-700">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-white">{selectedProyecto.nombre}</h2>
                  <p className="text-slate-400 mt-1">{selectedProyecto.entidad}</p>
                </div>
                <button
                  onClick={() => setSelectedProyecto(null)}
                  className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                >
                  <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <h4 className="text-sm font-medium text-slate-400 mb-1">Descripción</h4>
                <p className="text-white">{selectedProyecto.descripcion}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium text-slate-400 mb-1">Responsable</h4>
                  <p className="text-white">{selectedProyecto.responsable}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-slate-400 mb-1">Estado</h4>
                  <p className="text-white capitalize">{selectedProyecto.estado?.replace('_', ' ')}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-slate-400 mb-1">Fecha Inicio</h4>
                  <p className="text-white">{selectedProyecto.fecha_inicio}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-slate-400 mb-1">Fecha Fin</h4>
                  <p className="text-white">{selectedProyecto.fecha_fin || '—'}</p>
                </div>
              </div>

              {selectedProyecto.metricas && (
                <div>
                  <h4 className="text-sm font-medium text-slate-400 mb-2">Métricas</h4>
                  <div className="grid grid-cols-3 gap-3">
                    {Object.entries(selectedProyecto.metricas).map(([key, value]) => (
                      <div key={key} className="bg-slate-700/50 rounded-lg p-3 text-center">
                        <p className="text-xs text-slate-400 capitalize">{key.replace('_', ' ')}</p>
                        <p className="text-lg font-bold text-white">{value}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="p-6 border-t border-slate-700 flex justify-end space-x-3">
              <button
                onClick={() => setSelectedProyecto(null)}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                Cerrar
              </button>
              <button className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors">
                Generar Reporte
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ProjectsPage;
