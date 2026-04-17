import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

function MetricsPanel({ title, value, unit, status, trend }) {
  const getStatusColor = () => {
    switch (status) {
      case 'healthy':
      case 'normal':
        return 'bg-green-50 border-green-200 text-green-700';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-700';
      case 'danger':
      case 'critical':
        return 'bg-red-50 border-red-200 text-red-700';
      default:
        return 'bg-white border-gray-200';
    }
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-green-500" />;
      case 'down':
        return <TrendingDown className="w-4 h-4 text-red-500" />;
      default:
        return <Minus className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className={`metric-card border ${getStatusColor()}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-600">{title}</span>
        {getTrendIcon()}
      </div>
      <div className="flex items-baseline">
        <span className="text-2xl font-bold">{value}</span>
        <span className="text-sm ml-1 text-gray-500">{unit}</span>
      </div>
    </div>
  );
}

export default MetricsPanel;
