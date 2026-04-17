import axios from 'axios';

const API_BASE_URL = 'http://localhost:3001/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
});

api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response) {
      const { status, data } = error.response;
      
      if (status === 401) {
        const isGuest = localStorage.getItem('isGuest') === 'true';
        const guestExpiry = localStorage.getItem('guestExpiresAt');
        
        if (isGuest && guestExpiry && new Date(guestExpiry) > new Date()) {
          console.log('Sesión de invitado válida, manteniendo sesión...');
          const errorObj = new Error(data?.error || data?.message || 'Sesión válida');
          errorObj.skipAuthRedirect = true;
          return Promise.reject(errorObj);
        }
        
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('permissions');
        localStorage.removeItem('isGuest');
        localStorage.removeItem('guestExpiresAt');
        
        if (!error.config?.skipAuthRedirect) {
          window.location.href = '/login?expired=true';
        }
      }
      
      const errorMessage = data?.error || data?.message || 'Error en la solicitud';
      return Promise.reject(new Error(errorMessage));
    }
    
    if (error.request) {
      return Promise.reject(new Error('No se pudo conectar con el servidor'));
    }
    
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: async (email, password) => {
    return await api.post('/auth/login', { email, password });
  },
  
  register: async (userData) => {
    return await api.post('/auth/register', userData);
  },
  
  loginAsGuest: async () => {
    return await api.post('/auth/guest');
  },
  
  getMe: async () => {
    return await api.get('/auth/me');
  },
  
  updateProfile: async (data) => {
    return await api.put('/auth/profile', data);
  },
  
  changePassword: async (data) => {
    return await api.post('/auth/change-password', data);
  }
};

export const fetchMetrics = async (catchmentId) => {
  try {
    const data = await api.get(`/demo/metrics/${catchmentId}`);
    return data;
  } catch (error) {
    console.error('Error fetching metrics:', error);
    return {
      catchment_id: catchmentId,
      metrics: {
        caudal: { value: 4.2, unit: 'm³/s', status: 'normal' },
        precipitacion: { value: 12, unit: 'mm', status: 'normal' },
        temperatura: { value: 24, unit: '°C', status: 'normal' },
        humedad: { value: 78, unit: '%', status: 'normal' },
        ndvi: { value: 0.65, status: 'healthy' },
        ndwi: { value: 0.42, status: 'stable' }
      }
    };
  }
};

export const fetchAlerts = async (catchmentId) => {
  try {
    const data = await api.get(`/demo/alerts/${catchmentId}`);
    return data.alerts || [];
  } catch (error) {
    console.error('Error fetching alerts:', error);
    return [];
  }
};

export const fetchPredictions = async (catchmentId, horizon = 7) => {
  try {
    const data = await api.get(`/demo/predictions/${catchmentId}`, { horizon });
    return data.predictions || [];
  } catch (error) {
    console.error('Error fetching predictions:', error);
    return [];
  }
};

export const fetchNarrative = async (catchmentId) => {
  try {
    const data = await api.get(`/demo/narrative/${catchmentId}`);
    return data;
  } catch (error) {
    console.error('Error fetching narrative:', error);
    return null;
  }
};

export const fetchCatchments = async () => {
  try {
    const data = await api.get('/demo/catchments');
    return data.catchments || [];
  } catch (error) {
    console.error('Error fetching catchments:', error);
    return [];
  }
};

export const fetchStations = async (catchmentId) => {
  try {
    const data = await api.get(`/demo/stations/${catchmentId}`);
    return data || [];
  } catch (error) {
    console.error('Error fetching stations:', error);
    return [];
  }
};

export const fetchIndexData = async (indexName, catchmentId, date) => {
  try {
    const data = await api.get(`/demo/indices/${indexName}`, {
      params: { catchment: catchmentId, date }
    });
    return data;
  } catch (error) {
    console.error(`Error fetching ${indexName}:`, error);
    throw error;
  }
};

export const exportReport = async (type, params) => {
  try {
    const data = await api.post(`/reports/${type}`, params);
    return data;
  } catch (error) {
    console.error('Error exporting report:', error);
    throw error;
  }
};

export default api;