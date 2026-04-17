import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Menu, X, Home, Map, Bell, BarChart3, FolderOpen, FileText, 
  Settings, LogOut, User, ChevronRight, Layers, Activity,
  Droplets, CloudRain, Thermometer, Leaf, Info
} from 'lucide-react';
import { useAuth } from '../hooks/useNotifications';

const menuItems = [
  { id: 'dashboard', label: 'Dashboard', icon: Home, path: '/' },
  { id: 'map', label: 'Mapa Interactivo', icon: Map, path: '/map' },
  { id: 'layers', label: 'Capas', icon: Layers, path: '/layers' },
  { id: 'stations', label: 'Estaciones', icon: Activity, path: '/stations' },
  { id: 'metrics', label: 'Métricas', icon: BarChart3, path: '/metrics' },
];

const analysisItems = [
  { id: 'analisis', label: 'Análisis', icon: FolderOpen, path: '/analisis' },
  { id: 'projects', label: 'Proyectos', icon: FolderOpen, path: '/projects' },
  { id: 'predictions', label: 'Predicciones', icon: BarChart3, path: '/predictions' },
];

const reportsItems = [
  { id: 'reports', label: 'Reportes', icon: FileText, path: '/reports' },
  { id: 'statistics', label: 'Estadísticas', icon: BarChart3, path: '/statistics' },
];

const settingsItems = [
  { id: 'settings', label: 'Configuración', icon: Settings, path: '/settings' },
  { id: 'admin', label: 'Administración', icon: Settings, path: '/admin', adminOnly: true },
];

export default function Sidebar() {
  const [isOpen, setIsOpen] = useState(false);
  const [expandedMenus, setExpandedMenus] = useState({});
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const toggleMenu = (menuId) => {
    setExpandedMenus(prev => ({
      ...prev,
      [menuId]: !prev[menuId]
    }));
  };

  const handleNavigation = (path) => {
    navigate(path);
    setIsOpen(false);
  };

  const handleLogout = () => {
    logout();
    setIsOpen(false);
    navigate('/');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="fixed top-16 left-4 z-[9997] p-2 bg-white rounded-lg shadow-md hover:bg-gray-50 transition-colors"
      >
        <Menu className="w-6 h-6 text-gray-700" />
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-[10000]" onClick={() => setIsOpen(false)}>
          <div className="absolute inset-0 bg-black/50" />
        </div>
      )}

      <div 
        className={`fixed top-0 left-0 h-full w-72 bg-white shadow-2xl z-[10001] transform transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-sky-600 to-indigo-600">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
              <span className="text-sky-600 font-bold text-lg">SF</span>
            </div>
            <div>
              <h2 className="text-white font-bold">Skyfusion</h2>
              <p className="text-sky-100 text-xs">Analytics</p>
            </div>
          </div>
          <button onClick={() => setIsOpen(false)} className="p-1 text-white/80 hover:text-white">
            <X className="w-6 h-6" />
          </button>
        </div>

        {isAuthenticated && user && (
          <div className="p-4 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-sky-500 rounded-full flex items-center justify-center">
                <User className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-gray-900 truncate">{user.fullName || user.username}</p>
                <p className="text-sm text-gray-500 truncate">{user.email}</p>
                <span className="inline-block mt-1 px-2 py-0.5 text-xs bg-sky-100 text-sky-700 rounded">
                  {user.role || 'Usuario'}
                </span>
              </div>
            </div>
          </div>
        )}

        <div className="overflow-y-auto h-[calc(100vh-200px)]">
          <div className="p-2">
            <MenuSection 
              title="Principal" 
              items={menuItems} 
              isActive={isActive}
              expandedMenus={expandedMenus}
              toggleMenu={toggleMenu}
              onNavigate={handleNavigation}
            />
            
            <MenuSection 
              title="Análisis" 
              items={analysisItems} 
              isActive={isActive}
              expandedMenus={expandedMenus}
              toggleMenu={toggleMenu}
              onNavigate={handleNavigation}
            />
            
            <MenuSection 
              title="Reportes" 
              items={reportsItems} 
              isActive={isActive}
              expandedMenus={expandedMenus}
              toggleMenu={toggleMenu}
              onNavigate={handleNavigation}
            />

            <MenuSection 
              title="Sistema" 
              items={settingsItems.filter(i => !i.adminOnly || user?.role === 'admin')} 
              isActive={isActive}
              expandedMenus={expandedMenus}
              toggleMenu={toggleMenu}
              onNavigate={handleNavigation}
            />
          </div>
        </div>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between text-sm text-gray-500 mb-2">
            <span>v1.0.0</span>
            <span>© 2024 Skyfusion</span>
          </div>
          {isAuthenticated ? (
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              <span>Cerrar Sesión</span>
            </button>
          ) : (
            <button
              onClick={() => { handleNavigation('/'); setIsOpen(false); }}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-sky-500 text-white rounded-lg hover:bg-sky-600 transition-colors"
            >
              <User className="w-4 h-4" />
              <span>Iniciar Sesión</span>
            </button>
          )}
        </div>
      </div>
    </>
  );
}

function MenuSection({ title, items, isActive, expandedMenus, toggleMenu, onNavigate }) {
  return (
    <div className="mb-2">
      <button
        onClick={() => toggleMenu(title)}
        className="w-full flex items-center justify-between px-3 py-2 text-sm font-semibold text-gray-500 uppercase tracking-wide hover:text-gray-700"
      >
        {title}
        <ChevronRight className={`w-4 h-4 transform transition-transform ${expandedMenus[title] ? 'rotate-90' : ''}`} />
      </button>
      
      {expandedMenus[title] && (
        <div className="ml-2 pl-2 border-l border-gray-200">
          {items.map(item => (
            <button
              key={item.id}
              onClick={() => onNavigate(item.path)}
              className={`w-full flex items-center space-x-3 px-3 py-2 text-sm rounded-lg transition-colors ${
                isActive(item.path) 
                  ? 'bg-sky-100 text-sky-700 font-medium' 
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <item.icon className="w-5 h-5" />
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}