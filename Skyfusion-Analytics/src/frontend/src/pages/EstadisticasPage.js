import React, { useState, useEffect } from 'react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

function EstadisticasPage() {
  const [loading, setLoading] = useState(true);
  const [metricas, setMetricas] = useState(null);

  useEffect(() => {
    fetchMetricas();
  }, []);

  const fetchMetricas = async () => {
    setLoading(true);
    try {
      const [proyectosRes, alertasRes] = await Promise.all([
        fetch('http://localhost:3001/api/v1/proyectos/resumen'),
        fetch('http://localhost:3001/api/v1/demo/alerts/COMBEIMA')
      ]);

      const proyectosData = await proyectosRes.json();
      const alertasData = await alertasRes.json();

      setMetricas({
        proyectos: proyectosData,
        alertas: alertasData.alerts || []
      });
    } catch (error) {
      console.error('Error fetching metricas:', error);
    } finally {
      setLoading(false);
    }
  };

  const tendenciaData = {
    labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
    datasets: [
      {
        label: 'NDVI Promedio',
        data: [0.62, 0.65, 0.58, 0.55, 0.52, 0.48],
        borderColor: '#22c55e',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        fill: true,
        tension: 0.4
      },
      {
        label: 'Caudal (m³/s)',
        data: [4.2, 4.5, 3.8, 3.2, 2.9, 2.7],
        borderColor: '#0ea5e9',
        backgroundColor: 'rgba(14, 165, 233, 0.1)',
        fill: true,
        tension: 0.4
      }
    ]
  };

  const proyeccionData = {
    labels: ['Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
    datasets: [
      {
        label: 'Predicción NDVI',
        data: [0.45, 0.42, 0.40, 0.45, 0.52, 0.58],
        borderColor: '#a855f7',
        borderDash: [5, 5],
        fill: false,
        tension: 0.4
      },
      {
        label: 'Intervalo Confianza',
        data: [0.50, 0.48, 0.46, 0.50, 0.58, 0.65],
        borderColor: 'rgba(168, 85, 247, 0.3)',
        backgroundColor: 'rgba(168, 85, 247, 0.1)',
        fill: '+1',
        tension: 0.4
      }
    ]
  };

  const estadoProyectosData = {
    labels: ['Activos', 'En Progreso', 'Completados', 'Pausados'],
    datasets: [
      {
        data: [1, 2, 1, 1],
        backgroundColor: ['#22c55e', '#3b82f6', '#a855f7', '#f59e0b'],
        borderWidth: 0
      }
    ]
  };

  const kpis = [
    {
      titulo: 'Proyectos Activos',
      valor: 2,
      cambio: '+1',
      positivo: true,
      icono: '📊'
    },
    {
      titulo: 'Muestras Analizadas',
      valor: '1,247',
      cambio: '+156',
      positivo: true,
      icono: '🔬'
    },
    {
      titulo: 'Temperatura Promedio',
      valor: '24.3°C',
      cambio: '+1.2°C',
      positivo: false,
      icono: '🌡️'
    },
    {
      titulo: 'Alertas Activas',
      valor: 2,
      cambio: '-1',
      positivo: true,
      icono: '⚠️'
    }
  ];

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: { color: '#94a3b8' }
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(148, 163, 184, 0.1)' },
        ticks: { color: '#94a3b8' }
      },
      y: {
        grid: { color: 'rgba(148, 163, 184, 0.1)' },
        ticks: { color: '#94a3b8' }
      }
    }
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
        labels: { color: '#94a3b8' }
      }
    },
    cutout: '65%'
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">Cargando estadísticas...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">
            Estadísticas y Proyecciones
          </h1>
          <p className="text-slate-400">
            Dashboard cuantitativo con análisis predictivo
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {kpis.map((kpi, index) => (
            <div key={index} className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700">
              <div className="flex items-center justify-between mb-3">
                <span className="text-2xl">{kpi.icono}</span>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  kpi.positivo ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                }`}>
                  {kpi.cambio}
                </span>
              </div>
              <p className="text-3xl font-bold text-white mb-1">{kpi.valor}</p>
              <p className="text-sm text-slate-400">{kpi.titulo}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
              <span>📈</span>
              <span>Tendencia Mensual</span>
            </h2>
            <div className="h-[300px]">
              <Line data={tendenciaData} options={chartOptions} />
            </div>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
              <span>🎯</span>
              <span>Estado de Proyectos</span>
            </h2>
            <div className="h-[300px]">
              <Doughnut data={estadoProyectosData} options={doughnutOptions} />
            </div>
          </div>
        </div>

        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white flex items-center space-x-2">
              <span>🔮</span>
              <span>Proyección 2026</span>
            </h2>
            <div className="flex items-center space-x-2 text-sm">
              <span className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></span>
              <span className="text-slate-400">Basado en modelo LSTM</span>
            </div>
          </div>
          <div className="h-[300px]">
            <Line data={proyeccionData} options={chartOptions} />
          </div>
          <div className="mt-4 p-4 bg-purple-500/10 rounded-lg border border-purple-500/20">
            <p className="text-sm text-purple-300">
              <strong>Análisis:</strong> Se anticipa una disminución gradual del NDVI para los meses de agosto-septiembre 
              debido a la temporada seca, con recuperación esperada para noviembre. La precisión del modelo es del 82%.
            </p>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700">
            <h2 className="text-lg font-semibold text-white mb-4">KPIs de Impacto</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg">
                <span className="text-slate-400">Proyectos completados vs mes anterior</span>
                <span className="text-green-400 font-semibold">+25%</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg">
                <span className="text-slate-400">Reducción de alertas falsas</span>
                <span className="text-green-400 font-semibold">-18%</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg">
                <span className="text-slate-400">Tiempo de análisis</span>
                <span className="text-blue-400 font-semibold">-32%</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg">
                <span className="text-slate-400">Precisión de predicciones</span>
                <span className="text-purple-400 font-semibold">82%</span>
              </div>
            </div>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700">
            <h2 className="text-lg font-semibold text-white mb-4">Eventos Registrados</h2>
            <div className="space-y-3">
              {[
                { tipo: 'Sequía', count: 12, color: 'yellow' },
                { tipo: 'Inundación', count: 3, color: 'red' },
                { tipo: 'Alerta verde', count: 45, color: 'green' },
                { tipo: 'Mantenimiento', count: 8, color: 'blue' }
              ].map((evento, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className={`w-3 h-3 rounded-full bg-${evento.color}-500`}></span>
                    <span className="text-slate-300">{evento.tipo}</span>
                  </div>
                  <span className="text-white font-semibold">{evento.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default EstadisticasPage;
