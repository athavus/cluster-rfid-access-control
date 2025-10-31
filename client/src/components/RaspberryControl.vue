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

          <div class="mt-3">
            <label class="block text-sm text-green-900 mb-1">Pino GPIO (BCM) do LED externo</label>
            <input
              type="number"
              class="w-32 px-2 py-1 border rounded"
              :min="0"
              :max="27"
              v-model.number="externalLedPin"
            />
          </div>

          <div class="mt-3">
            <label class="block text-sm text-green-900 mb-1">IP do dispositivo alvo (ex.: 192.168.130.166)</label>
            <input
              type="text"
              class="w-64 px-2 py-1 border rounded"
              placeholder="192.168.130.166"
              v-model.trim="targetHost"
            />
            <p class="mt-1 text-xs text-green-700">Somente LED usa este IP. Porta 8000 será assumida se omitida.</p>
          </div>

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
            <p>{{ formatCpuPercent(selectedDeviceDetails.cpu_percent) }}%</p>
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
import { deviceService, ledService, realtimeService, rfidService } from '../services/raspberryApi.js';

export default {
  name: 'RaspberryControl',
  components: {},
  setup() {
    const loading = ref(false);
    const error = ref(null);
    const isOnline = ref(true);

    const devices = ref([]);
    const selectedDeviceId = ref(null);
    const selectedDeviceDetails = ref(null);
    const realtimeMessages = ref([]);
    const externalLedPin = ref(17);
    const targetHost = ref('');
    const lastRfidUid = ref(null);
    const lastRfidTimestamp = ref(null);
    const showRfidBanner = ref(false);
    const showNameModal = ref(false);
    const newTagName = ref('');
    const modalCountdown = ref(15);
    let modalTimer = null;

    let refreshTimer = null;

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

    const pollLastRfid = async () => {
      if (!selectedDeviceId.value) return;
      try {
        const data = await rfidService.getLastRead(selectedDeviceId.value);
        if (!data.exists) return;
        const ts = new Date(data.timestamp).getTime();
        if (lastRfidTimestamp.value && ts <= lastRfidTimestamp.value) return;
        lastRfidUid.value = data.uid;
        lastRfidTimestamp.value = ts;
        showRfidBanner.value = true;
        if (!data.tag_name || data.tag_name === '<Sem nome>') {
          openNameModal();
        }
      } catch {}
    };

    const openNameModal = () => {
      newTagName.value = '';
      showNameModal.value = true;
      modalCountdown.value = 15;
      if (modalTimer) clearInterval(modalTimer);
      modalTimer = setInterval(() => {
        modalCountdown.value -= 1;
        if (modalCountdown.value <= 0) {
          closeNameModal();
        }
      }, 1000);
    };

    const closeNameModal = () => {
      showNameModal.value = false;
      if (modalTimer) {
        clearInterval(modalTimer);
        modalTimer = null;
      }
    };

    const submitTagName = async () => {
      if (!lastRfidUid.value || !newTagName.value.trim()) return;
      try {
        await rfidService.nameTag(lastRfidUid.value, newTagName.value.trim(), selectedDeviceId.value);
        closeNameModal();
      } catch (e) {
        console.error(e);
      }
    };

    const selectDevice = async (id) => {
      if (id === selectedDeviceId.value) return;
      selectedDeviceId.value = id;
      externalLedPin.value = 17;
      
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

    const formatCpuPercent = (value) => {
      if (typeof value === 'number') return value.toFixed(1);
      const parsed = parseFloat(String(value ?? '').replace('%', '').trim());
      if (!Number.isFinite(parsed)) return '0.0';
      return parsed.toFixed(1);
    };

    const normalizeHost = (raw) => {
      if (!raw) return null;
      const cleaned = String(raw).trim().replace(/;|\s|,/g, '');
      if (cleaned.length === 0) return null;
      return cleaned;
    };

    const toggleLED = async (status) => {
      loading.value = true;
      error.value = null;
      try {
        const host = normalizeHost(targetHost.value);
        if (status === 'ON') {
          await ledService.turnOn('external', selectedDeviceId.value, externalLedPin.value, host);
        } else {
          await ledService.turnOff('external', selectedDeviceId.value, externalLedPin.value, host);
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
          pollLastRfid();
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
      externalLedPin,
      targetHost,
      filteredRealtimeMessages,
      fetchAllData,
      selectDevice,
      formatDate,
      ledStatusClasses,
      stringifyMessage,
      formatCpuPercent,
      normalizeHost,
      toggleLED,
      // RFID
      showRfidBanner,
      lastRfidUid,
      showNameModal,
      newTagName,
      modalCountdown,
      submitTagName,
      closeNameModal,
      
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

<!-- RFID Banner & Modal UI -->
<template>
  <div v-if="showRfidBanner" class="fixed top-20 right-4 bg-blue-600 text-white px-4 py-2 rounded shadow-lg z-50">
    RFID detectado: UID {{ lastRfidUid }}
  </div>

  <div v-if="showNameModal" class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg p-6 w-full max-w-md">
      <h3 class="text-lg font-semibold mb-2">Nomear nova Tag</h3>
      <p class="text-sm text-gray-600 mb-4">UID: {{ lastRfidUid }} • Fecha em {{ modalCountdown }}s</p>
      <input type="text" v-model.trim="newTagName" class="w-full border rounded px-3 py-2 mb-4" placeholder="Nome da tag" />
      <div class="flex justify-end gap-2">
        <button @click="closeNameModal" class="px-3 py-1 border rounded">Cancelar</button>
        <button @click="submitTagName" class="px-3 py-1 bg-blue-600 text-white rounded">Salvar</button>
      </div>
    </div>
  </div>
</template>


