<template>
  <Transition name="modal">
    <div v-if="show" class="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-[100] p-4" @click.self="$emit('close')">
      <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full transform transition-all ring-4 ring-blue-400 ring-opacity-50">
        <!-- Header com ícone e animação -->
        <div class="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6 rounded-t-2xl text-center relative overflow-hidden">
          <div class="absolute inset-0 bg-white opacity-10 animate-pulse"></div>
          <div class="relative z-10">
            <!-- Ícone RFID com animação -->
            <div class="mx-auto mb-4 w-20 h-20 bg-white bg-opacity-20 rounded-full flex items-center justify-center animate-bounce">
              <svg class="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"></path>
              </svg>
            </div>
            <h2 class="text-2xl font-bold mb-2">Tag RFID Detectada!</h2>
            <div class="w-24 h-1 bg-white mx-auto rounded-full"></div>
          </div>
        </div>

        <!-- Conteúdo do modal -->
        <div class="p-6">
          <!-- Nome da Tag (se existir) -->
          <div v-if="tagName && tagName !== '<Sem nome>'" class="mb-6 text-center">
            <p class="text-sm text-gray-500 mb-1 uppercase tracking-wide font-semibold">Nome</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{{ tagName }}</p>
          </div>

          <!-- Mensagem quando não tem nome -->
          <div v-else class="mb-4 text-center">
            <p class="text-sm text-amber-600 bg-amber-50 px-3 py-2 rounded-lg inline-block font-medium">
              Tag não nomeada
            </p>
          </div>

          <!-- UID da Tag -->
          <div class="mb-6 text-center">
            <p class="text-sm text-gray-500 mb-2 uppercase tracking-wide font-semibold">Tag UID</p>
            <div class="bg-gray-100 rounded-lg p-4 border-2 border-blue-200 hover:border-blue-300 transition-colors">
              <p class="text-xl font-mono font-semibold text-gray-800 break-all select-all">{{ uid }}</p>
            </div>
          </div>

          <!-- Timestamp (opcional) -->
          <div class="text-center text-xs text-gray-400 mb-4">
            <span class="inline-flex items-center gap-1">
              <span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              Detectado agora
            </span>
          </div>

          <!-- Botão de fechar -->
          <button 
            @click="$emit('close')" 
            class="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-all hover:scale-105 active:scale-95 shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  </Transition>
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
    },
    uid: {
      type: String,
      default: ''
    },
    tagName: {
      type: String,
      default: null
    }
  },
  emits: ['close']
};
</script>

<style scoped>
.modal-enter-active, .modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from, .modal-leave-to {
  opacity: 0;
}

.modal-enter-active .bg-white, .modal-leave-active .bg-white {
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s ease;
}

.modal-enter-from .bg-white, .modal-leave-to .bg-white {
  transform: scale(0.7) translateY(-20px);
  opacity: 0;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.1;
  }
  50% {
    opacity: 0.2;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

.animate-bounce {
  animation: bounce 1s infinite;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(-5%);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  50% {
    transform: translateY(0);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
}
</style>

