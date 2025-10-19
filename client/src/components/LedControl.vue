<script setup lang="ts">

</script>

<template>
  <button @click="toggleLed" :disabled="loading">
    {{ ledOn ? "Desligar LED" : "Ligar LED" }} 
  <button>

</template>
