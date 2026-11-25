import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Backend (backend/main.py) runs on 8020; /api is proxied so the browser never sees CORS.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8020',
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8020',
        changeOrigin: true,
      },
    },
  },
});
