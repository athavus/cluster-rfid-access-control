<template>
  <div v-if="error" class="fixed bottom-4 right-4 bg-red-600 text-white px-4 py-2 rounded shadow-lg z-50">
    {{ error }}
    <button @click="$emit('dismiss')" class="ml-4 font-bold">×</button>
  </div>
</template>

<script>
export default {
  name: 'ErrorBanner',
  props: {
    error: {
      type: String,
      default: null
    }
  },
  emits: ['dismiss']
};
</script>

