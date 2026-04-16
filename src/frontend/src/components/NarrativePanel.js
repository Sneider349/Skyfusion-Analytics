import React from 'react';
import { Sparkles, AlertTriangle, CheckCircle } from 'lucide-react';

function NarrativePanel({ narrative }) {
  const getAlertColor = (level) => {
    switch (level) {
      case 'red': return 'bg-red-50 border-red-200 text-red-700';
      case 'orange': return 'bg-orange-50 border-orange-200 text-orange-700';
      case 'yellow': return 'bg-yellow-50 border-yellow-200 text-yellow-700';
      default: return 'bg-green-50 border-green-200 text-green-700';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <div className="flex items-center space-x-2 mb-4">
        <Sparkles className="w-5 h-5 text-indigo-500" />
        <h3 className="text-lg font-semibold text-gray-800">Análisis IA</h3>
      </div>
      
      {narrative ? (
        <div className="space-y-4">
          <div className="p-3 bg-sky-50 rounded-lg">
            <h4 className="text-sm font-medium text-sky-700 mb-1">Resumen Actual</h4>
            <p className="text-sm text-gray-600">{narrative.summary}</p>
          </div>
          
          <div className="p-3 bg-indigo-50 rounded-lg">
            <h4 className="text-sm font-medium text-indigo-700 mb-1">Pronóstico</h4>
            <p className="text-sm text-gray-600">{narrative.forecast}</p>
          </div>
          
          {narrative.alert && (
            <div className={`p-3 rounded-lg border ${getAlertColor(narrative.alert.level)}`}>
              <div className="flex items-center space-x-2 mb-1">
                {narrative.alert.level === 'green' ? (
                  <CheckCircle className="w-4 h-4" />
                ) : (
                  <AlertTriangle className="w-4 h-4" />
                )}
                <h4 className="text-sm font-medium">{narrative.alert.title}</h4>
              </div>
              <p className="text-xs">{narrative.alert.description}</p>
            </div>
          )}
          
          {narrative.recommendations && narrative.recommendations.length > 0 && (
            <div className="p-3 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Recomendaciones</h4>
              <ul className="text-xs text-gray-600 space-y-1">
                {narrative.recommendations.map((rec, i) => (
                  <li key={i} className="flex items-start">
                    <span className="mr-1">•</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-4 text-gray-500">
          <Sparkles className="w-8 h-8 mx-auto mb-2 text-gray-300" />
          <p className="text-sm">Cargando análisis...</p>
        </div>
      )}
    </div>
  );
}

export default NarrativePanel;
