<template>
  <div v-if="show" class="fixed top-20 right-4 bg-blue-600 text-white px-4 py-2 rounded shadow-lg z-50">
    {{ message }}
  </div>
</template>

<script>
export default {
  name: 'RfidBanner',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    message: {
      type: String,
      default: ''
    }
  }
};
</script>

