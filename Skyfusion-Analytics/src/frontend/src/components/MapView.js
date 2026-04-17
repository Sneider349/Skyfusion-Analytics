import React, { useRef, useEffect, useState } from 'react';

const COMBEIMA_CENTER = { lat: 4.539324915299756, lng: -75.31540320818968 };

const stations = [
  { id: 'COMB-001', name: 'Puente Combeima', lat: 4.559473, lng: -75.320521, type: 'caudal' },
  { id: 'COMB-002', name: 'El Carmen', lat: 4.3010648002920675, lng: -75.21487306865815, type: 'pluviometro' },
  { id: 'COMB-003', name: 'Buenavista', lat: 4.506860108157828, lng: -75.10367078688878, type: 'caudal' },
  { id: 'COMB-004', name: 'Toche', lat: 4.4789, lng: -75.40921803550827, type: 'meteo' }
];

function MapView({ catchmentId, selectedLayers, onToggleLayer, onMapReady }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const layersRef = useRef({
    markers: [],
    riverLayer: null,
    waterLayer: null,
    vegLayer: null
  });
  const loadedRef = useRef({
    rivers: false,
    ndwi: false,
    ndvi: false
  });
  const [mapReady, setMapReady] = useState(false);

  useEffect(() => {
    let mounted = true;

    const initMap = async () => {
      if (!containerRef.current || mapRef.current) return;

      try {
        const L = (await import('leaflet')).default;
        await import('leaflet/dist/leaflet.css');

        if (!mounted || !containerRef.current) return;

        const map = L.map(containerRef.current, {
          center: [COMBEIMA_CENTER.lat, COMBEIMA_CENTER.lng],
          zoom: 12
        });

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '© OpenStreetMap'
        }).addTo(map);

        const markers = stations.map(st => {
          const color = st.type === 'caudal' ? '#22c55e' : st.type === 'pluviometro' ? '#3b82f6' : '#f59e0b';
          return L.circleMarker([st.lat, st.lng], {
            radius: 8,
            fillColor: color,
            color: '#fff',
            weight: 2,
            fillOpacity: 1
          }).bindPopup(`<b>${st.name}</b><br/>${st.type}`);
        });

        layersRef.current.markers = markers;
        mapRef.current = { map, L };

        setMapReady(true);
        loadedRef.current = { rivers: false, ndwi: false, ndvi: false };

        setTimeout(() => map.invalidateSize(), 100);

        const searchByCoordinates = (lat, lng) => {
          if (!mapRef.current) return;
          const { map: currentMap, L: Leaflet } = mapRef.current;
          const marker = Leaflet.circleMarker([lat, lng], {
            radius: 10,
            fillColor: '#ef4444',
            color: '#fff',
            weight: 3,
            fillOpacity: 1
          }).bindPopup(`<b>Busqueda</b><br/>Lat: ${lat.toFixed(6)}<br/>Lng: ${lng.toFixed(6)}`).addTo(currentMap);
          currentMap.setView([lat, lng], 14);
        };

        if (onMapReady) onMapReady({ searchByCoordinates });
      } catch (err) {
        console.error('Map init error:', err);
      }
    };

    initMap();

    return () => {
      mounted = false;
      if (mapRef.current) {
        try { mapRef.current.map.remove(); } catch (e) {}
        mapRef.current = null;
      }
      layersRef.current = { markers: [], riverLayer: null, waterLayer: null, vegLayer: null };
      loadedRef.current = { rivers: false, ndwi: false, ndvi: false };
    };
  }, []);

  useEffect(() => {
    if (!mapReady || !mapRef.current) return;

    const { map } = mapRef.current;

    if (selectedLayers.sensors) {
      layersRef.current.markers.forEach(m => {
        if (!map.hasLayer(m)) m.addTo(map);
      });
    } else {
      layersRef.current.markers.forEach(m => {
        if (map.hasLayer(m)) map.removeLayer(m);
      });
    }
  }, [selectedLayers.sensors, mapReady]);

  useEffect(() => {
    if (!mapReady || !mapRef.current) return;

    const { map, L } = mapRef.current;

    if (selectedLayers.rivers) {
      if (layersRef.current.riverLayer && !map.hasLayer(layersRef.current.riverLayer)) {
        layersRef.current.riverLayer.addTo(map);
      } else if (!layersRef.current.riverLayer && !loadedRef.current.rivers) {
        loadedRef.current.rivers = true;
        const bbox = '4.3,-75.45,4.6,-75.1';
        const url = `https://overpass-api.de/api/interpreter?data=[out:json][timeout:25];way["waterway"](${bbox});out geom;`;

        fetch(url)
          .then(r => r.json())
          .then(data => {
            if (!mapRef.current) return;
            const coords = data.elements.map(el => el.geometry.map(g => [g.lat, g.lon]));
            const riverLayer = L.polyline(coords, {
              color: '#1e88e5',
              weight: 4,
              opacity: 0.9
            });
            layersRef.current.riverLayer = riverLayer;
            if (mapRef.current && selectedLayers.rivers) {
              riverLayer.addTo(mapRef.current.map);
            }
          })
          .catch(err => {
            console.error('Error loading rivers:', err);
            loadedRef.current.rivers = false;
          });
      }
    } else {
      if (layersRef.current.riverLayer && map.hasLayer(layersRef.current.riverLayer)) {
        map.removeLayer(layersRef.current.riverLayer);
      }
    }
  }, [selectedLayers.rivers, mapReady]);

  useEffect(() => {
    if (!mapReady || !mapRef.current) return;

    const { map, L } = mapRef.current;

    if (selectedLayers.ndwi) {
      if (layersRef.current.waterLayer && !map.hasLayer(layersRef.current.waterLayer)) {
        layersRef.current.waterLayer.addTo(map);
      } else if (!layersRef.current.waterLayer && !loadedRef.current.ndwi) {
        loadedRef.current.ndwi = true;
        const bbox = '4.3,-75.45,4.6,-75.1';
        const url = `https://overpass-api.de/api/interpreter?data=[out:json][timeout:25];(way["natural"="water"](${bbox});way["water"](${bbox}););out geom;`;

        fetch(url)
          .then(r => r.json())
          .then(data => {
            if (!mapRef.current) return;

            const features = data.elements.map(el => {
              if (el.geometry && el.geometry.length > 2) {
                const ring = el.geometry.map(g => [g.lat, g.lon]);
                ring.push(ring[0]);
                return L.polygon([ring], {
                  color: '#0284c7',
                  fillColor: '#38bdf8',
                  fillOpacity: 0.5,
                  weight: 1
                });
              } else if (el.geometry) {
                const coords = el.geometry.map(g => [g.lat, g.lon]);
                return L.polyline(coords, {
                  color: '#0284c7',
                  weight: 3,
                  opacity: 0.8
                });
              }
              return null;
            }).filter(Boolean);

            if (features.length > 0) {
              const waterLayer = L.layerGroup(features);
              layersRef.current.waterLayer = waterLayer;
              if (mapRef.current && selectedLayers.ndwi) {
                waterLayer.addTo(mapRef.current.map);
              }
            }
          })
          .catch(err => {
            console.error('Error loading water:', err);
            loadedRef.current.ndwi = false;
          });
      }
    } else {
      if (layersRef.current.waterLayer && map.hasLayer(layersRef.current.waterLayer)) {
        map.removeLayer(layersRef.current.waterLayer);
      }
    }
  }, [selectedLayers.ndwi, mapReady]);

  useEffect(() => {
    if (!mapReady || !mapRef.current) return;

    const { map, L } = mapRef.current;

    if (selectedLayers.ndvi) {
      if (layersRef.current.vegLayer && !map.hasLayer(layersRef.current.vegLayer)) {
        layersRef.current.vegLayer.addTo(map);
      } else if (!layersRef.current.vegLayer && !loadedRef.current.ndvi) {
        loadedRef.current.ndvi = true;
        const bbox = '4.3,-75.45,4.6,-75.1';
        const url = `https://overpass-api.de/api/interpreter?data=[out:json][timeout:25];(way["landuse"="forest"](${bbox});way["natural"="wood"](${bbox}););out geom;`;

        fetch(url)
          .then(r => r.json())
          .then(data => {
            if (!mapRef.current) return;

            const features = data.elements.map(el => {
              if (el.geometry && el.geometry.length > 2) {
                const ring = el.geometry.map(g => [g.lat, g.lon]);
                ring.push(ring[0]);
                return L.polygon([ring], {
                  color: '#16a34a',
                  fillColor: '#22c55e',
                  fillOpacity: 0.4,
                  weight: 1
                });
              }
              return null;
            }).filter(Boolean);

            if (features.length > 0) {
              const vegLayer = L.layerGroup(features);
              layersRef.current.vegLayer = vegLayer;
              if (mapRef.current && selectedLayers.ndvi) {
                vegLayer.addTo(mapRef.current.map);
              }
            }
          })
          .catch(err => {
            console.error('Error loading vegetation:', err);
            loadedRef.current.ndvi = false;
          });
      }
    } else {
      if (layersRef.current.vegLayer && map.hasLayer(layersRef.current.vegLayer)) {
        map.removeLayer(layersRef.current.vegLayer);
      }
    }
  }, [selectedLayers.ndvi, mapReady]);

  const handleToggle = (key) => {
    if (onToggleLayer) onToggleLayer(key);
  };

  return (
    <div className="relative bg-white rounded-lg shadow-md" style={{ height: '500px' }}>
      <div ref={containerRef} className="absolute inset-0" />

      <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-4 z-[1000]" style={{ minWidth: '180px' }}>
        <h4 className="text-sm font-bold mb-3">Capas</h4>
        <div className="space-y-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={selectedLayers.rivers} onChange={() => handleToggle('rivers')} />
            <span className="w-3 h-3 rounded-full bg-sky-500"></span>
            Ríos
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={selectedLayers.sensors} onChange={() => handleToggle('sensors')} />
            <span className="w-3 h-3 rounded-full bg-orange-500"></span>
            Estaciones
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={selectedLayers.ndvi} onChange={() => handleToggle('ndvi')} />
            <span className="w-3 h-3 rounded-full bg-green-500"></span>
            Vegetación
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={selectedLayers.ndwi} onChange={() => handleToggle('ndwi')} />
            <span className="w-3 h-3 rounded-full bg-blue-500"></span>
            Agua
          </label>
        </div>
      </div>

      <div className="absolute bottom-4 left-4 bg-white rounded shadow px-3 py-2 text-xs">
        {stations.length} estaciones
      </div>
    </div>
  );
}

export default MapView;
