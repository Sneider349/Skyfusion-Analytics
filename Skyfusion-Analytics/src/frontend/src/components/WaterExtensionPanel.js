import React, { useState, useEffect } from 'react';
import { Bar } from 'react-chartjs-2';
import { Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend);

function WaterExtensionPanel({ catchmentId = 'COMBEIMA', waterExtensionPrediction }) {
  const [activeHorizon, setActiveHorizon] = useState(7);
  const [predictionData, setPredictionData] = useState(null);
  
  useEffect(() => {
    if (waterExtensionPrediction) {
      setPredictionData(waterExtensionPrediction);
    }
  }, [waterExtensionPrediction]);
  
  const horizons = [
    { value: 7, label: '7 días', color: 'bg-blue-500' },
    { value: 14, label: '14 días', color: 'bg-amber-500' },
    { value: 30, label: '30 días', color: 'bg-purple-500' }
  ];
  
  const riskColors = {
    high_flood: { bg: 'bg-red-100', border: 'border-red-500', text: 'text-red-700' },
    moderate_flood: { bg: 'bg-orange-100', border: 'border-orange-500', text: 'text-orange-700' },
    normal: { bg: 'bg-green-100', border: 'border-green-500', text: 'text-green-700' },
    moderate_drought: { bg: 'bg-yellow-100', border: 'border-yellow-500', text: 'text-yellow-700' },
    high_drought: { bg: 'bg-amber-100', border: 'border-amber-500', text: 'text-amber-700' },
    unknown: { bg: 'bg-gray-100', border: 'border-gray-500', text: 'text-gray-700' }
  };
  
  const getRiskLabel = (risk) => {
    const labels = {
      high_flood: 'Riesgo Alto de Inundación',
      moderate_flood: 'Riesgo Moderado de Inundación',
      normal: 'Condiciones Normales',
      moderate_drought: 'Riesgo Moderado de Sequía',
      high_drought: 'Riesgo Alto de Sequía',
      unknown: 'Sin datos'
    };
    return labels[risk] || 'Desconocido';
  };
  
  const barData = {
    labels: ['7 días', '14 días', '30 días'],
    datasets: [
      {
        label: 'Extensión de Agua Predicha',
        data: predictionData?.horizons
          ? [
              predictionData.horizons.h7?.water_extension?.predicted_area_ratio * 100 || 0,
              predictionData.horizons.h14?.water_extension?.predicted_area_ratio * 100 || 0,
              predictionData.horizons.h30?.water_extension?.predicted_area_ratio * 100 || 0
            ]
          : [30, 35, 32],
        backgroundColor: ['rgba(14, 165, 233, 0.7)', 'rgba(245, 158, 11, 0.7)', 'rgba(168, 85, 247, 0.7)'],
        borderColor: ['rgb(14, 165, 233)', 'rgb(245, 158, 11)', 'rgb(168, 85, 247)'],
        borderWidth: 1
      }
    ]
  };
  
  const doughnutData = {
    labels: ['Agua', 'Tierra'],
    datasets: [
      {
        data: predictionData
          ? [
              predictionData.horizons?.[`h${activeHorizon}`]?.water_extension?.predicted_area_ratio || 0.3,
              1 - (predictionData.horizons?.[`h${activeHorizon}`]?.water_extension?.predicted_area_ratio || 0.3)
            ]
          : [0.3, 0.7],
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(34, 197, 94, 0.8)'
        ],
        borderColor: [
          'rgb(59, 130, 246)',
          'rgb(34, 197, 94)'
        ],
        borderWidth: 1
      }
    ]
  };
  
  const barOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top'
      },
      title: {
        display: true,
        text: 'Predicción de Extensión de Agua por Horizonte'
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        title: {
          display: true,
          text: 'Porcentaje de Área (%)'
        }
      }
    }
  };
  
  const doughnutOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'bottom'
      },
      title: {
        display: true,
        text: `Distribución Agua/Tierra - ${activeHorizon} días`
      }
    }
  };
  
  const currentPrediction = predictionData?.horizons?.[`h${activeHorizon}`]?.water_extension;
  const currentRisk = currentPrediction?.risk_level || 'unknown';
  const riskStyle = riskColors[currentRisk];
  
  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-800">
          Predicción de Extensión de Agua
        </h3>
        <p className="text-sm text-gray-500">
          Cuenca: {catchmentId}
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        {horizons.map((h) => (
          <button
            key={h.value}
            onClick={() => setActiveHorizon(h.value)}
            className={`p-3 rounded-lg border-2 transition-all ${
              activeHorizon === h.value
                ? `${h.color} text-white border-transparent`
                : 'bg-gray-50 border-gray-200 hover:border-gray-400'
            }`}
          >
            <div className="font-medium">{h.label}</div>
            <div className="text-xs opacity-75">
              {predictionData?.horizons?.[`h${h.value}`]?.water_extension?.predicted_area_ratio
                ? `${(predictionData.horizons[`h${h.value}`].water_extension.predicted_area_ratio * 100).toFixed(1)}%`
                : '--'}
            </div>
          </button>
        ))}
      </div>
      
      <div className={`p-4 rounded-lg border-2 ${riskStyle.bg} ${riskStyle.border} ${riskStyle.text} mb-4`}>
        <div className="flex items-center justify-between">
          <div>
            <span className="font-semibold">Nivel de Riesgo: </span>
            <span className="font-bold">{getRiskLabel(currentRisk)}</span>
          </div>
          <div className="text-right">
            <span className="text-sm">Confianza: </span>
            <span className="font-bold">
              {currentPrediction?.confidence
                ? `${(currentPrediction.confidence * 100).toFixed(0)}%`
                : '--'}
            </span>
          </div>
        </div>
        <div className="mt-2 text-sm">
          Área predicha: <span className="font-semibold">
            {currentPrediction?.area_km2
              ? `${currentPrediction.area_km2} km²`
              : '--'}
          </span>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Bar data={barData} options={barOptions} />
        </div>
        <div>
          <Doughnut data={doughnutData} options={doughnutOptions} />
        </div>
      </div>
      
      {predictionData?.trend_analysis && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <h4 className="font-semibold text-gray-700 mb-2">Análisis de Tendencia</h4>
          <div className="flex items-center gap-4">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              predictionData.trend_analysis.trend === 'increasing' 
                ? 'bg-red-100 text-red-700'
                : predictionData.trend_analysis.trend === 'decreasing'
                  ? 'bg-amber-100 text-amber-700'
                  : 'bg-green-100 text-green-700'
            }`}>
              {predictionData.trend_analysis.trend === 'increasing' ? '↗️ Tendencia Creciente' :
               predictionData.trend_analysis.trend === 'decreasing' ? '↘️ Tendencia Decreciente' :
               '→ Estable'}
            </span>
            <span className="text-sm text-gray-600">
              {predictionData.trend_analysis.recommendation}
            </span>
          </div>
        </div>
      )}
      
      <div className="mt-4 text-xs text-gray-400">
        <p>Modelo: CNN-LSTM-Attention | Arquitectura: Espacial-Temporal</p>
        <p>Resolución: 30m | Datos: Landsat/Sentinel + Sensores IoT</p>
      </div>
    </div>
  );
}

export default WaterExtensionPanel;
