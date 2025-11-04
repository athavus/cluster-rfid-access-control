<template>
  <header class="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
    <div class="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
      <h1 class="text-xl font-semibold text-gray-900">Raspberry Pi IoT Dashboard</h1>
      <div class="flex items-center gap-4">
        <button 
          @click="$emit('refresh')" 
          class="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md"
        >
          Atualizar
        </button>
        <button 
          @click="$emit('export-db')" 
          class="px-3 py-1 text-sm bg-blue-100 hover:bg-blue-200 rounded-md"
        >
          Exportar DB
        </button>
        <div class="flex items-center gap-2 text-sm font-medium">
          <span 
            class="inline-block w-3 h-3 rounded-full" 
            :class="isOnline ? 'bg-green-500' : 'bg-red-500'" 
            aria-label="Conexão"
          ></span>
          <span>{{ isOnline ? 'Online' : 'Offline' }}</span>
        </div>
      </div>
    </div>
  </header>
</template>

<script>
export default {
  name: 'DashboardHeader',
  props: {
    isOnline: {
      type: Boolean,
      default: true
    }
  },
  emits: ['refresh', 'export-db']
};
</script>

