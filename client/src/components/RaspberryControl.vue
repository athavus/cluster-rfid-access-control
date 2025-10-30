<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-500 via-blue-500 from-gray-500">
    <!-- Header -->
    <header class="sticky top-0 z-50 bg-white/95 backdrop-blur-lg border-b border-gray-200 shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex justify-between items-center">
          <div class="flex items-center gap-4">
            <div class="text-5xl animate-bounce">🍓</div>
            <div>
              <h1 class="text-2xl font-bold text-gray-900">Raspberry Pi IoT Dashboard</h1>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <button 
              @click="fetchAllData" 
              class="p-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-all hover:rotate-180 duration-300"
            >
              <span class="text-xl">🔄</span>
            </button>
            <div :class="[
              'flex items-center gap-2 px-4 py-2 rounded-full font-semibold text-sm',
              isOnline ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            ]">
              <span class="relative flex h-2 w-2">
                <span :class="[
                  'animate-ping absolute inline-flex h-full w-full rounded-full opacity-75',
                  isOnline ? 'bg-green-400' : 'bg-red-400'
                ]"></span>
                <span :class="[
                  'relative inline-flex rounded-full h-2 w-2',
                  isOnline ? 'bg-green-500' : 'bg-red-500'
                ]"></span>
              </span>
              {{ isOnline ? 'Online' : 'Offline' }}
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Error Message -->
      <div v-if="error" class="mb-6 bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
        <span class="text-2xl">⚠️</span>
        <div>
          <h3 class="font-semibold text-red-900">Erro de Conexão</h3>
          <p class="text-sm text-red-700">{{ error }}</p>
        </div>
        <button @click="error = null" class="ml-auto text-red-500 hover:text-red-700">✕</button>
      </div>

      <!-- Stats Row -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all hover:-translate-y-1">
          <div class="flex items-center gap-4">
            <div class="w-14 h-14 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center text-2xl">
              🖥️
            </div>
            <div>
              <div class="text-3xl font-bold text-gray-900">{{ stats.total_devices }}</div>
              <div class="text-sm text-gray-500">Active Devices</div>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all hover:-translate-y-1">
          <div class="flex items-center gap-4">
            <div class="w-14 h-14 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center text-2xl">
              💡
            </div>
            <div>
              <div class="text-3xl font-bold text-gray-900">{{ stats.total_led_actions }}</div>
              <div class="text-sm text-gray-500">Total Actions</div>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all hover:-translate-y-1">
          <div class="flex items-center gap-4">
            <div class="w-14 h-14 bg-gradient-to-br from-pink-500 to-pink-600 rounded-xl flex items-center justify-center text-2xl">
              📊
            </div>
            <div>
              <div class="text-3xl font-bold text-gray-900">{{ stats.led_actions_24h }}</div>
              <div class="text-sm text-gray-500">Last 24h</div>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all hover:-translate-y-1">
          <div class="flex items-center gap-4">
            <div class="w-14 h-14 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl flex items-center justify-center text-2xl">
              ⚡
            </div>
            <div>
              <div class="text-3xl font-bold text-gray-900">{{ stats.realtime_messages }}</div>
              <div class="text-sm text-gray-500">Messages</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Control Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <!-- LED Control Panel -->
        <div class="lg:col-span-1 bg-white rounded-2xl shadow-lg overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 class="text-xl font-bold text-gray-900">LED Control</h2>
            <button @click="fetchLEDStatus" class="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
              Refresh
            </button>
          </div>
          <div class="p-6 space-y-4">
            <!-- Internal LED -->
            <div class="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4 space-y-3">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center text-2xl">
                    💡
                  </div>
                  <div>
                    <h3 class="font-semibold text-gray-900">Internal LED</h3>
                    <p class="text-xs text-gray-500">GPIO Pin 17</p>
                  </div>
                </div>
                <span :class="[
                  'px-3 py-1 rounded-full text-xs font-bold',
                  ledStatus.led_internal === 'ON' ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-600'
                ]">
                  {{ ledStatus.led_internal }}
                </span>
              </div>
              <div class="flex gap-2">
                <button 
                  @click="toggleLED('internal', 'ON')" 
                  class="flex-1 py-2.5 bg-green-500 hover:bg-green-600 text-white font-semibold rounded-lg transition-all hover:scale-105 active:scale-95"
                >
                  ON
                </button>
                <button 
                  @click="toggleLED('internal', 'OFF')" 
                  class="flex-1 py-2.5 bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg transition-all hover:scale-105 active:scale-95"
                >
                  OFF
                </button>
              </div>
            </div>

            <!-- External LED -->
            <div class="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-4 space-y-3">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center text-2xl">
                    💡
                  </div>
                  <div>
                    <h3 class="font-semibold text-gray-900">External LED</h3>
                    <p class="text-xs text-gray-500">GPIO Pin 27</p>
                  </div>
                </div>
                <span :class="[
                  'px-3 py-1 rounded-full text-xs font-bold',
                  ledStatus.led_external === 'ON' ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-600'
                ]">
                  {{ ledStatus.led_external }}
                </span>
              </div>
              <div class="flex gap-2">
                <button 
                  @click="toggleLED('external', 'ON')" 
                  class="flex-1 py-2.5 bg-green-500 hover:bg-green-600 text-white font-semibold rounded-lg transition-all hover:scale-105 active:scale-95"
                >
                  ON
                </button>
                <button 
                  @click="toggleLED('external', 'OFF')" 
                  class="flex-1 py-2.5 bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg transition-all hover:scale-105 active:scale-95"
                >
                  OFF
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Chart -->
        <div class="lg:col-span-2 bg-white rounded-2xl shadow-lg overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 class="text-xl font-bold text-gray-900">LED Activity (Last 24h)</h2>
            <div class="flex gap-4 text-sm">
              <span class="flex items-center gap-2">
                <span class="w-3 h-3 bg-blue-500 rounded-full"></span>
                Internal
              </span>
              <span class="flex items-center gap-2">
                <span class="w-3 h-3 bg-green-500 rounded-full"></span>
                External
              </span>
            </div>
          </div>
          <div class="p-6">
            <div class="h-64 relative">
              <canvas ref="chartCanvas" class="w-full h-full"></canvas>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- System Health -->
        <div class="bg-white rounded-2xl shadow-lg overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-200">
            <h2 class="text-xl font-bold text-gray-900">System Health</h2>
          </div>
          <div class="p-6 space-y-3">
            <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <span class="text-sm font-medium text-gray-600">API Status</span>
              <span :class="[
                'px-3 py-1 text-xs font-bold rounded-full',
                health.api === 'healthy' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
              ]">
                {{ health.api }}
              </span>
            </div>
            <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <span class="text-sm font-medium text-gray-600">Database</span>
              <span :class="[
                'px-3 py-1 text-xs font-bold rounded-full',
                health.database === 'connected' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
              ]">
                {{ health.database }}
              </span>
            </div>
            <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <span class="text-sm font-medium text-gray-600">GPIO</span>
              <span :class="[
                'px-3 py-1 text-xs font-bold rounded-full',
                health.gpio === 'available' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'
              ]">
                {{ health.gpio }}
              </span>
            </div>
            <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <span class="text-sm font-medium text-gray-600">Devices</span>
              <span class="px-3 py-1 bg-blue-100 text-blue-700 text-xs font-bold rounded-full">
                {{ health.registered_devices }}
              </span>
            </div>
          </div>
        </div>

        <!-- Recent Activity -->
        <div class="bg-white rounded-2xl shadow-lg overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 class="text-xl font-bold text-gray-900">Recent Activity</h2>
            <button @click="fetchHistory" class="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
              Load More
            </button>
          </div>
          <div class="p-6">
            <div v-if="history.length === 0" class="text-center text-gray-500 py-8">
              No activity yet
            </div>
            <div v-else class="space-y-3 max-h-80 overflow-y-auto">
              <div 
                v-for="item in history.slice(0, 6)" 
                :key="item.id"
                class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div :class="[
                  'w-10 h-10 rounded-lg flex items-center justify-center text-xl',
                  item.action === 'ON' ? 'bg-green-100' : 'bg-gray-200'
                ]">
                  {{ item.action === 'ON' ? '💡' : '⚫' }}
                </div>
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-semibold text-gray-900 truncate">
                    {{ item.led_type }} LED turned {{ item.action }}
                  </div>
                  <div class="text-xs text-gray-500">
                    Pi #{{ item.raspberry_id }} • {{ formatTime(item.timestamp) }}
                  </div>
                </div>
                <span :class="[
                  'px-2 py-1 text-xs font-bold rounded-full',
                  item.action === 'ON' ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-600'
                ]">
                  {{ item.action }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Grafana Integration -->
        <div class="bg-white rounded-2xl shadow-lg overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 class="text-xl font-bold text-gray-900">Grafana</h2>
            <span class="px-3 py-1 bg-yellow-100 text-yellow-700 text-xs font-bold rounded-full">
              Coming Soon
            </span>
          </div>
          <div class="p-6 text-center">
            <div class="text-6xl mb-4">📊</div>
            <h3 class="text-lg font-bold text-gray-900 mb-2">Connect to Grafana</h3>
            <p class="text-sm text-gray-500 mb-4">
              Visualize your IoT data with powerful dashboards
            </p>
            <div class="space-y-2 mb-6 text-left">
              <div class="flex items-center gap-2 text-sm text-green-600">
                <span>✓</span>
                <span>Real-time metrics</span>
              </div>
              <div class="flex items-center gap-2 text-sm text-green-600">
                <span>✓</span>
                <span>Custom dashboards</span>
              </div>
              <div class="flex items-center gap-2 text-sm text-green-600">
                <span>✓</span>
                <span>Alert notifications</span>
              </div>
            </div>
            <button 
              @click="showGrafanaInfo"
              class="w-full py-2.5 bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 text-white font-semibold rounded-lg transition-all hover:scale-105 active:scale-95"
            >
              Setup Grafana
            </button>
          </div>
        </div>
      </div>
    </main>

    <!-- Loading Overlay -->
    <div v-if="loading" class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div class="w-16 h-16 border-4 border-white/30 border-t-white rounded-full animate-spin"></div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick, onBeforeUnmount } from 'vue';
import { ledService, deviceService, healthService, realtimeService } from '../services/raspberryApi.js';

export default {
  name: 'RaspberryControl',
  setup() {
    const loading = ref(false);
    const isOnline = ref(true);
    const chartCanvas = ref(null);
    const currentRaspberryId = ref(1);
    const error = ref(null);
    let statusInterval = null;
    let historyInterval = null;
    
    const health = ref({
      api: 'loading...',
      database: 'loading...',
      gpio: 'loading...',
      registered_devices: 0
    });
    
    const ledStatus = ref({
      raspberry_id: 1,
      led_internal: 'OFF',
      led_external: 'OFF',
      last_update: null
    });
    
    const stats = ref({
      total_devices: 0,
      total_led_actions: 0,
      led_actions_24h: 0,
      realtime_messages: 0
    });
    
    const history = ref([]);

    const toggleLED = async (ledType, status) => {
      loading.value = true;
      error.value = null;
      
      try {
        if (status === 'ON') {
          await ledService.turnOn(ledType, currentRaspberryId.value);
        } else {
          await ledService.turnOff(ledType, currentRaspberryId.value);
        }
        
        // Atualiza o status local
        if (ledType === 'internal') {
          ledStatus.value.led_internal = status;
        } else {
          ledStatus.value.led_external = status;
        }
        
        // Recarrega dados
        await Promise.all([
          fetchLEDStatus(),
          fetchHistory(),
          fetchStats()
        ]);
      } catch (err) {
        console.error('Erro ao controlar LED:', err);
        error.value = `Erro ao ${status === 'ON' ? 'ligar' : 'desligar'} LED ${ledType}`;
        isOnline.value = false;
      } finally {
        loading.value = false;
      }
    };

    const fetchLEDStatus = async () => {
      try {
        const data = await ledService.getStatus(currentRaspberryId.value);
        ledStatus.value = {
          raspberry_id: data.raspberry_id,
          led_internal: data.led_internal,
          led_external: data.led_external,
          last_update: data.last_update
        };
        isOnline.value = true;
      } catch (err) {
        console.error('Erro ao buscar status dos LEDs:', err);
        isOnline.value = false;
      }
    };

    const fetchHistory = async () => {
      try {
        const data = await ledService.getHistory(null, null, 50);
        history.value = data;
        await nextTick();
        drawChart();
      } catch (err) {
        console.error('Erro ao buscar histórico:', err);
      }
    };

    const fetchHealth = async () => {
      try {
        const data = await healthService.checkHealth();
        health.value = {
          api: data.status || 'healthy',
          database: data.database || 'connected',
          gpio: data.gpio || 'available',
          registered_devices: data.registered_devices || 0
        };
      } catch (err) {
        console.error('Erro ao buscar health:', err);
        health.value = {
          api: 'error',
          database: 'error',
          gpio: 'error',
          registered_devices: 0
        };
      }
    };

    const fetchStats = async () => {
      try {
        const data = await healthService.getStats();
        stats.value = {
          total_devices: data.total_devices || 0,
          total_led_actions: data.total_led_actions || 0,
          led_actions_24h: data.led_actions_24h || 0,
          realtime_messages: data.realtime_messages || 0
        };
      } catch (err) {
        console.error('Erro ao buscar estatísticas:', err);
      }
    };

    const fetchAllData = async () => {
      loading.value = true;
      error.value = null;
      
      try {
        await Promise.all([
          fetchHealth(),
          fetchStats(),
          fetchLEDStatus(),
          fetchHistory()
        ]);
        isOnline.value = true;
      } catch (err) {
        console.error('Erro ao carregar dados:', err);
        error.value = 'Erro ao conectar com a API';
        isOnline.value = false;
      } finally {
        loading.value = false;
      }
    };

    const formatTime = (dateString) => {
      if (!dateString) return 'N/A';
      const date = new Date(dateString);
      const now = new Date();
      const diff = Math.floor((now - date) / 1000);
      
      if (diff < 60) return `${diff}s ago`;
      if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
      if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
      return date.toLocaleDateString('pt-BR');
    };

    const showGrafanaInfo = () => {
      alert('Grafana Setup:\n\n1. Install Grafana\n2. Configure Prometheus/InfluxDB\n3. Add data source\n4. Import dashboard JSON\n5. Connect to your API');
    };

    const drawChart = () => {
      const canvas = chartCanvas.value;
      if (!canvas || history.value.length === 0) return;
      
      const ctx = canvas.getContext('2d');
      const width = canvas.width = canvas.offsetWidth * 2;
      const height = canvas.height = canvas.offsetHeight * 2;
      ctx.scale(2, 2);
      
      ctx.clearRect(0, 0, width, height);
      
      // Grid
      ctx.strokeStyle = '#e5e7eb';
      ctx.lineWidth = 1;
      for (let i = 0; i <= 5; i++) {
        const y = (height / 2) * (i / 5);
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width / 2, y);
        ctx.stroke();
      }
      
      // Processa dados do histórico para o gráfico
      const last24h = history.value.filter(item => {
        const itemDate = new Date(item.timestamp);
        const now = new Date();
        return (now - itemDate) < 24 * 60 * 60 * 1000;
      });
      
      // Agrupa por hora
      const internalByHour = new Array(24).fill(0);
      const externalByHour = new Array(24).fill(0);
      
      last24h.forEach(item => {
        const date = new Date(item.timestamp);
        const hour = date.getHours();
        if (item.led_type === 'internal' && item.action === 'ON') {
          internalByHour[hour]++;
        } else if (item.led_type === 'external' && item.action === 'ON') {
          externalByHour[hour]++;
        }
      });
      
      const maxValue = Math.max(...internalByHour, ...externalByHour, 1);
      
      // Internal LED
      ctx.strokeStyle = '#3b82f6';
      ctx.lineWidth = 3;
      ctx.beginPath();
      for (let i = 0; i < 10; i++) {
        const dataIndex = Math.floor((i / 10) * 24);
        const value = internalByHour[dataIndex];
        const x = (width / 2) * (i / 9);
        const y = (height / 2) - (value / maxValue * height / 2 * 0.8);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
      
      // External LED
      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 3;
      ctx.beginPath();
      for (let i = 0; i < 10; i++) {
        const dataIndex = Math.floor((i / 10) * 24);
        const value = externalByHour[dataIndex];
        const x = (width / 2) * (i / 9);
        const y = (height / 2) - (value / maxValue * height / 2 * 0.8);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    };

    onMounted(async () => {
      console.log('🍓 Dashboard conectado à API FastAPI');
      await fetchAllData();
      await nextTick();
      drawChart();
      window.addEventListener('resize', drawChart);
      
      // Auto-refresh a cada 5 segundos
      statusInterval = setInterval(() => {
        fetchLEDStatus();
        fetchStats();
      }, 5000);
      
      // Refresh do histórico a cada 10 segundos
      historyInterval = setInterval(() => {
        fetchHistory();
      }, 10000);
    });

    onBeforeUnmount(() => {
      if (statusInterval) clearInterval(statusInterval);
      if (historyInterval) clearInterval(historyInterval);
      window.removeEventListener('resize', drawChart);
    });

    return {
      loading,
      isOnline,
      health,
      ledStatus,
      stats,
      history,
      chartCanvas,
      error,
      toggleLED,
      fetchLEDStatus,
      fetchHistory,
      fetchAllData,
      formatTime,
      showGrafanaInfo
    };
  }
};
</script>
