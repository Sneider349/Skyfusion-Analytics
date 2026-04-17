import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

function NarrativaIA({ analisis, loading }) {
  const [activeTab, setActiveTab] = useState('diagnostico');

  if (loading) {
    return (
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-6 shadow-2xl">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-8 h-8 bg-indigo-500 rounded-lg animate-pulse"></div>
          <h3 className="text-lg font-semibold text-white">Análisis IA</h3>
        </div>
        <div className="space-y-3">
          <div className="h-4 bg-slate-700 rounded animate-pulse w-3/4"></div>
          <div className="h-4 bg-slate-700 rounded animate-pulse w-1/2"></div>
          <div className="h-20 bg-slate-700 rounded animate-pulse"></div>
        </div>
      </div>
    );
  }

  if (!analisis) {
    return (
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-6 shadow-2xl">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-8 h-8 bg-slate-600 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-white">Análisis IA</h3>
        </div>
        <p className="text-slate-400 text-sm">
          Selecciona un punto en el mapa para generar análisis.
        </p>
      </div>
    );
  }

  const getAlertColor = (nivel) => {
    switch (nivel) {
      case 'rojo': return 'bg-red-500/20 border-red-500 text-red-400';
      case 'naranja': return 'bg-orange-500/20 border-orange-500 text-orange-400';
      case 'amarillo': return 'bg-yellow-500/20 border-yellow-500 text-yellow-400';
      default: return 'bg-green-500/20 border-green-500 text-green-400';
    }
  };

  return (
    <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl shadow-2xl overflow-hidden">
      <div className="p-4 border-b border-slate-700">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-white">Análisis Inteligente</h3>
        </div>
      </div>

      <div className="flex border-b border-slate-700">
        {['diagnostico', 'alertas', 'recomendaciones', 'dashboard'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-3 text-xs font-medium uppercase tracking-wider transition-all ${
              activeTab === tab
                ? 'bg-indigo-600 text-white'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="p-4">
        {activeTab === 'diagnostico' && (
          <div className="space-y-4">
            <div className="bg-slate-800/50 rounded-lg p-4">
              <h4 className="text-sm font-medium text-indigo-400 mb-2">Diagnóstico Actual</h4>
              <p className="text-white text-sm leading-relaxed">
                {analisis.diagnostico || 'Analizando datos...'}
              </p>
            </div>
            
            {analisis.datos_satelitales && (
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                  <p className="text-xs text-slate-400 mb-1">NDVI</p>
                  <p className="text-xl font-bold text-green-400">
                    {analisis.datos_satelitales.ndvi?.valor?.toFixed(2) || '—'}
                  </p>
                </div>
                <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                  <p className="text-xs text-slate-400 mb-1">NDWI</p>
                  <p className="text-xl font-bold text-blue-400">
                    {analisis.datos_satelitales.ndwi?.valor?.toFixed(2) || '—'}
                  </p>
                </div>
                <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                  <p className="text-xs text-slate-400 mb-1">Temp</p>
                  <p className="text-xl font-bold text-orange-400">
                    {analisis.datos_satelitales.temperatura?.valor?.toFixed(1) || '—'}°C
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'alertas' && (
          <div className="space-y-3">
            <div className={`rounded-lg p-4 border ${getAlertColor(analisis.alerta?.nivel)}`}>
              <div className="flex items-center space-x-2 mb-2">
                <span className={`w-3 h-3 rounded-full ${
                  analisis.alerta?.nivel === 'rojo' ? 'bg-red-500' :
                  analisis.alerta?.nivel === 'naranja' ? 'bg-orange-500' :
                  analisis.alerta?.nivel === 'amarillo' ? 'bg-yellow-500' : 'bg-green-500'
                }`}></span>
                <span className="font-medium uppercase">{analisis.alerta?.nivel || 'verde'}</span>
              </div>
              <p className="text-sm">{analisis.alerta?.mensaje || 'Sin alertas'}</p>
            </div>
          </div>
        )}

        {activeTab === 'recomendaciones' && (
          <div className="space-y-2">
            {(analisis.recomendaciones || []).map((rec, index) => (
              <div key={index} className="flex items-start space-x-3 bg-slate-800/30 rounded-lg p-3">
                <span className="w-6 h-6 bg-indigo-600 rounded-full flex items-center justify-center text-xs text-white font-bold flex-shrink-0">
                  {index + 1}
                </span>
                <p className="text-sm text-slate-300">{rec}</p>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'dashboard' && (
          <div className="space-y-3">
            {(analisis.dashboard?.widgets || []).map((widget, index) => (
              <div key={index} className="bg-slate-800/50 rounded-lg p-4 flex items-center justify-between">
                <div>
                  <p className="text-xs text-slate-400">{widget.titulo}</p>
                  <p className="text-lg font-bold" style={{ color: widget.color }}>{widget.valor}</p>
                </div>
                <div className={`w-12 h-12 rounded-full flex items-center justify-center`} style={{ backgroundColor: `${widget.color}20` }}>
                  <span className="text-2xl" style={{ color: widget.color }}>
                    {widget.tipo === 'indicador' ? '📊' : widget.tipo === 'grafico' ? '📈' : '⚠️'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="px-4 pb-4">
        <p className="text-xs text-slate-500 text-center">
          Generado por Skyfusion AI • {new Date().toLocaleString()}
        </p>
      </div>
    </div>
  );
}

export default NarrativaIA;
