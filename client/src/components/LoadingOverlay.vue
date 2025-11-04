<template>
  <div v-if="loading" class="fixed inset-0 bg-white bg-opacity-80 flex items-center justify-center z-50">
    <svg class="animate-spin h-12 w-12 text-gray-700" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
    </svg>
  </div>
</template>

<script>
export default {
  name: 'LoadingOverlay',
  props: {
    loading: {
      type: Boolean,
      required: true
    }
  }
};
</script>

