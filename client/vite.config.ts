import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    strictPort: true, // Se a porta estiver ocupada, falha em vez de usar outra
    open: 'true'
  },
  css : {
    postcss: './postcss.config.js'
  }
})
