import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogOut, Loader } from 'lucide-react';

function LogoutPage() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  React.useEffect(() => {
    const performLogout = async () => {
      await logout();
      setTimeout(() => {
        navigate('/login');
      }, 1000);
    };
    performLogout();
  }, [logout, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-sky-50 to-blue-50">
      <div className="text-center">
        <Loader className="w-12 h-12 text-sky-600 animate-spin mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-700">Cerrando sesión...</h2>
        <p className="text-gray-500 mt-2">Gracias por usar Skyfusion Analytics</p>
      </div>
    </div>
  );
}

export default LogoutPage;
