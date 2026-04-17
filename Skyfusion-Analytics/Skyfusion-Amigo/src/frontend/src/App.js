import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import MapView from './components/MapView';
import MetricsPanel from './components/MetricsPanel';
import AlertsPanel from './components/AlertsPanel';
import PredictionsPanel from './components/PredictionsPanel';
import NarrativePanel from './components/NarrativePanel';
import { fetchMetrics, fetchAlerts, fetchPredictions, fetchNarrative } from './services/api';
import { useWebSocket } from './hooks/useWebSocket';
import AnalisisPage from './pages/AnalisisPage';
import ProjectsPage from './pages/ProjectsPage';
import EstadisticasPage from './pages/EstadisticasPage';
import AdminPage from './pages/AdminPage';
import LoginPage from './pages/LoginPage';
import { GuestNotice } from './components/GuestComponents';

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-sky-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Cargando...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}

function DashboardWithAuth() {
  const { user, permissions, isGuest, logout } = useAuth();
  const navigate = useNavigate();
  const [catchmentId] = useState('COMBEIMA');
  const [metrics, setMetrics] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [narrative, setNarrative] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedLayers, setSelectedLayers] = useState({
    ndvi: true,
    ndwi: true,
    rivers: true,
    sensors: true
  });
  const [mapRef, setMapRef] = useState(null);

  const { lastMessage } = useWebSocket(`catchment:${catchmentId}`);

  useEffect(() => {
    loadData();
  }, [catchmentId]);

  useEffect(() => {
    if (lastMessage) {
      if (lastMessage.type === 'prediction') {
        setPredictions(lastMessage.data.predictions);
      } else if (lastMessage.type === 'alert') {
        setAlerts(prev => [lastMessage.data, ...prev.filter(a => a.id !== lastMessage.data.id)]);
      } else if (lastMessage.type === 'metrics') {
        setMetrics(prev => ({
          ...prev,
          ...lastMessage.data.metrics
        }));
      }
    }
  }, [lastMessage]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [metricsData, alertsData, predictionsData, narrativeData] = await Promise.all([
        fetchMetrics(catchmentId),
        fetchAlerts(catchmentId),
        fetchPredictions(catchmentId),
        fetchNarrative(catchmentId)
      ]);

      setMetrics(metricsData.metrics);
      setAlerts(alertsData);
      setPredictions(predictionsData);
      setNarrative(narrativeData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleLayer = (layer) => {
    setSelectedLayers(prev => ({
      ...prev,
      [layer]: !prev[layer]
    }));
  };

  const handleSearch = async (query) => {
    if (!query || !mapRef) return;
    const cleaned = query.trim().replace(/,/g, ' ').replace(/\s+/g, ' ');
    const parts = cleaned.split(' ');
    if (parts.length >= 2) {
      const lat = parseFloat(parts[0]);
      const lng = parseFloat(parts[1]);
      if (!isNaN(lat) && !isNaN(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
        mapRef.searchByCoordinates(lat, lng);
        return;
      }
    }
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1`,
        { headers: { 'User-Agent': 'SkyfusionAnalytics/1.0' } }
      );
      const data = await response.json();
      if (data && data.length > 0) {
        mapRef.searchByCoordinates(parseFloat(data[0].lat), parseFloat(data[0].lon));
      }
    } catch (e) {
      console.error('Search error:', e);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleUpgrade = () => {
    navigate('/login', { state: { showRegister: true } });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-sky-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Cargando Skyfusion Analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <GuestNotice
        user={user}
        permissions={permissions}
        onLogout={handleLogout}
        onUpgrade={handleUpgrade}
      />
      <div className={isGuest ? 'pt-16' : ''}>
        <Header onSearch={handleSearch} />
        <Sidebar />
        <main className="container mx-auto p-4 pt-20 pl-16">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
            <div className="lg:col-span-3">
              <MapView 
                catchmentId={catchmentId}
                selectedLayers={selectedLayers}
                onToggleLayer={toggleLayer}
                onMapReady={(mapMethods) => setMapRef(mapMethods)}
              />
            </div>

            <div className="space-y-4">
              <AlertsPanel alerts={alerts} />
              <NarrativePanel narrative={narrative} />
            </div>
          </div>

          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricsPanel
              title="Caudal"
              value={metrics?.caudal?.value || '4.2'}
              unit={metrics?.caudal?.unit || 'm³/s'}
              status={metrics?.caudal?.status || 'normal'}
              trend={metrics?.caudal?.trend || 'stable'}
            />
            <MetricsPanel
              title="NDVI"
              value={metrics?.ndvi?.value || '0.65'}
              unit=""
              status={metrics?.ndvi?.status || 'healthy'}
              trend={metrics?.ndvi?.trend || 'stable'}
            />
            <MetricsPanel
              title="Precipitación"
              value={metrics?.precipitacion?.value || '12'}
              unit={metrics?.precipitacion?.unit || 'mm'}
              status={metrics?.precipitacion?.status || 'normal'}
              trend={metrics?.precipitacion?.trend || 'stable'}
            />
            <MetricsPanel
              title="Temperatura"
              value={metrics?.temperatura?.value || '24'}
              unit={metrics?.temperatura?.unit || '°C'}
              status={metrics?.temperatura?.status || 'normal'}
              trend={metrics?.temperatura?.trend || 'stable'}
            />
          </div>

          <div className="mt-4">
            <PredictionsPanel predictions={predictions} />
          </div>
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardWithAuth />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route
            path="/analisis"
            element={
              <ProtectedRoute>
                <AnalisisPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/proyectos"
            element={
              <ProtectedRoute>
                <ProjectsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/estadisticas"
            element={
              <ProtectedRoute>
                <EstadisticasPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute>
                <AdminPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;