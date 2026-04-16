import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  LogIn, 
  UserPlus, 
  User, 
  Mail, 
  Lock, 
  AlertCircle, 
  CheckCircle, 
  Loader,
  Crown,
  Shield,
  MapPin,
  Bell,
  BarChart3,
  Zap,
  Globe,
  Droplets,
  CloudRain,
  Thermometer,
  Activity
} from 'lucide-react';

function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, register, loginAsGuest, loading } = useAuth();
  
  const [mode, setMode] = useState('login');
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    username: '',
    fullName: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get('expired') === 'true') {
      setError('Tu sesión ha expirado. Por favor, inicia sesión nuevamente.');
    }
  }, [location]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError('');
    setSuccess('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setIsSubmitting(true);

    if (mode === 'register') {
      if (formData.password !== formData.confirmPassword) {
        setError('Las contraseñas no coinciden');
        setIsSubmitting(false);
        return;
      }
      if (formData.password.length < 6) {
        setError('La contraseña debe tener al menos 6 caracteres');
        setIsSubmitting(false);
        return;
      }
      if (!formData.username || formData.username.length < 3) {
        setError('El nombre de usuario debe tener al menos 3 caracteres');
        setIsSubmitting(false);
        return;
      }
    }
    
    if (!formData.email || !formData.password) {
      setError('Por favor, completa todos los campos');
      setIsSubmitting(false);
      return;
    }

    try {
      if (mode === 'login') {
        await login(formData.email, formData.password);
        setSuccess('¡Bienvenido de vuelta!');
      } else {
        await register({
          email: formData.email,
          password: formData.password,
          username: formData.username,
          fullName: formData.fullName
        });
        setSuccess('¡Cuenta creada exitosamente!');
      }
      setTimeout(() => navigate('/dashboard'), 1200);
    } catch (err) {
      setError(err.message || 'Ocurrió un error. Verifica tus credenciales.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGuestLogin = async () => {
    setError('');
    setSuccess('');
    setIsSubmitting(true);
    try {
      await loginAsGuest();
      setSuccess('Sesión de invitado creada. Cargando dashboard...');
      setTimeout(() => navigate('/dashboard'), 1200);
    } catch (err) {
      setError(err.message || 'Error al crear sesión de invitado');
    } finally {
      setIsSubmitting(false);
    }
  };

  const switchMode = () => {
    setMode(mode === 'login' ? 'register' : 'login');
    setError('');
    setSuccess('');
    setFormData({
      email: '',
      password: '',
      confirmPassword: '',
      username: '',
      fullName: ''
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-600 via-blue-700 to-indigo-900 flex items-center justify-center p-4">
      <div className="w-full max-w-7xl grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
        
        {/* Lado izquierdo - Información de la plataforma */}
        <div className="hidden lg:block space-y-8 text-white">
          <div className="space-y-6">
            <div className="flex items-center space-x-4">
              <div className="w-20 h-20 bg-gradient-to-br from-sky-400 to-blue-500 rounded-2xl flex items-center justify-center shadow-2xl">
                <Globe className="w-12 h-12" />
              </div>
              <div>
                <h1 className="text-6xl font-bold tracking-tight">Skyfusion</h1>
                <p className="text-3xl font-light text-sky-200">Analytics Platform</p>
              </div>
            </div>
            <p className="text-xl text-sky-100 leading-relaxed max-w-lg">
              Plataforma SaaS de análisis multitemporal para monitoreo y predicción ambiental en cuencas hidrográficas
            </p>
          </div>

          <div className="grid grid-cols-2 gap-5">
            <div className="bg-white/10 backdrop-blur-md p-5 rounded-2xl border border-white/20 hover:bg-white/15 transition-all">
              <MapPin className="w-10 h-10 mb-3 text-sky-300" />
              <h3 className="font-bold text-lg">Monitoreo de Cuencas</h3>
              <p className="text-sm text-sky-100 mt-2">Visualiza múltiples cuencas hidrográficas en tiempo real</p>
            </div>
            <div className="bg-white/10 backdrop-blur-md p-5 rounded-2xl border border-white/20 hover:bg-white/15 transition-all">
              <BarChart3 className="w-10 h-10 mb-3 text-blue-300" />
              <h3 className="font-bold text-lg">Análisis NDVI/NDWI</h3>
              <p className="text-sm text-sky-100 mt-2">Métricas avanzadas de vegetación y agua</p>
            </div>
            <div className="bg-white/10 backdrop-blur-md p-5 rounded-2xl border border-white/20 hover:bg-white/15 transition-all">
              <Bell className="w-10 h-10 mb-3 text-amber-300" />
              <h3 className="font-bold text-lg">Alertas Inteligentes</h3>
              <p className="text-sm text-sky-100 mt-2">Predicción de inundaciones y sequías</p>
            </div>
            <div className="bg-white/10 backdrop-blur-md p-5 rounded-2xl border border-white/20 hover:bg-white/15 transition-all">
              <Zap className="w-10 h-10 mb-3 text-emerald-300" />
              <h3 className="font-bold text-lg">IA Predictiva</h3>
              <p className="text-sm text-sky-100 mt-2">Machine Learning para análisis futuro</p>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-md p-6 rounded-2xl border border-white/20">
            <div className="flex items-center space-x-3 mb-4">
              <Shield className="w-8 h-8 text-emerald-400" />
              <h3 className="text-xl font-bold">Seguridad y Acceso</h3>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="flex items-center text-sm text-sky-100">
                <CheckCircle className="w-4 h-4 mr-2 text-green-400" />
                Tokens JWT encriptados
              </div>
              <div className="flex items-center text-sm text-sky-100">
                <CheckCircle className="w-4 h-4 mr-2 text-green-400" />
                Permisos granulares
              </div>
              <div className="flex items-center text-sm text-sky-100">
                <CheckCircle className="w-4 h-4 mr-2 text-green-400" />
                Sesiones 24h
              </div>
              <div className="flex items-center text-sm text-sky-100">
                <CheckCircle className="w-4 h-4 mr-2 text-green-400" />
                Acceso invitado
              </div>
            </div>
          </div>

          <div className="flex items-center justify-center space-x-8 text-sky-200">
            <div className="flex items-center">
              <Droplets className="w-5 h-5 mr-2" />
              <span className="text-sm">Caudal</span>
            </div>
            <div className="flex items-center">
              <CloudRain className="w-5 h-5 mr-2" />
              <span className="text-sm">Precipitación</span>
            </div>
            <div className="flex items-center">
              <Thermometer className="w-5 h-5 mr-2" />
              <span className="text-sm">Temperatura</span>
            </div>
            <div className="flex items-center">
              <Activity className="w-5 h-5 mr-2" />
              <span className="text-sm">Análisis</span>
            </div>
          </div>
        </div>

        {/* Lado derecho - Formulario */}
        <div className="w-full max-w-md mx-auto">
          <div className="bg-white rounded-3xl shadow-2xl overflow-hidden">
            <div className="bg-gradient-to-r from-sky-600 via-blue-600 to-indigo-700 p-8 text-center relative overflow-hidden">
              <div className="absolute inset-0 opacity-10">
                <div className="absolute top-0 left-0 w-32 h-32 bg-white rounded-full -translate-x-1/2 -translate-y-1/2"></div>
                <div className="absolute bottom-0 right-0 w-40 h-40 bg-white rounded-full translate-x-1/2 translate-y-1/2"></div>
              </div>
              <div className="relative z-10">
                <div className="w-20 h-20 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center mx-auto mb-4">
                  <Crown className="w-10 h-10 text-white" />
                </div>
                <h2 className="text-3xl font-bold text-white">
                  {mode === 'login' ? 'Bienvenido de Vuelta' : 'Únete a Nosotros'}
                </h2>
                <p className="text-sky-100 mt-2 text-lg">
                  {mode === 'login' 
                    ? 'Accede a tu cuenta Skyfusion' 
                    : 'Crea tu cuenta gratuita'}
                </p>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="p-8 space-y-5">
              {error && (
                <div className="flex items-start p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
                  <AlertCircle className="w-5 h-5 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-sm">{error}</span>
                </div>
              )}

              {success && (
                <div className="flex items-start p-4 bg-green-50 border border-green-200 rounded-xl text-green-700">
                  <CheckCircle className="w-5 h-5 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-sm">{success}</span>
                </div>
              )}

              {mode === 'register' && (
                <>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Nombre de usuario
                    </label>
                    <div className="relative">
                      <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                      <input
                        type="text"
                        name="username"
                        value={formData.username}
                        onChange={handleChange}
                        required
                        className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition-all"
                        placeholder="usuario123"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Nombre completo <span className="text-gray-400 font-normal">(opcional)</span>
                    </label>
                    <input
                      type="text"
                      name="fullName"
                      value={formData.fullName}
                      onChange={handleChange}
                      className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition-all"
                      placeholder="Juan Pérez"
                    />
                  </div>
                </>
              )}

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Correo electrónico
                </label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition-all"
                    placeholder="correo@ejemplo.com"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Contraseña
                </label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition-all"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              {mode === 'register' && (
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Confirmar contraseña
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="password"
                      name="confirmPassword"
                      value={formData.confirmPassword}
                      onChange={handleChange}
                      required
                      className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition-all"
                      placeholder="••••••••"
                    />
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex items-center justify-center py-4 bg-gradient-to-r from-sky-600 to-blue-600 text-white font-bold rounded-xl hover:from-sky-700 hover:to-blue-700 transition-all disabled:opacity-50 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              >
                {isSubmitting ? (
                  <Loader className="w-6 h-6 animate-spin" />
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

              <div className="text-center">
                <button
                  type="button"
                  onClick={switchMode}
                  className="text-sky-600 hover:text-sky-700 hover:underline font-medium transition-colors"
                >
                  {mode === 'login' 
                    ? '¿No tienes cuenta? Regístrate aquí' 
                    : '¿Ya tienes cuenta? Inicia sesión'}
                </button>
              </div>
            </form>

            <div className="px-8 pb-8">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-200"></div>
                </div>
                <div className="relative flex justify-center">
                  <span className="px-4 bg-white text-sm text-gray-500 font-medium">o</span>
                </div>
              </div>

              <button
                onClick={handleGuestLogin}
                disabled={isSubmitting}
                className="w-full mt-6 flex items-center justify-center py-4 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold rounded-xl transition-all disabled:opacity-50"
              >
                {isSubmitting ? (
                  <Loader className="w-6 h-6 animate-spin mr-2" />
                ) : (
                  <User className="w-5 h-5 mr-2" />
                )}
                Entrar como Invitado
              </button>

              <div className="mt-6 p-4 bg-sky-50 rounded-xl border border-sky-100">
                <p className="text-xs text-gray-600 text-center">
                  <span className="font-semibold text-sky-700">Modo Invitado:</span> Acceso por 24 horas a dashboard, mapas y análisis.
                  <br />
                  <span className="text-sky-600 font-medium">No requiere registro.</span>
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 text-center text-sm text-white/70">
            <p>Al continuar, aceptas nuestros{' '}
              <a href="#" className="underline hover:text-white transition-colors">Términos</a>
              {' '}y{' '}
              <a href="#" className="underline hover:text-white transition-colors">Política de Privacidad</a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
