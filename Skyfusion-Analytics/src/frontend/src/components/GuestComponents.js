import React, { useState, useEffect } from 'react';
import { AlertTriangle, Info, X, Clock, ChevronDown, ChevronUp } from 'lucide-react';

function GuestNotice({ user, permissions, onLogout, onUpgrade }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState('');

  useEffect(() => {
    if (user?.expiresAt) {
      const updateTime = () => {
        const now = new Date();
        const expiry = new Date(user.expiresAt);
        const diff = expiry - now;

        if (diff <= 0) {
          setTimeRemaining('Expirada');
          onLogout();
          return;
        }

        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        
        if (hours > 0) {
          setTimeRemaining(`${hours}h ${minutes}m`);
        } else {
          setTimeRemaining(`${minutes} minutos`);
        }
      };

      updateTime();
      const interval = setInterval(updateTime, 60000);
      return () => clearInterval(interval);
    }
  }, [user?.expiresAt, onLogout]);

  if (!user?.isGuest) return null;

  const deniedPermissions = Object.entries(permissions || {})
    .filter(([key, value]) => key.startsWith('can') && value === false)
    .map(([key]) => {
      const names = {
        canViewAlerts: 'Ver alertas personalizadas',
        canViewReports: 'Ver reportes',
        canManageUsers: 'Gestionar usuarios',
        canManageSensors: 'Gestionar sensores',
        canManageProjects: 'Gestionar proyectos',
        canManageCatchments: 'Gestionar cuencas',
        canExportData: 'Exportar datos',
        canCreateAlerts: 'Crear alertas',
        canModifySettings: 'Modificar configuración'
      };
      return names[key] || key;
    });

  const allowedPermissions = Object.entries(permissions || {})
    .filter(([key, value]) => key.startsWith('can') && value === true)
    .map(([key]) => {
      const names = {
        canViewDashboard: 'Ver dashboard',
        canViewMap: 'Ver mapas',
        canViewAnalytics: 'Ver análisis',
        canViewPredictions: 'Ver predicciones'
      };
      return names[key] || key;
    });

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-gradient-to-r from-amber-50 to-orange-50 border-b-2 border-amber-300 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between py-3">
          <div className="flex items-center flex-1">
            <AlertTriangle className="w-5 h-5 text-amber-600 mr-3 flex-shrink-0" />
            <div className="flex-1">
              <div className="flex items-center space-x-3">
                <span className="font-semibold text-amber-900">
                  Modo Invitado
                </span>
                {timeRemaining && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                    <Clock className="w-3 h-3 mr-1" />
                    {timeRemaining} restante
                  </span>
                )}
              </div>
              <p className="text-sm text-amber-700 mt-0.5">
                Estás explorando con acceso limitado. 
                <button 
                  onClick={onUpgrade}
                  className="ml-1 font-medium underline hover:no-underline"
                >
                  Regístrate para acceso completo
                </button>
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-2 text-amber-600 hover:text-amber-700 hover:bg-amber-100 rounded-lg transition-colors"
            >
              {isExpanded ? (
                <ChevronUp className="w-5 h-5" />
              ) : (
                <ChevronDown className="w-5 h-5" />
              )}
            </button>
            <button
              onClick={onLogout}
              className="p-2 text-amber-600 hover:text-amber-700 hover:bg-amber-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {isExpanded && (
          <div className="pb-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white rounded-lg p-4 border border-green-200">
                <h4 className="font-semibold text-green-800 mb-2 flex items-center">
                  <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                  Disponible para ti
                </h4>
                <ul className="space-y-1 text-sm text-green-700">
                  {allowedPermissions.map((perm, idx) => (
                    <li key={idx} className="flex items-center">
                      <span className="w-1 h-1 bg-green-500 rounded-full mr-2"></span>
                      {perm}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-white rounded-lg p-4 border border-red-200">
                <h4 className="font-semibold text-red-800 mb-2 flex items-center">
                  <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                  No disponible
                </h4>
                <ul className="space-y-1 text-sm text-red-700">
                  {deniedPermissions.map((perm, idx) => (
                    <li key={idx} className="flex items-center">
                      <span className="w-1 h-1 bg-red-500 rounded-full mr-2"></span>
                      {perm}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="mt-4 flex justify-end">
              <button
                onClick={onUpgrade}
                className="px-4 py-2 bg-gradient-to-r from-sky-600 to-blue-600 text-white font-medium rounded-lg hover:from-sky-700 hover:to-blue-700 transition-all shadow-md hover:shadow-lg"
              >
                Crear Cuenta Gratis
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function PermissionGate({ permission, children, fallback = null }) {
  const permissions = JSON.parse(localStorage.getItem('permissions') || '{}');
  
  if (permissions[permission] === true) {
    return children;
  }
  
  return fallback;
}

function RestrictedFeature({ featureName, onUpgrade }) {
  return (
    <div className="bg-gray-100 rounded-lg p-6 text-center border-2 border-dashed border-gray-300">
      <AlertTriangle className="w-8 h-8 text-gray-400 mx-auto mb-2" />
      <h3 className="font-medium text-gray-700 mb-2">Función restringida</h3>
      <p className="text-sm text-gray-600 mb-4">
        {featureName} no está disponible en modo invitado.
      </p>
      <button
        onClick={onUpgrade}
        className="px-4 py-2 bg-sky-600 text-white text-sm font-medium rounded-lg hover:bg-sky-700 transition-colors"
      >
        Actualizar a cuenta completa
      </button>
    </div>
  );
}

export { GuestNotice, PermissionGate, RestrictedFeature };
export default GuestNotice;
