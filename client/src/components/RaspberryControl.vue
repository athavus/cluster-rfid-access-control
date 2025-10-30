<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div class="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
        <h1 class="text-xl font-semibold text-gray-900">Raspberry Pi IoT Dashboard</h1>
        <div class="flex items-center gap-4">
          <button @click="fetchAllData" class="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md">Atualizar</button>
          <div class="flex items-center gap-2 text-sm font-medium">
            <span class="inline-block w-3 h-3 rounded-full" :class="isOnline ? 'bg-green-500' : 'bg-red-500'" aria-label="Conexão"></span>
            <span>{{ isOnline ? 'Online' : 'Offline' }}</span>
          </div>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-4 gap-6">

      <!-- Device Selector -->
      <section class="col-span-1 bg-white rounded-lg shadow p-4 overflow-auto max-h-[calc(100vh-128px)]">
        <h2 class="font-semibold text-gray-800 mb-4">Dispositivos</h2>
        <ul class="space-y-2">
          <li v-for="device in devices" :key="device.raspberry_id">
            <button
              @click="selectDevice(device.raspberry_id)"
              type="button"
              class="w-full text-left px-4 py-2 rounded-md cursor-pointer transition-colors"
              :class="selectedDeviceId === device.raspberry_id ? 'bg-blue-500 text-white' : 'hover:bg-blue-50 text-gray-700'"
            >
              Raspberry ID: {{ device.raspberry_id }}
            </button>
          </li>
        </ul>
      </section>

      <!-- Device Details -->
      <section
        v-if="selectedDeviceDetails"
        class="col-span-3 bg-white rounded-lg shadow p-6 overflow-auto max-h-[calc(100vh-128px)]"
      >
        <h2 class="text-lg font-semibold mb-4">Detalhes do Dispositivo: {{ selectedDeviceId }}</h2>

        <!-- LED Externo Status + Controle -->
        <div class="mb-6 max-w-md p-4 rounded-md bg-green-50">
          <h3 class="font-semibold text-green-700 mb-2">LED Externo</h3>
          <p>
            Status:
            <span :class="ledStatusClasses(selectedDeviceDetails.led_external_status)">
              {{ selectedDeviceDetails.led_external_status ? 'ON' : 'OFF' }}
            </span>
          </p>
          <p>Última atualização: {{ formatDate(selectedDeviceDetails.last_update) }}</p>

          <div class="mt-4 flex gap-4">
            <button
              @click="toggleLED('ON')"
              :disabled="loading"
              class="flex-1 py-2.5 bg-green-500 hover:bg-green-600 text-white font-semibold rounded-lg transition-all hover:scale-105 active:scale-95"
            >
              Ligar
            </button>
            <button
              @click="toggleLED('OFF')"
              :disabled="loading"
              class="flex-1 py-2.5 bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg transition-all hover:scale-105 active:scale-95"
            >
              Desligar
            </button>
          </div>
        </div>

        <!-- Device Status Info -->
        <div class="grid grid-cols-3 gap-6 mb-6 text-gray-700">
          <div>
            <h4 class="font-semibold mb-1">WiFi Status</h4>
            <p>{{ selectedDeviceDetails.wifi_status || 'Desconhecido' }}</p>
          </div>
          <div>
            <h4 class="font-semibold mb-1">Uso de Memória</h4>
            <p>{{ selectedDeviceDetails.mem_usage || 'Desconhecido' }}</p>
          </div>
          <div>
            <h4 class="font-semibold mb-1">Temperatura CPU</h4>
            <p>{{ selectedDeviceDetails.cpu_temp || 'Desconhecido' }}</p>
          </div>
          <div>
            <h4 class="font-semibold mb-1">% CPU</h4>
            <p>{{ selectedDeviceDetails.cpu_percent.toFixed(1) }}%</p>
          </div>
          <div>
            <h4 class="font-semibold mb-1">GPIO usados</h4>
            <p>{{ selectedDeviceDetails.gpio_used_count }}</p>
          </div>
          <div>
            <h4 class="font-semibold mb-1">SPI Buses</h4>
            <p>{{ selectedDeviceDetails.spi_buses }}</p>
          </div>
          <div>
            <h4 class="font-semibold mb-1">I2C Buses</h4>
            <p>{{ selectedDeviceDetails.i2c_buses }}</p>
          </div>
          <div>
            <h4 class="font-semibold mb-1">USB Devices</h4>
            <p>{{ selectedDeviceDetails.usb_devices_count }}</p>
          </div>
          <div>
            <h4 class="font-semibold mb-1">Interfaces de Rede</h4>
            <p>{{ selectedDeviceDetails.net_ifaces.join(', ') || 'Nenhuma' }}</p>
          </div>
        </div>

        <!-- GRÁFICOS EM TEMPO REAL -->
        <div class="mt-6 bg-gray-50 p-6 rounded-lg border border-gray-200">
          <h3 class="font-semibold mb-4 text-lg">Monitoramento em Tempo Real</h3>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- CPU Usage -->
            <div class="bg-white p-4 rounded-lg shadow">
              <h4 class="font-semibold mb-3 text-gray-700">CPU Usage (%)</h4>
              <div class="chart-container">
                <Line :data="cpuChartData" :options="chartOptions" />
              </div>
            </div>
            
            <!-- Temperatura -->
            <div class="bg-white p-4 rounded-lg shadow">
              <h4 class="font-semibold mb-3 text-gray-700">Temperatura (°C)</h4>
              <div class="chart-container">
                <Line :data="tempChartData" :options="chartOptions" />
              </div>
            </div>
            
            <!-- Network -->
            <div class="bg-white p-4 rounded-lg shadow col-span-1 md:col-span-2">
              <h4 class="font-semibold mb-3 text-gray-700">Tráfego de Rede (bytes)</h4>
              <div class="chart-container">
                <Line :data="networkChartData" :options="chartOptions" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Loading and Errors -->
      <div v-if="error" class="fixed bottom-4 right-4 bg-red-600 text-white px-4 py-2 rounded shadow-lg z-50">
        {{ error }}
        <button @click="error = null" class="ml-4 font-bold">×</button>
      </div>

      <div v-if="loading" class="fixed inset-0 bg-white bg-opacity-80 flex items-center justify-center z-50">
        <svg class="animate-spin h-12 w-12 text-gray-700" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
        </svg>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { Line } from 'vue-chartjs';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import { deviceService, ledService, realtimeService } from '../services/raspberryApi.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

export default {
  name: 'RaspberryControl',
  components: {
    Line
  },
  setup() {
    const loading = ref(false);
    const error = ref(null);
    const isOnline = ref(true);

    const devices = ref([]);
    const selectedDeviceId = ref(null);
    const selectedDeviceDetails = ref(null);
    const realtimeMessages = ref([]);

    // Arrays para histórico dos gráficos
    const cpuHistory = ref([]);
    const tempHistory = ref([]);
    const networkSentHistory = ref([]);
    const networkRecvHistory = ref([]);
    const timeLabels = ref([]);

    let refreshTimer = null;

    // Configurações dos gráficos
    const chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top'
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    };

    // Dados reativos dos gráficos
    const cpuChartData = computed(() => ({
      labels: timeLabels.value,
      datasets: [{
        label: 'CPU %',
        data: cpuHistory.value,
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true
      }]
    }));

    const tempChartData = computed(() => ({
      labels: timeLabels.value,
      datasets: [{
        label: 'Temperatura °C',
        data: tempHistory.value,
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.4,
        fill: true
      }]
    }));

    const networkChartData = computed(() => ({
      labels: timeLabels.value,
      datasets: [
        {
          label: 'Enviado',
          data: networkSentHistory.value,
          borderColor: 'rgb(34, 197, 94)',
          backgroundColor: 'rgba(34, 197, 94, 0.1)',
          tension: 0.4
        },
        {
          label: 'Recebido',
          data: networkRecvHistory.value,
          borderColor: 'rgb(168, 85, 247)',
          backgroundColor: 'rgba(168, 85, 247, 0.1)',
          tension: 0.4
        }
      ]
    }));

    // Atualizar gráficos
    const updateCharts = (details) => {
      if (!details) return;
      
      const now = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      const maxPoints = 20;
      
      // Atualizar labels de tempo
      timeLabels.value.push(now);
      if (timeLabels.value.length > maxPoints) {
        timeLabels.value.shift();
      }
      
      // CPU
      cpuHistory.value.push(details.cpu_percent || 0);
      if (cpuHistory.value.length > maxPoints) {
        cpuHistory.value.shift();
      }
      
      // Temperatura (remover °C)
      const temp = parseFloat((details.cpu_temp || '0').toString().replace('°C', '').replace('C', '').trim()) || 0;
      tempHistory.value.push(temp);
      if (tempHistory.value.length > maxPoints) {
        tempHistory.value.shift();
      }
      
      // Network
      networkSentHistory.value.push(details.net_bytes_sent || 0);
      networkRecvHistory.value.push(details.net_bytes_recv || 0);
      if (networkSentHistory.value.length > maxPoints) {
        networkSentHistory.value.shift();
        networkRecvHistory.value.shift();
      }

      console.log('Gráficos atualizados:', { 
        cpu: details.cpu_percent, 
        temp, 
        sent: details.net_bytes_sent,
        recv: details.net_bytes_recv
      });
    };

    const fetchDevices = async () => {
      try {
        const data = await deviceService.getAllDevices();
        devices.value = data;
        if (!selectedDeviceId.value && data.length > 0) {
          selectedDeviceId.value = data[0].raspberry_id;
        }
      } catch (err) {
        error.value = 'Erro ao buscar dispositivos.';
        isOnline.value = false;
      }
    };

    const fetchDeviceDetails = async (id) => {
      if (!id) return;
      try {
        const details = await deviceService.getDevice(id);
        selectedDeviceDetails.value = details;
        updateCharts(details); // ← Atualizar gráficos
        isOnline.value = true;
      } catch {
        error.value = 'Erro ao buscar detalhes do dispositivo.';
        selectedDeviceDetails.value = null;
        isOnline.value = false;
      }
    };

    const fetchRealtimeMessages = async () => {
      try {
        const data = await realtimeService.getData(50);
        realtimeMessages.value = data.data || [];
        isOnline.value = true;
      } catch {
        error.value = 'Erro ao buscar mensagens em tempo real.';
        isOnline.value = false;
      }
    };

    const fetchAllData = async () => {
      loading.value = true;
      error.value = null;
      try {
        await fetchDevices();
        if (selectedDeviceId.value) {
          await fetchDeviceDetails(selectedDeviceId.value);
        }
        await fetchRealtimeMessages();
        isOnline.value = true;
      } catch {
        error.value = 'Erro ao carregar dados da API.';
        isOnline.value = false;
      }
      loading.value = false;
    };

    const selectDevice = async (id) => {
      if (id === selectedDeviceId.value) return;
      selectedDeviceId.value = id;
      
      // Resetar histórico ao trocar de dispositivo
      cpuHistory.value = [];
      tempHistory.value = [];
      networkSentHistory.value = [];
      networkRecvHistory.value = [];
      timeLabels.value = [];
      
      loading.value = true;
      error.value = null;
      await fetchDeviceDetails(id);
      loading.value = false;
    };

    const filteredRealtimeMessages = computed(() => {
      return realtimeMessages.value.filter(msg => msg.raspberry_id == selectedDeviceId.value);
    });

    const formatDate = (dateStr) => {
      if (!dateStr) return 'N/A';
      return new Date(dateStr).toLocaleString('pt-BR');
    };

    const ledStatusClasses = (statusBoolean) => {
      return statusBoolean ? 'text-green-600 font-semibold' : 'text-gray-500 font-normal';
    };

    const stringifyMessage = (msg) => {
      try {
        return JSON.stringify(msg, null, 2);
      } catch {
        return String(msg);
      }
    };

    const toggleLED = async (status) => {
      loading.value = true;
      error.value = null;
      try {
        if (status === 'ON') {
          await ledService.turnOn('external', selectedDeviceId.value);
        } else {
          await ledService.turnOff('external', selectedDeviceId.value);
        }
        await fetchDeviceDetails(selectedDeviceId.value);
      } catch (err) {
        error.value = `Erro ao ${status === 'ON' ? 'ligar' : 'desligar'} LED externo`;
      }
      loading.value = false;
    };

    onMounted(() => {
      fetchAllData();
      refreshTimer = setInterval(() => {
        if (selectedDeviceId.value) {
          fetchDeviceDetails(selectedDeviceId.value);
          fetchRealtimeMessages();
        }
      }, 5000);
    });

    onBeforeUnmount(() => {
      if (refreshTimer) clearInterval(refreshTimer);
    });

    return {
      loading,
      error,
      isOnline,
      devices,
      selectedDeviceId,
      selectedDeviceDetails,
      realtimeMessages,
      filteredRealtimeMessages,
      fetchAllData,
      selectDevice,
      formatDate,
      ledStatusClasses,
      stringifyMessage,
      toggleLED,
      // Gráficos
      cpuChartData,
      tempChartData,
      networkChartData,
      chartOptions
    };
  }
};
</script>

<style scoped>
section {
  scrollbar-width: thin;
  scrollbar-color: rgba(107, 114, 128, 0.5) transparent;
}

section::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

section::-webkit-scrollbar-thumb {
  background-color: rgba(107, 114, 128, 0.5);
  border-radius: 4px;
}

button {
  transition: background-color 0.3s ease;
}

.chart-container {
  position: relative;
  height: 250px;
  width: 100%;
}
</style>
