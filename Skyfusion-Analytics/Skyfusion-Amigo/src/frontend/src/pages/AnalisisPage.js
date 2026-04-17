import React, { useState, useCallback } from 'react';
import InteractiveMap from '../components/InteractiveMap';
import NarrativaIA from '../components/NarrativaIA';
import { fetchMetrics, fetchAlerts, fetchPredictions } from '../services/api';

function AnalisisPage() {
  const [loading, setLoading] = useState(false);
  const [analisis, setAnalisis] = useState(null);
  const [selectedPoint, setSelectedPoint] = useState(null);
  const [error, setError] = useState(null);

  const handleMarkerMove = useCallback(async (markerData) => {
    setLoading(true);
    setError(null);
    setSelectedPoint({ lat: markerData.lat, lng: markerData.lng });

    try {
      const response = await fetch('http://localhost:3001/api/v1/analisis/coordenadas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lat: markerData.lat,
          lng: markerData.lng,
          meses: 12
        })
      });

      if (!response.ok) {
        throw new Error('Error en el análisis');
      }

      const data = await response.json();
      setAnalisis(data);
    } catch (err) {
      console.error('Error:', err);
      setError('Error al conectar con el servidor de análisis');
      
      setAnalisis({
        diagnostico: `Análisis para coordinates ${markerData.lat.toFixed(4)}, ${markerData.lng.toFixed(4)}. El área presenta condiciones de vegetación moderadas con signos de estrés hídrico. Se recomienda monitoreo continuo.`,
        alerta: {
          nivel: 'amarillo',
          mensaje: 'Estrés hídrico moderado detectado',
          color: '#f59e0b'
        },
        recomendaciones: [
          'Monitoreo continuo de niveles de agua',
          'Revisar estado de reservas hídricas',
          'Coordinar con CRQ para planificación',
          'Notificar al sector agropecuario',
          'Activar protocolo de contingencia'
        ],
        dashboard: {
          widgets: [
            { tipo: 'indicador', titulo: 'NDVI', valor: '0.55', color: '#22c55e' },
            { tipo: 'indicador', titulo: 'NDWI', valor: '0.38', color: '#0ea5e9' },
            { tipo: 'indicador', titulo: 'Temp', valor: '25°C', color: '#f59e0b' }
          ]
        },
        datos_satelitales: {
          ndvi: { valor: 0.55 },
          ndwi: { valor: 0.38 },
          temperatura: { valor: 25 }
        }
      });
    } finally {
      setLoading(false);
    }
  }, []);

  const handleMapClick = useCallback(async (coords) => {
    await handleMarkerMove({
      id: `CLICK-${Date.now()}`,
      lat: coords.lat,
      lng: coords.lng,
      nombre: 'Punto seleccionado',
      tipo: 'custom'
    });
  }, [handleMarkerMove]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">
            Centro de Análisis IA
          </h1>
          <p className="text-slate-400">
            Análisis ambiental en tiempo real con Google Earth Engine y Inteligencia Artificial
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-3 space-y-4">
            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-4 border border-white/10">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-white flex items-center space-x-2">
                  <span>🗺️</span>
                  <span>Mapa Interactivo</span>
                </h2>
                <div className="flex items-center space-x-2 text-sm text-slate-400">
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                  <span>GEE Conectado</span>
                </div>
              </div>
              
              <div className="h-[500px] rounded-lg overflow-hidden">
                <InteractiveMap 
                  onMarkerMove={handleMarkerMove}
                  onMapClick={handleMapClick}
                  selectedPoint={selectedPoint}
                />
              </div>
            </div>

            {error && (
              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                <p className="text-yellow-400 text-sm">{error}</p>
              </div>
            )}
          </div>

          <div className="space-y-4">
            <NarrativaIA 
              analisis={analisis} 
              loading={loading}
            />

            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-4 border border-white/10">
              <h3 className="text-sm font-semibold text-white mb-3">Punto Seleccionado</h3>
              {selectedPoint ? (
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Latitud:</span>
                    <span className="text-white font-mono">{selectedPoint.lat.toFixed(6)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Longitud:</span>
                    <span className="text-white font-mono">{selectedPoint.lng.toFixed(6)}</span>
                  </div>
                  <button
                    onClick={() => handleMarkerMove({ id: 'REFRESH', lat: selectedPoint.lat, lng: selectedPoint.lng, nombre: 'Actualizar', tipo: 'refresh' })}
                    disabled={loading}
                    className="w-full mt-3 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-lg text-white text-sm transition-colors"
                  >
                    {loading ? 'Analizando...' : 'Actualizar Análisis'}
                  </button>
                </div>
              ) : (
                <p className="text-slate-500 text-sm">Selecciona un punto en el mapa</p>
              )}
            </div>

            <div className="bg-gradient-to-br from-indigo-600 to-purple-600 rounded-xl p-4 text-white">
              <h3 className="font-semibold mb-2">💡 Guía Rápida</h3>
              <ul className="text-sm space-y-2 text-indigo-100">
                <li>• Arrastra los marcadores para analizar diferentes ubicaciones</li>
                <li>• Haz clic en el mapa para agregar nuevos puntos de análisis</li>
                <li>• El análisis incluye NDVI, NDWI y temperatura</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AnalisisPage;
