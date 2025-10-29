<template>
  <div class="raspberry-control">
    <h1>Raspberry Pi LED Control</h1>

    <!-- Health Status -->
    <div class="health-section">
      <h2>System Health</h2>
      <button @click="fetchHealth">Refresh Health</button>
      <div v-if="health" class="health-info">
        <div class="health-item">
          <strong>API:</strong> {{ health.api }}
        </div>
        <div class="health-item">
          <strong>Database:</strong> {{ health.database }}
        </div>
        <div class="health-item">
          <strong>GPIO:</strong> {{ health.gpio }}
        </div>
        <div class="health-item">
          <strong>Devices:</strong> {{ health.registered_devices }}
        </div>
      </div>
    </div>

    <!-- LED Controls -->
    <div class="led-section">
      <h2>LED Control Panel</h2>
      
      <div class="led-status" v-if="ledStatus">
        <div class="status-card">
          <h3>Internal LED</h3>
          <div :class="['led-indicator', ledStatus.led_internal]">
            {{ ledStatus.led_internal }}
          </div>
        </div>
        <div class="status-card">
          <h3>External LED</h3>
          <div :class="['led-indicator', ledStatus.led_external]">
            {{ ledStatus.led_external }}
          </div>
        </div>
      </div>

      <div class="controls">
        <div class="control-group">
          <h3>Internal LED</h3>
          <button @click="toggleLED('internal', 'ON')" class="btn-on">
            💡 Turn ON
          </button>
          <button @click="toggleLED('internal', 'OFF')" class="btn-off">
            ⚫ Turn OFF
          </button>
        </div>

        <div class="control-group">
          <h3>External LED</h3>
          <button @click="toggleLED('external', 'ON')" class="btn-on">
            💡 Turn ON
          </button>
          <button @click="toggleLED('external', 'OFF')" class="btn-off">
            ⚫ Turn OFF
          </button>
        </div>
      </div>

      <button @click="fetchLEDStatus" class="btn-refresh">
        Refresh Status
      </button>
    </div>

    <!-- Statistics -->
    <div class="stats-section">
      <h2>Statistics</h2>
      <button @click="fetchStats">Load Stats</button>
      <div v-if="stats" class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">{{ stats.total_devices }}</div>
          <div class="stat-label">Total Devices</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.total_led_actions }}</div>
          <div class="stat-label">Total LED Actions</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.led_actions_24h }}</div>
          <div class="stat-label">Actions (24h)</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.realtime_messages }}</div>
          <div class="stat-label">RT Messages</div>
        </div>
      </div>
    </div>

    <!-- LED History -->
    <div class="history-section">
      <h2>LED History</h2>
      <button @click="fetchHistory">Load History</button>
      <div v-if="history.length > 0" class="history-list">
        <div v-for="item in history" :key="item.id" class="history-item">
          <span class="history-time">{{ formatDate(item.timestamp) }}</span>
          <span class="history-device">Pi #{{ item.raspberry_id }}</span>
          <span class="history-led">{{ item.led_type }}</span>
          <span :class="['history-action', item.action]">{{ item.action }}</span>
        </div>
      </div>
    </div>

    <!-- Loading & Error States -->
    <div v-if="loading" class="loading">Loading...</div>
    <div v-if="error" class="error">
      ❌ {{ error }}
      <button @click="error = null" style="margin-left: 10px; padding: 5px 10px;">✕</button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { ledService, healthService } from '@/services/raspberryApi';

export default {
  name: 'RaspberryControl',
  setup() {
    const loading = ref(false);
    const error = ref(null);
    const health = ref(null);
    const ledStatus = ref(null);
    const stats = ref(null);
    const history = ref([]);

    // Controlar LED
    const toggleLED = async (ledType, status) => {
      loading.value = true;
      error.value = null;
      try {
        const result = await ledService.controlLED(1, ledType, status);
        console.log('LED controlado:', result);
        await fetchLEDStatus(); // Atualizar status após controlar
      } catch (err) {
        error.value = err.response?.data?.detail || err.message;
        console.error('❌ Erro ao controlar LED:', err);
      } finally {
        loading.value = false;
      }
    };

    // Buscar status dos LEDs
    const fetchLEDStatus = async () => {
      try {
        ledStatus.value = await ledService.getStatus(1);
        console.log('Status LED atualizado:', ledStatus.value);
      } catch (err) {
        console.error('❌ Erro ao buscar status:', err);
      }
    };

    // Buscar health
    const fetchHealth = async () => {
      loading.value = true;
      error.value = null;
      try {
        health.value = await healthService.checkHealth();
        console.log('Health check:', health.value);
      } catch (err) {
        error.value = err.message;
        console.error('❌ Erro no health check:', err);
      } finally {
        loading.value = false;
      }
    };

    // Buscar estatísticas
    const fetchStats = async () => {
      loading.value = true;
      error.value = null;
      try {
        stats.value = await healthService.getStats();
        console.log('Stats carregadas:', stats.value);
      } catch (err) {
        error.value = err.message;
        console.error('❌ Erro ao carregar stats:', err);
      } finally {
        loading.value = false;
      }
    };

    // Buscar histórico
    const fetchHistory = async () => {
      loading.value = true;
      error.value = null;
      try {
        history.value = await ledService.getHistory(null, null, 20);
        console.log('Histórico carregado:', history.value.length, 'itens');
      } catch (err) {
        error.value = err.message;
        console.error('❌ Erro ao carregar histórico:', err);
      } finally {
        loading.value = false;
      }
    };

    // Formatar data
    const formatDate = (dateString) => {
      const date = new Date(dateString);
      return date.toLocaleString('pt-BR');
    };

    // Carregar dados iniciais
    onMounted(() => {
      console.log('Componente montado - Carregando dados da API...');
      fetchHealth();
      fetchLEDStatus();
      fetchStats();
    });

    return {
      loading,
      error,
      health,
      ledStatus,
      stats,
      history,
      toggleLED,
      fetchLEDStatus,
      fetchHealth,
      fetchStats,
      fetchHistory,
      formatDate
    };
  }
};
</script>

<style scoped>
.raspberry-control {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  font-family: Arial, sans-serif;
}

h1 {
  text-align: center;
  color: #c51a4a;
}

h2 {
  color: #333;
  border-bottom: 2px solid #c51a4a;
  padding-bottom: 10px;
}

/* Health Section */
.health-section {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.health-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-top: 15px;
}

.health-item {
  background: white;
  padding: 15px;
  border-radius: 5px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* LED Section */
.led-section {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.led-status {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.status-card {
  flex: 1;
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  text-align: center;
}

.led-indicator {
  margin-top: 10px;
  padding: 10px 20px;
  border-radius: 20px;
  font-weight: bold;
  font-size: 18px;
}

.led-indicator.ON {
  background: #28a745;
  color: white;
}

.led-indicator.OFF {
  background: #6c757d;
  color: white;
}

.controls {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.control-group {
  text-align: center;
}

button {
  margin: 5px;
  padding: 12px 24px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.3s;
}

.btn-on {
  background: #28a745;
  color: white;
}

.btn-on:hover {
  background: #218838;
}

.btn-off {
  background: #dc3545;
  color: white;
}

.btn-off:hover {
  background: #c82333;
}

.btn-refresh {
  background: #007bff;
  color: white;
  width: 100%;
}

.btn-refresh:hover {
  background: #0056b3;
}

/* Stats Section */
.stats-section {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
  margin-top: 15px;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #c51a4a;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 5px;
}

/* History Section */
.history-section {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.history-list {
  margin-top: 15px;
  max-height: 400px;
  overflow-y: auto;
}

.history-item {
  display: flex;
  gap: 15px;
  padding: 10px;
  border-bottom: 1px solid #eee;
  align-items: center;
}

.history-time {
  color: #666;
  font-size: 14px;
}

.history-device {
  font-weight: bold;
  color: #c51a4a;
}

.history-led {
  color: #007bff;
}

.history-action {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}

.history-action.ON {
  background: #d4edda;
  color: #155724;
}

.history-action.OFF {
  background: #f8d7da;
  color: #721c24;
}

/* Loading & Error */
.loading {
  text-align: center;
  padding: 20px;
  font-size: 18px;
  color: #007bff;
}

.error {
  background: #f8d7da;
  color: #721c24;
  padding: 15px;
  border-radius: 5px;
  margin: 20px 0;
  border: 1px solid #f5c6cb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>