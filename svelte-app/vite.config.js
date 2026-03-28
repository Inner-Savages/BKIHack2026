import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  server: {
    allowedHosts: ['mobywatel.baumg.art'],
    proxy: {
      // Wszystkie requesty /api/* → backend FastAPI na :8000
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  preview: {
    allowedHosts: ['mobywatel.baumg.art'],
  },
});
