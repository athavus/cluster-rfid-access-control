<template>
  <div v-if="show" class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg p-6 w-full max-w-md">
      <h3 class="text-lg font-semibold mb-2">Nomear nova Tag</h3>
      <p class="text-sm text-gray-600 mb-4">UID: {{ uid }} • Fecha em {{ countdown }}s</p>
      <input 
        type="text" 
        v-model.trim="tagName" 
        class="w-full border rounded px-3 py-2 mb-4" 
        placeholder="Nome da tag"
        @keyup.enter="handleSubmit"
      />
      <div class="flex justify-end gap-2">
        <button @click="$emit('cancel')" class="px-3 py-1 border rounded">Cancelar</button>
        <button @click="handleSubmit" class="px-3 py-1 bg-blue-600 text-white rounded">Salvar</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue';

export default {
  name: 'RfidNameModal',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    uid: {
      type: String,
      default: null
    },
    countdown: {
      type: Number,
      default: 15
    }
  },
  emits: ['submit', 'cancel'],
  setup(props, { emit }) {
    const tagName = ref('');

    watch(() => props.show, (newVal) => {
      if (newVal) {
        tagName.value = '';
      }
    });

    const handleSubmit = () => {
      if (tagName.value.trim()) {
        emit('submit', tagName.value.trim());
      }
    };

    return {
      tagName,
      handleSubmit
    };
  }
};
</script>

