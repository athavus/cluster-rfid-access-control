<template>
  <section
    v-if="deviceDetails"
    class="col-span-3 bg-white rounded-lg shadow p-6 overflow-auto max-h-[calc(100vh-128px)]"
  >
    <h2 class="text-lg font-semibold mb-4">Detalhes do Dispositivo: {{ deviceId }}</h2>

    <ExternalLedControl
      :led-status="deviceDetails.led_external_status"
      :last-update="deviceDetails.last_update"
      :pin="externalLedPin"
      :target-host="targetHost"
      :loading="loading"
      @update:pin="$emit('update:externalLedPin', $event)"
      @update:targetHost="$emit('update:targetHost', $event)"
      @toggle-led="$emit('toggle-led', $event)"
    />

    <DeviceStatusGrid 
      :device-details="deviceDetails" 
      :show-rfid-banner="showRfidBanner"
    />
  </section>
</template>

<script>
import ExternalLedControl from './ExternalLedControl.vue';
import DeviceStatusGrid from './DeviceStatusGrid.vue';

export default {
  name: 'DeviceDetails',
  components: {
    ExternalLedControl,
    DeviceStatusGrid
  },
  props: {
    deviceDetails: {
      type: Object,
      default: null
    },
    deviceId: {
      type: [String, Number],
      default: null
    },
    externalLedPin: {
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
    },
    showRfidBanner: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:externalLedPin', 'update:targetHost', 'toggle-led']
};
</script>

