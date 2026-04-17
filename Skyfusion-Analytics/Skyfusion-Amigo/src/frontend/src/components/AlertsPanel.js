import React, { useState, useEffect, useRef } from 'react';
import { AlertTriangle, CheckCircle, Info, Bell, X, Clock, RefreshCw, MapPin, ChevronDown, ChevronUp } from 'lucide-react';

function AlertsPanel({ alerts = [], catchmentId, onRefresh, autoRefresh = true, refreshInterval = 30000 }) {
  const [expandedAlert, setExpandedAlert] = useState(null);
  const [localAlerts, setLocalAlerts] = useState(alerts);
  const [loading, setLoading] = useState(false);
  const intervalRef = useRef(null);

  useEffect(() => {
    setLocalAlerts(alerts);
  }, [alerts]);

  useEffect(() => {
    if (autoRefresh && onRefresh) {
      intervalRef.current = setInterval(() => {
        onRefresh();
      }, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [autoRefresh, onRefresh, refreshInterval]);

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'red':
        return 'bg-red-50 border-red-300 hover:bg-red-100';
      case 'orange':
        return 'bg-orange-50 border-orange-300 hover:bg-orange-100';
      case 'yellow':
        return 'bg-yellow-50 border-yellow-300 hover:bg-yellow-100';
      default:
        return 'bg-green-50 border-green-300 hover:bg-green-100';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'red':
        return <AlertTriangle className="w-5 h-5 text-red-600" />;
      case 'orange':
        return <AlertTriangle className="w-5 h-5 text-orange-500" />;
      case 'yellow':
        return <Info className="w-5 h-5 text-yellow-600" />;
      default:
        return <CheckCircle className="w-5 h-5 text-green-600" />;
    }
  };

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'red':
        return 'bg-red-600 text-white';
      case 'orange':
        return 'bg-orange-500 text-white';
      case 'yellow':
        return 'bg-yellow-500 text-white';
      default:
        return 'bg-green-600 text-white';
    }
  };

  const getSeverityLabel = (severity) => {
    switch (severity) {
      case 'red':
        return 'Crítico';
      case 'orange':
        return 'Advertencia';
      case 'yellow':
        return 'Precaución';
      default:
        return 'Normal';
    }
  };

  const formatTime = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);

    if (diffMins < 1) return 'Ahora mismo';
    if (diffMins < 60) return `Hace ${diffMins} min`;
    if (diffHours < 24) return `Hace ${diffHours} h`;
    return date.toLocaleDateString('es-CO', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  const handleRefresh = async () => {
    if (!onRefresh) return;
    setLoading(true);
    try {
      await onRefresh();
    } finally {
      setLoading(false);
    }
  };

  const handleToggleExpand = (alertId) => {
    setExpandedAlert(expandedAlert === alertId ? null : alertId);
  };

  const criticalAlerts = localAlerts.filter(a => a.severity === 'red');
  const warningAlerts = localAlerts.filter(a => a.severity === 'orange');
  const cautionAlerts = localAlerts.filter(a => a.severity === 'yellow');
  const normalAlerts = localAlerts.filter(a => a.severity === 'green');

  const totalActive = criticalAlerts.length + warningAlerts.length + cautionAlerts.length;

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Bell className="w-5 h-5 text-sky-600" />
          <h3 className="text-lg font-semibold text-gray-800">Alertas Activas</h3>
          {totalActive > 0 && (
            <span className="px-2 py-0.5 text-xs font-bold bg-sky-100 text-sky-700 rounded-full">
              {totalActive}
            </span>
          )}
        </div>
        {onRefresh && (
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="p-2 text-gray-500 hover:text-sky-600 hover:bg-sky-50 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        )}
      </div>

      {catchmentId && (
        <div className="flex items-center text-xs text-gray-500 mb-3 pb-3 border-b border-gray-100">
          <MapPin className="w-3 h-3 mr-1" />
          <span>Cuenca: {catchmentId}</span>
        </div>
      )}

      <div className="space-y-2">
        {localAlerts && localAlerts.length > 0 ? (
          <>
            {criticalAlerts.length > 0 && (
              <div className="mb-3">
                <div className="text-xs font-semibold text-red-600 uppercase tracking-wide mb-2">
                  Críticas ({criticalAlerts.length})
                </div>
                {criticalAlerts.map((alert, index) => (
                  <AlertCard 
                    key={alert.id || `critical-${index}`}
                    alert={alert}
                    expanded={expandedAlert === alert.id}
                    onToggle={() => handleToggleExpand(alert.id)}
                    getSeverityColor={getSeverityColor}
                    getSeverityIcon={getSeverityIcon}
                    getSeverityBadge={getSeverityBadge}
                    getSeverityLabel={getSeverityLabel}
                    formatTime={formatTime}
                  />
                ))}
              </div>
            )}

            {warningAlerts.length > 0 && (
              <div className="mb-3">
                <div className="text-xs font-semibold text-orange-500 uppercase tracking-wide mb-2">
                  Advertencias ({warningAlerts.length})
                </div>
                {warningAlerts.map((alert, index) => (
                  <AlertCard 
                    key={alert.id || `warning-${index}`}
                    alert={alert}
                    expanded={expandedAlert === alert.id}
                    onToggle={() => handleToggleExpand(alert.id)}
                    getSeverityColor={getSeverityColor}
                    getSeverityIcon={getSeverityIcon}
                    getSeverityBadge={getSeverityBadge}
                    getSeverityLabel={getSeverityLabel}
                    formatTime={formatTime}
                  />
                ))}
              </div>
            )}

            {cautionAlerts.length > 0 && (
              <div className="mb-3">
                <div className="text-xs font-semibold text-yellow-600 uppercase tracking-wide mb-2">
                  Precauciones ({cautionAlerts.length})
                </div>
                {cautionAlerts.map((alert, index) => (
                  <AlertCard 
                    key={alert.id || `caution-${index}`}
                    alert={alert}
                    expanded={expandedAlert === alert.id}
                    onToggle={() => handleToggleExpand(alert.id)}
                    getSeverityColor={getSeverityColor}
                    getSeverityIcon={getSeverityIcon}
                    getSeverityBadge={getSeverityBadge}
                    getSeverityLabel={getSeverityLabel}
                    formatTime={formatTime}
                  />
                ))}
              </div>
            )}

            {normalAlerts.length > 0 && (
              <div>
                <div className="text-xs font-semibold text-green-600 uppercase tracking-wide mb-2">
                  Normales ({normalAlerts.length})
                </div>
                {normalAlerts.map((alert, index) => (
                  <AlertCard 
                    key={alert.id || `normal-${index}`}
                    alert={alert}
                    expanded={expandedAlert === alert.id}
                    onToggle={() => handleToggleExpand(alert.id)}
                    getSeverityColor={getSeverityColor}
                    getSeverityIcon={getSeverityIcon}
                    getSeverityBadge={getSeverityBadge}
                    getSeverityLabel={getSeverityLabel}
                    formatTime={formatTime}
                  />
                ))}
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg">
            <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-400" />
            <p className="font-medium text-gray-700">Sin alertas activas</p>
            <p className="text-sm mt-1">Todas las condiciones están normales</p>
          </div>
        )}
      </div>
    </div>
  );
}

function AlertCard({ alert, expanded, onToggle, getSeverityColor, getSeverityIcon, getSeverityBadge, getSeverityLabel, formatTime }) {
  return (
    <div 
      className={`p-3 rounded-lg border transition-all duration-200 ${getSeverityColor(alert.severity)} ${
        expanded ? 'shadow-md' : 'hover:shadow-sm'
      }`}
    >
      <div 
        className="flex items-start cursor-pointer"
        onClick={onToggle}
      >
        <div className="flex-shrink-0 mt-0.5">
          {getSeverityIcon(alert.severity)}
        </div>
        <div className="flex-1 ml-3 min-w-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className={`px-2 py-0.5 text-xs font-medium rounded ${getSeverityBadge(alert.severity)}`}>
                {getSeverityLabel(alert.severity)}
              </span>
              {alert.catchment_id && (
                <span className="text-xs text-gray-500">{alert.catchment_id}</span>
              )}
            </div>
            {expanded ? (
              <ChevronUp className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            )}
          </div>
          
          <p className="text-sm font-medium text-gray-800 mt-1">{alert.message}</p>
          
          <div className="flex items-center text-xs text-gray-500 mt-2">
            <Clock className="w-3 h-3 mr-1" />
            <span>{formatTime(alert.created_at)}</span>
            {alert.probability && (
              <span className="ml-3 px-2 py-0.5 bg-white/50 rounded">
                Prob: {Math.round(alert.probability * 100)}%
              </span>
            )}
          </div>

          {expanded && alert.recommendations && alert.recommendations.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-200/50">
              <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
                Recomendaciones
              </p>
              <ul className="space-y-1">
                {alert.recommendations.map((rec, i) => (
                  <li key={i} className="text-xs text-gray-600 flex items-start">
                    <span className="text-sky-500 mr-1">•</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AlertsPanel;