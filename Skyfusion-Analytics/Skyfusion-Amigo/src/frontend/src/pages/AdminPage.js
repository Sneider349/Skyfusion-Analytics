import React, { useState } from 'react';

const roles = [
  { id: 1, nombre: 'Administrador', descripcion: 'Acceso completo al sistema', permisos: 100 },
  { id: 2, nombre: 'Ingeniero', descripcion: 'Gestión de proyectos y análisis', permisos: 70 },
  { id: 3, nombre: 'Lector', descripcion: 'Solo visualización de datos', permisos: 30 }
];

const usuariosDemo = [
  { id: 1, nombre: 'Carlos Martínez', email: 'carlos.m@uniminuto.edu', rol: 'Administrador', estado: 'activo', ultimo_acceso: '2026-04-02' },
  { id: 2, nombre: 'Ana Sofía Pérez', email: 'ana.perez@crq.gov.co', rol: 'Ingeniero', estado: 'activo', ultimo_acceso: '2026-04-01' },
  { id: 3, nombre: 'José Roberto Silva', email: 'j.silva@ibague.gov.co', rol: 'Ingeniero', estado: 'inactivo', ultimo_acceso: '2026-03-28' },
  { id: 4, nombre: 'María Elena Gómez', email: 'm.gomez@gobtolima.gov.co', rol: 'Lector', estado: 'activo', ultimo_acceso: '2026-04-02' },
  { id: 5, nombre: 'Fernando López', email: 'f.lopez@car.gov.co', rol: 'Lector', estado: 'activo', ultimo_acceso: '2026-03-30' }
];

function AdminPage() {
  const [activeTab, setActiveTab] = useState('usuarios');
  const [usuarios, setUsuarios] = useState(usuariosDemo);
  const [showModal, setShowModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);

  const handleEditUser = (usuario) => {
    setSelectedUser(usuario);
    setShowModal(true);
  };

  const handleDeleteUser = (id) => {
    if (confirm('¿Estás seguro de eliminar este usuario?')) {
      setUsuarios(usuarios.filter(u => u.id !== id));
    }
  };

  const getEstadoColor = (estado) => {
    return estado === 'activo' 
      ? 'bg-green-500/20 text-green-400' 
      : 'bg-red-500/20 text-red-400';
  };

  const getRolColor = (rol) => {
    switch (rol) {
      case 'Administrador': return 'bg-purple-500/20 text-purple-400';
      case 'Ingeniero': return 'bg-blue-500/20 text-blue-400';
      default: return 'bg-gray-500/20 text-gray-400';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">
            Administración
          </h1>
          <p className="text-slate-400">
            Gestión de usuarios, roles y configuración del sistema
          </p>
        </div>

        <div className="flex space-x-1 mb-6 bg-slate-800/50 p-1 rounded-lg w-fit">
          {['usuarios', 'roles', 'configuracion'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all capitalize ${
                activeTab === tab
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-white/10'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {activeTab === 'usuarios' && (
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 overflow-hidden">
            <div className="p-4 border-b border-slate-700 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Usuarios del Sistema</h2>
              <button
                onClick={() => { setSelectedUser(null); setShowModal(true); }}
                className="flex items-center space-x-2 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm rounded-lg transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span>Nuevo Usuario</span>
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-700/50">
                  <tr>
                    <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-4 py-3">Usuario</th>
                    <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-4 py-3">Email</th>
                    <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-4 py-3">Rol</th>
                    <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-4 py-3">Estado</th>
                    <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-4 py-3">Último Acceso</th>
                    <th className="text-right text-xs font-medium text-slate-400 uppercase tracking-wider px-4 py-3">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700">
                  {usuarios.map(usuario => (
                    <tr key={usuario.id} className="hover:bg-slate-700/30 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-indigo-500/30 rounded-full flex items-center justify-center">
                            <span className="text-sm text-indigo-300 font-medium">
                              {usuario.nombre.charAt(0)}
                            </span>
                          </div>
                          <span className="text-white font-medium">{usuario.nombre}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-slate-400 text-sm">{usuario.email}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRolColor(usuario.rol)}`}>
                          {usuario.rol}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getEstadoColor(usuario.estado)}`}>
                          {usuario.estado}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-400 text-sm">{usuario.ultimo_acceso}</td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={() => handleEditUser(usuario)}
                            className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
                          >
                            <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          </button>
                          <button
                            onClick={() => handleDeleteUser(usuario.id)}
                            className="p-1.5 hover:bg-red-500/20 rounded-lg transition-colors"
                          >
                            <svg className="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'roles' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {roles.map(rol => (
              <div key={rol.id} className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">{rol.nombre}</h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    rol.id === 1 ? 'bg-purple-500/20 text-purple-400' :
                    rol.id === 2 ? 'bg-blue-500/20 text-blue-400' :
                    'bg-gray-500/20 text-gray-400'
                  }`}>
                    Nivel {rol.permisos}%
                  </span>
                </div>
                <p className="text-slate-400 text-sm mb-4">{rol.descripcion}</p>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-500">Gestión de proyectos</span>
                    <span className={rol.permisos >= 70 ? 'text-green-400' : 'text-red-400'}>
                      {rol.permisos >= 70 ? '✓' : '✗'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-500">Análisis IA</span>
                    <span className={rol.permisos >= 70 ? 'text-green-400' : 'text-red-400'}>
                      {rol.permisos >= 70 ? '✓' : '✗'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-500">Ver estadísticas</span>
                    <span className={rol.permisos >= 30 ? 'text-green-400' : 'text-red-400'}>
                      {rol.permisos >= 30 ? '✓' : '✗'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-500">Gestión de usuarios</span>
                    <span className={rol.permisos >= 100 ? 'text-green-400' : 'text-red-400'}>
                      {rol.permisos >= 100 ? '✓' : '✗'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'configuracion' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-4">Configuración General</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-white">Modo Demo</p>
                    <p className="text-slate-400 text-sm">Activar datos de ejemplo</p>
                  </div>
                  <button className="w-12 h-6 bg-indigo-600 rounded-full relative">
                    <span className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full"></span>
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-white">Notificaciones Push</p>
                    <p className="text-slate-400 text-sm">Recibir alertas en tiempo real</p>
                  </div>
                  <button className="w-12 h-6 bg-indigo-600 rounded-full relative">
                    <span className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full"></span>
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-white">IA Activa</p>
                    <p className="text-slate-400 text-sm">Análisis automático con GPT-4</p>
                  </div>
                  <button className="w-12 h-6 bg-indigo-600 rounded-full relative">
                    <span className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full"></span>
                  </button>
                </div>
              </div>
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-4">Información del Sistema</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">Versión</span>
                  <span className="text-white">1.0.0</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Node.js</span>
                  <span className="text-white">v22.18.0</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Base de datos</span>
                  <span className="text-yellow-400">Demo Mode</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Última actualización</span>
                  <span className="text-white">2026-04-02</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-2xl max-w-md w-full">
            <div className="p-6 border-b border-slate-700">
              <h2 className="text-xl font-semibold text-white">
                {selectedUser ? 'Editar Usuario' : 'Nuevo Usuario'}
              </h2>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Nombre</label>
                <input
                  type="text"
                  defaultValue={selectedUser?.nombre}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Email</label>
                <input
                  type="email"
                  defaultValue={selectedUser?.email}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Rol</label>
                <select className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-indigo-500">
                  <option>Administrador</option>
                  <option>Ingeniero</option>
                  <option>Lector</option>
                </select>
              </div>
            </div>
            <div className="p-6 border-t border-slate-700 flex justify-end space-x-3">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                Cancelar
              </button>
              <button className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors">
                Guardar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminPage;
