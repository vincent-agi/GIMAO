// frontend/vitest.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true, // Permet d'utiliser describe, it, expect sans les importer
    setupFiles: ['./src/components/__tests__/setup.js'],
    env: {
      VUE_APP_BACKEND_BASE_URL: 'http://localhost:8000',
    },
    server: {
      deps: {
        inline: ['vuetify'],
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
