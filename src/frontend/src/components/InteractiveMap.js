import React, { useRef, useEffect, useCallback } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const COMBEIMA_CENTER = [4.4389, -75.2094];
const DEFAULT_ZOOM = 12;

const ESTACIONES_PRESET = [
  { id: 'COMB-001', name: 'Puente Combeima', lat: 4.4389, lng: -75.2094, tipo: 'caudal' },
  { id: 'COMB-002', name: 'Juntas - Parte Alta', lat: 4.548, lng: -75.321, tipo: 'caudal' },
  { id: 'COMB-003', name: 'Villarestrepo', lat: 4.512, lng: -75.285, tipo: 'pluviometro' },
  { id: 'COMB-004', name: 'El Carmen', lat: 4.4567, lng: -75.2234, tipo: 'meteo' }
];

function InteractiveMap({ onMarkerMove, onMapClick, selectedPoint }) {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const markersRef = useRef({});

  const getTipoColor = (tipo) => {
    switch (tipo) {
      case 'caudal': return '#22c55e';
      case 'pluviometro': return '#3b82f6';
      case 'meteo': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  const createDraggableMarker = useCallback((lat, lng, id, nombre, tipo) => {
    const color = getTipoColor(tipo);
    
    const markerIcon = L.divIcon({
      className: 'custom-marker',
      html: `
        <div style="
          width: 24px;
          height: 24px;
          background: ${color};
          border: 3px solid white;
          border-radius: 50%;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3);
          cursor: move;
          display: flex;
          align-items: center;
          justify-content: center;
        ">
          <svg style="width: 12px; height: 12px; fill: white;" viewBox="0 0 24 24">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
          </svg>
        </div>
      `,
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });

    const marker = L.marker([lat, lng], { 
      icon: markerIcon,
      draggable: true 
    });

    marker.bindPopup(`
      <div style="min-width: 150px;">
        <strong style="color: #1f2937;">${nombre}</strong><br/>
        <span style="color: #6b7280; font-size: 12px;">${tipo.toUpperCase()}</span><br/>
        <span style="color: #9ca3af; font-size: 11px;">Lat: ${lat.toFixed(4)}, Lng: ${lng.toFixed(4)}</span>
        <div style="margin-top: 8px; font-size: 11px; color: #6366f1;">
          💡 Arrastra el marcador para analizar
        </div>
      </div>
    `);

    marker.on('dragend', (e) => {
      const newLatLng = e.target.getLatLng();
      const markerData = markersRef.current[id];
      
      if (markerData) {
        markerData.lat = newLatLng.lat;
        markerData.lng = newLatLng.lng;
        markersRef.current[id] = markerData;
      }

      if (onMarkerMove) {
        onMarkerMove({
          id,
          lat: newLatLng.lat,
          lng: newLatLng.lng,
          nombre,
          tipo
        });
      }

      marker.setPopupContent(`
        <div style="min-width: 150px;">
          <strong style="color: #1f2937;">${nombre}</strong><br/>
          <span style="color: #6b7280; font-size: 12px;">${tipo.toUpperCase()}</span><br/>
          <span style="color: #9ca3af; font-size: 11px;">Lat: ${newLatLng.lat.toFixed(4)}, Lng: ${newLatLng.lng.toFixed(4)}</span>
          <div style="margin-top: 8px; font-size: 11px; color: #6366f1;">
            ✅ Nuevo análisis generado
          </div>
        </div>
      `);
    });

    marker.on('click', () => {
      // Marcador seleccionado (id disponible para futura funcionalidad)
    });

    return marker;
  }, [onMarkerMove]);

  useEffect(() => {
    if (map.current) return;

    map.current = L.map(mapContainer.current, {
      center: COMBEIMA_CENTER,
      zoom: DEFAULT_ZOOM,
      zoomControl: true
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 18
    }).addTo(map.current);

    const riverLine = L.polyline([
      [-75.2600, 4.5200],
      [-75.2500, 4.5000],
      [-75.2400, 4.4800],
      [-75.2300, 4.4600],
      [-75.2200, 4.4400],
      [-75.2100, 4.4200],
      [-75.2000, 4.4000],
      [-75.1900, 4.3800],
      [-75.1800, 4.3600]
    ], {
      color: '#0ea5e9',
      weight: 3,
      opacity: 0.8
    }).addTo(map.current);

    riverLine.bindPopup('Río Combeima');

    ESTACIONES_PRESET.forEach(estacion => {
      markersRef.current[estacion.id] = { ...estacion };
      
      const marker = createDraggableMarker(
        estacion.lat,
        estacion.lng,
        estacion.id,
        estacion.name,
        estacion.tipo
      );
      
      marker.addTo(map.current);
    });

    map.current.on('click', (e) => {
      if (onMapClick) {
        onMapClick({
          lat: e.latlng.lat,
          lng: e.latlng.lng
        });
      }
    });

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, [createDraggableMarker, onMapClick]);

  useEffect(() => {
    if (selectedPoint && map.current) {
      map.current.setView([selectedPoint.lat, selectedPoint.lng], 14, {
        animate: true,
        duration: 0.5
      });
    }
  }, [selectedPoint]);

  const centerMap = () => {
    if (map.current) {
      map.current.setView(COMBEIMA_CENTER, DEFAULT_ZOOM, { animate: true });
    }
  };

  const addNewMarker = () => {
    const newId = `CUSTOM-${Date.now()}`;
    const center = map.current.getCenter();
    
    markersRef.current[newId] = {
      id: newId,
      name: 'Nuevo Punto',
      lat: center.lat,
      lng: center.lng,
      tipo: 'custom'
    };

    const marker = createDraggableMarker(
      center.lat,
      center.lng,
      newId,
      'Nuevo Punto',
      'custom'
    );
    
    marker.addTo(map.current);
    marker.openPopup();
  };

  return (
    <div className="relative w-full h-full rounded-xl overflow-hidden shadow-2xl">
      <div ref={mapContainer} className="absolute inset-0" />
      
      <div className="absolute top-4 left-4 z-[1000] bg-white/90 backdrop-blur-sm rounded-lg shadow-lg p-2 space-y-2">
        <h4 className="text-xs font-semibold text-gray-700 px-2">Herramientas</h4>
        <button
          onClick={centerMap}
          className="w-full flex items-center space-x-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors text-sm"
        >
          <span>📍</span>
          <span>Centrar</span>
        </button>
        <button
          onClick={addNewMarker}
          className="w-full flex items-center space-x-2 px-3 py-2 bg-indigo-100 hover:bg-indigo-200 rounded-lg transition-colors text-sm text-indigo-700"
        >
          <span>➕</span>
          <span>Agregar punto</span>
        </button>
      </div>

      <div className="absolute top-4 right-4 z-[1000] bg-white/90 backdrop-blur-sm rounded-lg shadow-lg p-3 max-w-[180px]">
        <h4 className="text-xs font-semibold text-gray-700 mb-2">Leyenda</h4>
        <div className="space-y-2 text-xs">
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-green-500"></span>
            <span>Caudal</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-blue-500"></span>
            <span>Pluviómetro</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-yellow-500"></span>
            <span>Meteorológico</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-purple-500"></span>
            <span>Personalizado</span>
          </div>
        </div>
        <div className="mt-3 pt-2 border-t text-[10px] text-gray-500">
          💡 Arrastra los marcadores para analizar nuevas ubicaciones
        </div>
      </div>

      <div className="absolute bottom-4 left-4 z-[1000] bg-white/90 backdrop-blur-sm rounded-lg shadow-lg p-2">
        <div className="flex items-center space-x-3 text-xs">
          <div className="flex items-center">
            <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
            <span>Normal</span>
          </div>
          <div className="flex items-center">
            <span className="w-2 h-2 bg-yellow-500 rounded-full mr-1"></span>
            <span>Precaución</span>
          </div>
          <div className="flex items-center">
            <span className="w-2 h-2 bg-orange-500 rounded-full mr-1"></span>
            <span>Alerta</span>
          </div>
          <div className="flex items-center">
            <span className="w-2 h-2 bg-red-500 rounded-full mr-1"></span>
            <span>Emergencia</span>
          </div>
        </div>
      </div>

      <div className="absolute bottom-4 right-4 z-[1000] bg-white/90 backdrop-blur-sm rounded-lg shadow-lg px-3 py-2">
        <p className="text-xs text-gray-600">
          <span className="font-medium">{ESTACIONES_PRESET.length}</span> estaciones activas
        </p>
      </div>
    </div>
  );
}

export default InteractiveMap;
