import React, { useState, useCallback } from 'react';
import { useAuth } from '../hooks/useNotifications';
import { LogIn, UserPlus, Mail, Lock, User, Building, Key, AlertCircle, CheckCircle, Loader } from 'lucide-react';

function AuthModal({ isOpen, onClose, initialMode = 'login' }) {
    const { login, register, loading, error: authError, isAuthenticated } = useAuth();
    const [mode, setMode] = useState(initialMode);
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        confirmPassword: '',
        username: '',
        fullName: '',
        catchments: []
    });
    const [formError, setFormError] = useState('');
    const [success, setSuccess] = useState('');

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
        setFormError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setFormError('');
        setSuccess('');

        if (mode === 'register') {
            if (formData.password !== formData.confirmPassword) {
                setFormError('Las contraseñas no coinciden');
                return;
            }
            if (formData.password.length < 6) {
                setFormError('La contraseña debe tener al menos 6 caracteres');
                return;
            }
        }

        try {
            if (mode === 'login') {
                await login(formData.email, formData.password);
                setSuccess('Iniciando sesión...');
            } else {
                await register({
                    email: formData.email,
                    password: formData.password,
                    username: formData.username,
                    fullName: formData.fullName
                });
                setSuccess('Cuenta creada exitosamente');
            }
            
            setTimeout(() => {
                onClose();
                setFormData({
                    email: '',
                    password: '',
                    confirmPassword: '',
                    username: '',
                    fullName: '',
                    catchments: []
                });
            }, 1000);
        } catch (err) {
            setFormError(err.message || 'Error en la operación');
        }
    };

    const switchMode = () => {
        setMode(mode === 'login' ? 'register' : 'login');
        setFormError('');
        setSuccess('');
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[10002] flex items-center justify-center">
            <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
            
            <div className="relative w-full max-w-md bg-white rounded-xl shadow-2xl overflow-hidden">
                <div className="bg-gradient-to-r from-sky-600 to-sky-700 p-6 text-center">
                    <h2 className="text-2xl font-bold text-white">
                        {mode === 'login' ? 'Skyfusion Analytics' : 'Crear Cuenta'}
                    </h2>
                    <p className="text-sky-100 mt-1">
                        {mode === 'login' ? 'Ingresa a tu cuenta' : 'Regístrate para comenzar'}
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    {authError && (
                        <div className="flex items-center p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                            <AlertCircle className="w-5 h-5 mr-2" />
                            {authError}
                        </div>
                    )}

                    {formError && (
                        <div className="flex items-center p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                            <AlertCircle className="w-5 h-5 mr-2" />
                            {formError}
                        </div>
                    )}

                    {success && (
                        <div className="flex items-center p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
                            <CheckCircle className="w-5 h-5 mr-2" />
                            {success}
                        </div>
                    )}

                    {mode === 'register' && (
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Nombre de usuario
                            </label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                <input
                                    type="text"
                                    name="username"
                                    value={formData.username}
                                    onChange={handleChange}
                                    required
                                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                                    placeholder="usuario123"
                                />
                            </div>
                        </div>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Correo electrónico
                        </label>
                        <div className="relative">
                            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                            <input
                                type="email"
                                name="email"
                                value={formData.email}
                                onChange={handleChange}
                                required
                                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                                placeholder="correo@ejemplo.com"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Contraseña
                        </label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                            <input
                                type="password"
                                name="password"
                                value={formData.password}
                                onChange={handleChange}
                                required
                                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                                placeholder="••••••••"
                            />
                        </div>
                    </div>

                    {mode === 'register' && (
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Confirmar contraseña
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                <input
                                    type="password"
                                    name="confirmPassword"
                                    value={formData.confirmPassword}
                                    onChange={handleChange}
                                    required
                                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                                    placeholder="••••••••"
                                />
                            </div>
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full flex items-center justify-center py-3 bg-gradient-to-r from-sky-600 to-sky-700 text-white font-semibold rounded-lg hover:from-sky-700 hover:to-sky-800 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? (
                            <Loader className="w-5 h-5 animate-spin" />
                        ) : mode === 'login' ? (
                            <>
                                <LogIn className="w-5 h-5 mr-2" />
                                Iniciar Sesión
                            </>
                        ) : (
                            <>
                                <UserPlus className="w-5 h-5 mr-2" />
                                Crear Cuenta
                            </>
                        )}
                    </button>

                    <div className="text-center pt-2">
                        <button
                            type="button"
                            onClick={switchMode}
                            className="text-sm text-sky-600 hover:text-sky-700 hover:underline"
                        >
                            {mode === 'login' 
                                ? '¿No tienes cuenta? Regístrate aquí' 
                                : '¿Ya tienes cuenta? Inicia sesión'}
                        </button>
                    </div>
                </form>

                <div className="px-6 pb-6">
                    <button
                        onClick={onClose}
                        className="w-full py-2 text-gray-500 hover:text-gray-700 text-sm"
                    >
                        Continuar como invitado
                    </button>
                </div>
            </div>
        </div>
    );
}

function UserMenu({ user, onLogout, onOpenAuth }) {
    const [showMenu, setShowMenu] = useState(false);

    if (!user) {
        return (
            <button
                onClick={onOpenAuth}
                className="flex items-center px-3 py-2 text-sm bg-sky-600 text-white hover:bg-sky-700 rounded-lg transition-colors"
            >
                <LogIn className="w-4 h-4 mr-2" />
                Ingresar
            </button>
        );
    }

    return (
        <div className="relative">
            <button
                onClick={() => setShowMenu(!showMenu)}
                className="flex items-center space-x-2 px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
                <div className="w-8 h-8 bg-sky-500 rounded-full flex items-center justify-center text-white font-semibold">
                    {user.username?.charAt(0).toUpperCase() || 'U'}
                </div>
                <span className="text-sm font-medium">{user.username}</span>
            </button>

            {showMenu && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50">
                    <div className="px-4 py-2 border-b border-gray-100">
                        <p className="font-medium text-gray-900">{user.fullName || user.username}</p>
                        <p className="text-sm text-gray-500">{user.email}</p>
                        <span className="inline-block mt-1 px-2 py-0.5 text-xs bg-sky-100 text-sky-700 rounded">
                            {user.role || 'Usuario'}
                        </span>
                    </div>
                    
                    {user.catchments && user.catchments.length > 0 && (
                        <div className="px-4 py-2 border-b border-gray-100">
                            <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Cuencas</p>
                            <div className="flex flex-wrap gap-1">
                                {user.catchments.map(c => (
                                    <span key={c} className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                                        {c}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    <button
                        onClick={() => {
                            setShowMenu(false);
                            onLogout();
                        }}
                        className="w-full flex items-center px-4 py-2 text-red-600 hover:bg-red-50 transition-colors"
                    >
                        <Lock className="w-4 h-4 mr-2" />
                        Cerrar Sesión
                    </button>
                </div>
            )}
        </div>
    );
}

export { AuthModal, UserMenu };
export default AuthModal;