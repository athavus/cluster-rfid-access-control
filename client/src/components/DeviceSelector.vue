<template>
  <section class="col-span-1 bg-white rounded-lg shadow p-4 overflow-auto max-h-[calc(100vh-128px)]">
    <h2 class="font-semibold text-gray-800 mb-4">Dispositivos</h2>
    <ul class="space-y-2">
      <li v-for="device in devices" :key="device.raspberry_id">
        <button
          @click="$emit('select-device', device.raspberry_id)"
          type="button"
          class="w-full text-left px-4 py-2 rounded-md cursor-pointer transition-colors"
          :class="selectedDeviceId === device.raspberry_id ? 'bg-blue-500 text-white' : 'hover:bg-blue-50 text-gray-700'"
        >
          Raspberry ID: {{ device.raspberry_id }}
        </button>
      </li>
    </ul>
  </section>
</template>

<script>
export default {
  name: 'DeviceSelector',
  props: {
    devices: {
      type: Array,
      required: true
    },
    selectedDeviceId: {
      type: [String, Number],
      default: null
    }
  },
  emits: ['select-device']
};
</script>

