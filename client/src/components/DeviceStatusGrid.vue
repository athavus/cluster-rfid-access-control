<template>
  <div class="grid grid-cols-3 gap-6 mb-6 text-gray-700">
    <div>
      <h4 class="font-semibold mb-1">WiFi Status</h4>
      <p>{{ deviceDetails.wifi_status || 'Desconhecido' }}</p>
    </div>
    <div>
      <h4 class="font-semibold mb-1">Uso de Memória</h4>
      <p>{{ deviceDetails.mem_usage || 'Desconhecido' }}</p>
    </div>
    <div>
      <h4 class="font-semibold mb-1">Temperatura CPU</h4>
      <p>{{ deviceDetails.cpu_temp || 'Desconhecido' }}</p>
    </div>
    <div>
      <h4 class="font-semibold mb-1">% CPU</h4>
      <p>{{ formatCpuPercent(deviceDetails.cpu_percent) }}%</p>
    </div>
    <div>
      <h4 class="font-semibold mb-1">GPIO usados</h4>
      <p>{{ deviceDetails.gpio_used_count }}</p>
    </div>
    <div>
      <h4 class="font-semibold mb-1">SPI Buses</h4>
      <p>{{ deviceDetails.spi_buses }}</p>
    </div>
    <div>
      <h4 class="font-semibold mb-1">I2C Buses</h4>
      <p>{{ deviceDetails.i2c_buses }}</p>
    </div>
    <div>
      <h4 class="font-semibold mb-1">USB Devices</h4>
      <p>{{ deviceDetails.usb_devices_count }}</p>
    </div>
    <div>
      <h4 class="font-semibold mb-1">Interfaces de Rede</h4>
      <p>{{ deviceDetails.net_ifaces?.join(', ') || 'Nenhuma' }}</p>
    </div>
    <div>
      <h4 class="font-semibold mb-1">Status Fechadura</h4>
      <p :class="getServoStatusClass(displayServoStatus)">
        {{ formatServoStatus(displayServoStatus) }}
      </p>
    </div>
    <div v-if="deviceDetails.last_door_open">
      <h4 class="font-semibold mb-1">Última Abertura</h4>
      <p class="text-sm">{{ formatDate(deviceDetails.last_door_open) }}</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DeviceStatusGrid',
  props: {
    deviceDetails: {
      type: Object,
      required: true
    },
    showRfidBanner: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      servoOpenTimer: null,
      isServoOpen: false
    };
  },
  watch: {
    showRfidBanner(newVal) {
      if (newVal) {
        // Quando o popup aparecer, mostra "aberta" por 1 segundo
        this.isServoOpen = true;
        if (this.servoOpenTimer) {
          clearTimeout(this.servoOpenTimer);
        }
        this.servoOpenTimer = setTimeout(() => {
          this.isServoOpen = false;
        }, 1000); // 1 segundo
      } else {
        // Se o popup fechar, garante que está fechada
        this.isServoOpen = false;
        if (this.servoOpenTimer) {
          clearTimeout(this.servoOpenTimer);
          this.servoOpenTimer = null;
        }
      }
    }
  },
  computed: {
    displayServoStatus() {
      // Sempre mostra "closed" exceto quando isServoOpen for true (1 segundo após popup aparecer)
      return this.isServoOpen ? 'open' : 'closed';
    }
  },
  beforeUnmount() {
    if (this.servoOpenTimer) {
      clearTimeout(this.servoOpenTimer);
    }
  },
  methods: {
    formatCpuPercent(value) {
      if (typeof value === 'number') return value.toFixed(1);
      const parsed = parseFloat(String(value ?? '').replace('%', '').trim());
      if (!Number.isFinite(parsed)) return '0.0';
      return parsed.toFixed(1);
    },
    formatServoStatus(status) {
      if (!status) return 'Desconhecido';
      const statusMap = {
        'closed': 'Fechada',
        'open': 'Aberta',
        'moving': 'Movendo'
      };
      return statusMap[status] || status;
    },
    getServoStatusClass(status) {
      if (!status) return '';
      const classMap = {
        'closed': 'text-gray-600',
        'open': 'text-green-600 font-semibold',
        'moving': 'text-yellow-600 font-semibold'
      };
      return classMap[status] || '';
    },
    formatDate(dateString) {
      if (!dateString) return 'Nunca';
      try {
        const date = new Date(dateString);
        return date.toLocaleString('pt-BR');
      } catch {
        return dateString;
      }
    }
  }
};
</script>

