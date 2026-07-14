import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  root: 'src/frontend',
  plugins: [react()],
  build: {
    outDir: '../../dist/client',
    emptyOutDir: true,
  },
  server: {
    port: 3000,
    proxy: {
      // The frontend source directory is also named `api`, so Vite serves modules
      // such as /api/client.ts. Proxy only extensionless backend API requests.
      '^/api/(?!.*\\.(?:ts|tsx)$)': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
