import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Bell, User, LogOut, Crown } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

function Header({ onSearch }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const { user, logout, isAuthenticated, isGuest } = useAuth();
  const userMenuRef = useRef(null);
  const notifMenuRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (onSearch && query.trim()) {
      onSearch(query);
    }
  };

  const handleLogout = () => {
    logout();
    setShowUserMenu(false);
    navigate('/login');
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setShowUserMenu(false);
      }
      if (notifMenuRef.current && !notifMenuRef.current.contains(event.target)) {
        setShowNotifications(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="bg-white shadow-md border-b border-gray-200 fixed top-0 left-0 right-0 z-[9998]">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-10 h-10 bg-gradient-to-br from-sky-500 to-indigo-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">SF</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-800">Skyfusion Analytics</h1>
                <p className="text-xs text-gray-500">Monitoreo Ambiental</p>
              </div>
            </div>
          </div>

          <div className="flex-1 max-w-xl mx-8">
            <form onSubmit={handleSubmit} className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Buscar ubicación o coordenadas..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-transparent"
              />
            </form>
          </div>

          <div className="flex items-center space-x-4 pr-2">
            <div className="relative" ref={notifMenuRef}>
              <button 
                onClick={() => setShowNotifications(!showNotifications)}
                className="p-2 text-gray-500 hover:text-sky-600 hover:bg-sky-50 rounded-lg transition-colors relative"
                title="Notificaciones"
              >
                <Bell className="w-5 h-5" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
              </button>
              
              {showNotifications && (
                <div className="absolute right-0 mt-2 w-72 bg-white rounded-lg shadow-2xl border border-gray-200 z-[9999]">
                  <div className="p-3 border-b border-gray-100 bg-sky-600 text-white rounded-t-lg">
                    <h3 className="font-semibold">Notificaciones</h3>
                  </div>
                  <div className="p-4 text-sm text-gray-500 text-center py-6">
                    <Bell className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                    <p>Sin notificaciones nuevas</p>
                  </div>
                </div>
              )}
            </div>
            
            <div className="relative" ref={userMenuRef}>
              <button 
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center space-x-2 p-2 text-gray-500 hover:text-sky-600 hover:bg-sky-50 rounded-lg transition-colors"
                title={isAuthenticated && user ? `Usuario: ${user.username}` : "Iniciar sesión"}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  isGuest 
                    ? 'bg-amber-500' 
                    : 'bg-sky-500'
                }`}>
                  {isGuest ? (
                    <Crown className="w-4 h-4 text-white" />
                  ) : (
                    <User className="w-4 h-4 text-white" />
                  )}
                </div>
                {isAuthenticated && user && (
                  <span className="text-sm font-medium text-gray-700 hidden lg:inline">
                    {user.username}
                  </span>
                )}
              </button>
              
              {isAuthenticated && user && showUserMenu && (
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-2xl border border-gray-200 z-[9999]">
                  <div className="p-4 border-b border-gray-100">
                    <div className="flex items-center justify-between">
                      <p className="font-semibold text-gray-900">{user.fullName || user.username}</p>
                      {isGuest && (
                        <span className="px-2 py-0.5 text-xs bg-amber-100 text-amber-700 rounded flex items-center">
                          <Crown className="w-3 h-3 mr-1" />
                          Invitado
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500">{user.email}</p>
                    {!isGuest && (
                      <span className="inline-block mt-1 px-2 py-0.5 text-xs bg-sky-100 text-sky-700 rounded">
                        {user.role || 'Usuario'}
                      </span>
                    )}
                  </div>
                  
                  {user.catchments && user.catchments.length > 0 && (
                    <div className="p-4 border-b border-gray-100">
                      <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Cuencas asignadas</p>
                      <div className="flex flex-wrap gap-1">
                        {user.catchments.map(c => (
                          <span key={c} className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">
                            {c}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center px-4 py-3 text-red-600 hover:bg-red-50 transition-colors"
                  >
                    <LogOut className="w-4 h-4 mr-2" />
                    Cerrar Sesión
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;