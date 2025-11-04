<template>
  <div class="mb-6 max-w-md p-4 rounded-md bg-green-50">
    <h3 class="font-semibold text-green-700 mb-2">LED Externo</h3>
    <p>
      Status:
      <span :class="ledStatusClasses(ledStatus)">
        {{ ledStatus ? 'ON' : 'OFF' }}
      </span>
    </p>
    <p>Última atualização: {{ formatDate(lastUpdate) }}</p>

    <div class="mt-3">
      <label class="block text-sm text-green-900 mb-1">Pino GPIO (BCM) do LED externo</label>
      <input
        type="number"
        class="w-32 px-2 py-1 border rounded"
        :min="0"
        :max="27"
        :value="pin"
        @input="$emit('update:pin', parseInt($event.target.value) || 0)"
      />
    </div>

    <div class="mt-3">
      <label class="block text-sm text-green-900 mb-1">IP do dispositivo alvo (ex.: 192.168.130.166)</label>
      <input
        type="text"
        class="w-64 px-2 py-1 border rounded"
        placeholder="192.168.130.166"
        :value="targetHost"
        @input="$emit('update:targetHost', $event.target.value)"
      />
      <p class="mt-1 text-xs text-green-700">Somente LED usa este IP. Porta 8000 será assumida se omitida.</p>
    </div>

    <div class="mt-4 flex gap-4">
      <button
        @click="$emit('toggle-led', 'ON')"
        :disabled="loading"
        class="flex-1 py-2.5 bg-green-500 hover:bg-green-600 text-white font-semibold rounded-lg transition-all hover:scale-105 active:scale-95"
      >
        Ligar
      </button>
      <button
        @click="$emit('toggle-led', 'OFF')"
        :disabled="loading"
        class="flex-1 py-2.5 bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg transition-all hover:scale-105 active:scale-95"
      >
        Desligar
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ExternalLedControl',
  props: {
    ledStatus: {
      type: Boolean,
      default: false
    },
    lastUpdate: {
      type: String,
      default: null
    },
    pin: {
      type: Number,
      default: 17
    },
    targetHost: {
      type: String,
      default: ''
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:pin', 'update:targetHost', 'toggle-led'],
  methods: {
    formatDate(dateStr) {
      if (!dateStr) return 'N/A';
      return new Date(dateStr).toLocaleString('pt-BR');
    },
    ledStatusClasses(statusBoolean) {
      return statusBoolean ? 'text-green-600 font-semibold' : 'text-gray-500 font-normal';
    }
  }
};
</script>

