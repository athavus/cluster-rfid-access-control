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
              <span class="px-3 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-full">
                {{ health.api }}
              </span>
            </div>
            <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <span class="text-sm font-medium text-gray-600">Database</span>
              <span class="px-3 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-full">
                {{ health.database }}
              </span>
            </div>
            <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <span class="text-sm font-medium text-gray-600">GPIO</span>
              <span class="px-3 py-1 bg-yellow-100 text-yellow-700 text-xs font-bold rounded-full">
                {{ health.gpio }}
              </span>
            </div>
            <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <span class="text-sm font-medium text-gray-600">RabbitMQ</span>
              <span class="px-3 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-full">
                running
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
            <div class="space-y-3 max-h-80 overflow-y-auto">
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
import { ref, onMounted, nextTick } from 'vue';

export default {
  name: 'RaspberryControl',
  setup() {
    const loading = ref(false);
    const isOnline = ref(true);
    const chartCanvas = ref(null);
    
    const health = ref({
      api: 'healthy',
      database: 'connected',
      gpio: 'available',
      registered_devices: 3
    });
    
    const ledStatus = ref({
      raspberry_id: 1,
      led_internal: 'ON',
      led_external: 'OFF',
      last_update: new Date().toISOString()
    });
    
    const stats = ref({
      total_devices: 3,
      total_led_actions: 1247,
      led_actions_24h: 89,
      realtime_messages: 342
    });
    
    const history = ref([
      { id: 1, raspberry_id: 1, led_type: 'internal', action: 'ON', timestamp: new Date().toISOString() },
      { id: 2, raspberry_id: 1, led_type: 'external', action: 'OFF', timestamp: new Date(Date.now() - 60000).toISOString() },
      { id: 3, raspberry_id: 2, led_type: 'internal', action: 'ON', timestamp: new Date(Date.now() - 120000).toISOString() },
      { id: 4, raspberry_id: 1, led_type: 'internal', action: 'OFF', timestamp: new Date(Date.now() - 180000).toISOString() },
      { id: 5, raspberry_id: 3, led_type: 'external', action: 'ON', timestamp: new Date(Date.now() - 240000).toISOString() },
      { id: 6, raspberry_id: 1, led_type: 'external', action: 'ON', timestamp: new Date(Date.now() - 300000).toISOString() },
    ]);

    const toggleLED = async (ledType, status) => {
      loading.value = true;
      await new Promise(resolve => setTimeout(resolve, 400));
      
      if (ledType === 'internal') {
        ledStatus.value.led_internal = status;
      } else {
        ledStatus.value.led_external = status;
      }
      
      history.value.unshift({
        id: history.value.length + 1,
        raspberry_id: 1,
        led_type: ledType,
        action: status,
        timestamp: new Date().toISOString()
      });
      
      stats.value.total_led_actions++;
      stats.value.led_actions_24h++;
      
      loading.value = false;
    };

    const fetchLEDStatus = async () => {
      loading.value = true;
      await new Promise(resolve => setTimeout(resolve, 300));
      loading.value = false;
    };

    const fetchHistory = async () => {
      loading.value = true;
      await new Promise(resolve => setTimeout(resolve, 400));
      loading.value = false;
    };

    const fetchAllData = async () => {
      loading.value = true;
      await new Promise(resolve => setTimeout(resolve, 500));
      loading.value = false;
    };

    const formatTime = (dateString) => {
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
      if (!canvas) return;
      
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
      
      // Internal LED
      ctx.strokeStyle = '#3b82f6';
      ctx.lineWidth = 3;
      ctx.beginPath();
      const internalData = [30, 45, 35, 50, 40, 55, 45, 60, 50, 65];
      for (let i = 0; i < internalData.length; i++) {
        const x = (width / 2) * (i / (internalData.length - 1));
        const y = (height / 2) - (internalData[i] / 100 * height / 2);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
      
      // External LED
      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 3;
      ctx.beginPath();
      const externalData = [20, 35, 40, 30, 45, 50, 40, 55, 60, 50];
      for (let i = 0; i < externalData.length; i++) {
        const x = (width / 2) * (i / (externalData.length - 1));
        const y = (height / 2) - (externalData[i] / 100 * height / 2);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    };

    onMounted(async () => {
      console.log('🍓 Dashboard com Tailwind CSS carregado!');
      await nextTick();
      drawChart();
      window.addEventListener('resize', drawChart);
    });

    return {
      loading,
      isOnline,
      health,
      ledStatus,
      stats,
      history,
      chartCanvas,
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