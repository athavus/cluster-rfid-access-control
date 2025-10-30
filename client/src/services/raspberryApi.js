import axios from 'axios';

// Configuração base da API
const api = axios.create({
  baseURL: 'http://192.168.130.9:8000', // Endereço do FastAPI
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Interceptor para tratamento de erros
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('Erro na API:', error.response.data);
    } else if (error.request) {
      console.error('Erro de rede:', error.request);
    }
    return Promise.reject(error);
  }
);

// ============= SERVIÇOS DE LED CONTROL =============
export const ledService = {
  // Controlar LED (genérico)
  controlLED: async (raspberryId, ledType, status) => {
    const response = await api.post('/api/led/control', {
      raspberry_id: raspberryId,
      led_type: ledType,
      status: status
    });
    return response.data;
  },

  // Ligar LED específico
  turnOn: async (ledType, raspberryId = 1) => {
    const response = await api.post(`/api/led/${ledType}/on`, null, {
      params: { raspberry_id: raspberryId }
    });
    return response.data;
  },

  // Desligar LED específico
  turnOff: async (ledType, raspberryId = 1) => {
    const response = await api.post(`/api/led/${ledType}/off`, null, {
      params: { raspberry_id: raspberryId }
    });
    return response.data;
  },

  // Buscar status dos LEDs
  getStatus: async (raspberryId = 1) => {
    const response = await api.get('/api/led/status', {
      params: { raspberry_id: raspberryId }
    });
    return response.data; // Deve retornar o status dos LEDs internos e externos
  },

  // Buscar histórico de ações dos LEDs
  getHistory: async (raspberryId = null, ledType = null, limit = 50) => {
    const params = { limit };
    if (raspberryId !== null) params.raspberry_id = raspberryId;
    if (ledType !== null) params.led_type = ledType;

    const response = await api.get('/api/led/history', { params });
    // mapeando o datetime para o formato desejado, se necessário
    return response.data;
  }
};

// ============= SERVIÇOS DE STATUS DOS DISPOSITIVOS =============
export const deviceService = {
  // Buscar status de todos os dispositivos
  getAllDevices: async () => {
    const response = await api.get('/api/devices/status');
    // Espera-se que raspberry_id seja string, conforme modelo!
    return response.data;
  },

  // Buscar status de um dispositivo específico (por id string)
  getDevice: async (raspberryId) => {
    const response = await api.get(`/api/devices/${raspberryId}/status`);
    return response.data;
  }
};

// ============= SERVIÇOS DE DADOS EM TEMPO REAL =============
export const realtimeService = {
  // Buscar dados em tempo real
  getData: async (limit = 50) => {
    const response = await api.get('/api/data/realtime', {
      params: { limit }
    });
    return response.data;
  },

  // Enviar dados manualmente (para testes/debug)
  postData: async (data) => {
    const response = await api.post('/api/data', data);
    return response.data;
  }
};

// ============= SERVIÇOS DE HEALTH CHECK =============
export const healthService = {
  // Root endpoint (info da API)
  getRoot: async () => {
    const response = await api.get('/');
    return response.data;
  },

  // Health check completo
  checkHealth: async () => {
    const response = await api.get('/health');
    return response.data;
  },

  // Estatísticas
  getStats: async () => {
    const response = await api.get('/api/stats');
    return response.data;
  }
};

export default api;

