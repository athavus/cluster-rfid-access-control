<template>
  <div>
    <!-- Grid de Status Existente -->
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

    <!-- Gráficos em Tempo Real -->
    <div class="mt-8">
      <h3 class="text-xl font-bold mb-4 text-gray-800">Monitoramento em Tempo Real</h3>
      
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Gráfico CPU -->
        <div class="bg-white p-4 rounded-lg shadow">
          <div class="flex justify-between items-center mb-3">
            <h4 class="font-semibold text-gray-700">CPU Usage</h4>
            <span class="text-2xl font-bold text-blue-600">{{ formatCpuPercent(deviceDetails.cpu_percent) }}%</span>
          </div>
          <canvas ref="cpuCanvas" width="600" height="300" class="w-full"></canvas>
        </div>

        <!-- Gráfico RAM -->
        <div class="bg-white p-4 rounded-lg shadow">
          <div class="flex justify-between items-center mb-3">
            <h4 class="font-semibold text-gray-700">Memória RAM</h4>
            <span class="text-2xl font-bold text-green-600">{{ currentRamValue }} MB</span>
          </div>
          <canvas ref="ramCanvas" width="600" height="300" class="w-full"></canvas>
        </div>

        <!-- Gráfico Temperatura -->
        <div class="bg-white p-4 rounded-lg shadow">
          <div class="flex justify-between items-center mb-3">
            <h4 class="font-semibold text-gray-700">Temperatura CPU</h4>
            <span class="text-2xl font-bold text-red-600">{{ currentTemp }}°C</span>
          </div>
          <canvas ref="tempCanvas" width="600" height="300" class="w-full"></canvas>
        </div>
      </div>
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
      isServoOpen: false,
      deviceHistories: {}, // Armazena histórico de cada dispositivo
      maxDataPoints: 30,
      currentRamValue: 0,
      currentTemp: 0,
      maxRamValue: 2048, // Máximo fixo para o gráfico de RAM em MB (2GB)
      currentDeviceId: null
    };
  },
  computed: {
    displayServoStatus() {
      return this.isServoOpen ? 'open' : 'closed';
    },
    deviceId() {
      return this.deviceDetails?.raspberry_id || 'unknown';
    },
    cpuHistory() {
      return this.getDeviceHistory('cpu');
    },
    ramHistory() {
      return this.getDeviceHistory('ram');
    },
    tempHistory() {
      return this.getDeviceHistory('temp');
    }
  },
  watch: {
    showRfidBanner(newVal) {
      if (newVal) {
        this.isServoOpen = true;
        if (this.servoOpenTimer) {
          clearTimeout(this.servoOpenTimer);
        }
        this.servoOpenTimer = setTimeout(() => {
          this.isServoOpen = false;
        }, 5000);
      } else {
        this.isServoOpen = false;
        if (this.servoOpenTimer) {
          clearTimeout(this.servoOpenTimer);
          this.servoOpenTimer = null;
        }
      }
    },
    deviceDetails: {
      handler(newVal) {
        this.updateChartData(newVal);
      },
      deep: true
    },
    deviceId(newId, oldId) {
      // Quando troca de dispositivo, redesenha os gráficos
      if (newId !== oldId) {
        this.currentDeviceId = newId;
        this.$nextTick(() => {
          this.redrawAllCharts();
        });
      }
    }
  },
  mounted() {
    this.currentDeviceId = this.deviceId;
    this.initializeDeviceHistory(this.deviceId);
    this.updateChartData(this.deviceDetails);
  },
  beforeUnmount() {
    if (this.servoOpenTimer) {
      clearTimeout(this.servoOpenTimer);
    }
  },
  methods: {
    initializeDeviceHistory(deviceId) {
      // Cria histórico vazio para o dispositivo se não existir
      if (!this.deviceHistories[deviceId]) {
        this.deviceHistories[deviceId] = {
          cpu: Array(this.maxDataPoints).fill(0),
          ram: Array(this.maxDataPoints).fill(0),
          temp: Array(this.maxDataPoints).fill(0)
        };
      }
    },
    getDeviceHistory(type) {
      const deviceId = this.deviceId;
      this.initializeDeviceHistory(deviceId);
      return this.deviceHistories[deviceId][type];
    },
    redrawAllCharts() {
      if (this.$refs.cpuCanvas) {
        this.drawChart(this.$refs.cpuCanvas, this.cpuHistory, '#3b82f6', 100);
        this.drawChart(this.$refs.ramCanvas, this.ramHistory, '#10b981', this.maxRamValue);
        this.drawChart(this.$refs.tempCanvas, this.tempHistory, '#ef4444', 100);
      }
    },
    updateChartData(details) {
      const deviceId = this.deviceId;
      this.initializeDeviceHistory(deviceId);
      
      // Extrai CPU
      const cpuValue = parseFloat(this.formatCpuPercent(details.cpu_percent));
      
      // Extrai RAM (em MB)
      let ramValue = 0;
      if (details.mem_usage) {
        const memStr = String(details.mem_usage);
        // Extrai apenas o número em MB (ex: "454 MB" -> 454)
        const match = memStr.match(/(\d+(?:\.\d+)?)\s*MB/i);
        if (match) {
          ramValue = parseFloat(match[1]);
        }
      }
      this.currentRamValue = ramValue.toFixed(0);
      
      // Extrai Temperatura
      let tempValue = 0;
      if (details.cpu_temp) {
        const tempStr = String(details.cpu_temp);
        tempValue = parseFloat(tempStr.replace('°C', '').replace('C', '').trim());
      }
      this.currentTemp = tempValue.toFixed(1);
      
      // Adiciona novos pontos ao histórico do dispositivo específico
      const history = this.deviceHistories[deviceId];
      history.cpu.push(cpuValue);
      history.ram.push(ramValue);
      history.temp.push(tempValue);
      
      // Remove pontos antigos (mantém apenas os últimos X pontos)
      if (history.cpu.length > this.maxDataPoints) {
        history.cpu.shift();
        history.ram.shift();
        history.temp.shift();
      }
      
      // Redesenha os gráficos apenas se for o dispositivo atual
      if (this.$refs.cpuCanvas && deviceId === this.currentDeviceId) {
        this.drawChart(this.$refs.cpuCanvas, this.cpuHistory, '#3b82f6', 100);
        this.drawChart(this.$refs.ramCanvas, this.ramHistory, '#10b981', this.maxRamValue);
        this.drawChart(this.$refs.tempCanvas, this.tempHistory, '#ef4444', 100);
      }
    },
    drawChart(canvas, data, color, maxValue) {
      if (!canvas) return;
      
      const ctx = canvas.getContext('2d');
      const width = canvas.width;
      const height = canvas.height;
      const padding = 40;
      const chartWidth = width - padding * 2;
      const chartHeight = height - padding * 2;
      
      // Limpa o canvas
      ctx.clearRect(0, 0, width, height);
      
      // Desenha o fundo
      ctx.fillStyle = '#f9fafb';
      ctx.fillRect(0, 0, width, height);
      
      // Desenha linhas de grade
      ctx.strokeStyle = '#e5e7eb';
      ctx.lineWidth = 1;
      
      // Linhas horizontais
      for (let i = 0; i <= 4; i++) {
        const y = padding + (chartHeight / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();
        
        // Labels do eixo Y
        ctx.fillStyle = '#6b7280';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'right';
        const value = maxValue - (maxValue / 4) * i;
        ctx.fillText(value.toFixed(0), padding - 5, y + 4);
      }
      
      // Desenha a linha do gráfico
      if (data.length > 1) {
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        data.forEach((value, index) => {
          const x = padding + (chartWidth / (this.maxDataPoints - 1)) * index;
          const y = padding + chartHeight - (value / maxValue) * chartHeight;
          
          if (index === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        });
        
        ctx.stroke();
        
        // Desenha área preenchida
        ctx.lineTo(width - padding, padding + chartHeight);
        ctx.lineTo(padding, padding + chartHeight);
        ctx.closePath();
        
        const gradient = ctx.createLinearGradient(0, padding, 0, height - padding);
        gradient.addColorStop(0, color + '40');
        gradient.addColorStop(1, color + '00');
        ctx.fillStyle = gradient;
        ctx.fill();
      }
      
      // Desenha borda do gráfico
      ctx.strokeStyle = '#d1d5db';
      ctx.lineWidth = 1;
      ctx.strokeRect(padding, padding, chartWidth, chartHeight);
    },
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
