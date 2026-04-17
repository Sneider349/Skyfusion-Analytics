import React from 'react';

const estadoColores = {
  activo: { bg: 'bg-green-500/20', border: 'border-green-500/30', text: 'text-green-400', badge: 'bg-green-500' },
  en_progreso: { bg: 'bg-blue-500/20', border: 'border-blue-500/30', text: 'text-blue-400', badge: 'bg-blue-500' },
  completado: { bg: 'bg-purple-500/20', border: 'border-purple-500/30', text: 'text-purple-400', badge: 'bg-purple-500' },
  pausado: { bg: 'bg-yellow-500/20', border: 'border-yellow-500/30', text: 'text-yellow-400', badge: 'bg-yellow-500' }
};

function ProjectCard({ proyecto, onClick, onEdit, onDelete }) {
  const colors = estadoColores[proyecto.estado] || estadoColores.activo;
  
  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('es-CO', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div 
      onClick={() => onClick && onClick(proyecto)}
      className={`bg-slate-800/50 backdrop-blur-sm rounded-xl border ${colors.border} overflow-hidden cursor-pointer hover:scale-[1.02] transition-transform duration-200`}
    >
      <div className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div className={`px-3 py-1 rounded-full text-xs font-medium ${colors.bg} ${colors.text} border ${colors.border}`}>
            {proyecto.estado?.replace('_', ' ').toUpperCase()}
          </div>
          <div className="flex items-center space-x-2">
            {onEdit && (
              <button 
                onClick={(e) => { e.stopPropagation(); onEdit(proyecto); }}
                className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
              >
                <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
            )}
            {onDelete && (
              <button 
                onClick={(e) => { e.stopPropagation(); onDelete(proyecto.id); }}
                className="p-1.5 hover:bg-red-500/20 rounded-lg transition-colors"
              >
                <svg className="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            )}
          </div>
        </div>

        <h3 className="text-lg font-semibold text-white mb-2 line-clamp-2">
          {proyecto.nombre}
        </h3>
        
        <p className="text-slate-400 text-sm mb-4 line-clamp-2">
          {proyecto.descripcion}
        </p>

        <div className="mb-4">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span>Progreso</span>
            <span className={`font-medium ${colors.text}`}>{proyecto.progreso}%</span>
          </div>
          <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
            <div 
              className={`h-full rounded-full ${colors.badge}`}
              style={{ width: `${proyecto.progreso}%` }}
            />
          </div>
        </div>

        <div className="flex items-center justify-between text-sm text-slate-400">
          <div className="flex items-center space-x-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <span>{proyecto.entidad}</span>
          </div>
          <span>{formatDate(proyecto.fecha_fin)}</span>
        </div>

        <div className="mt-3 pt-3 border-t border-slate-700 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-6 h-6 bg-indigo-500/30 rounded-full flex items-center justify-center">
              <span className="text-xs text-indigo-300 font-medium">
                {proyecto.responsable?.charAt(0) || 'U'}
              </span>
            </div>
            <span className="text-xs text-slate-500">{proyecto.responsable}</span>
          </div>
          <button className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center space-x-1">
            <span>Ver detalles</span>
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

export default ProjectCard;
