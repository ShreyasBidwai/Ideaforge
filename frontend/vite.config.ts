import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    target: 'es2020',
    reportCompressedSize: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('react') || id.includes('react-dom')) {
              return 'vendor';
            }
            if (id.includes('react-router') || id.includes('react-router-dom')) {
              return 'router';
            }
            if (id.includes('framer-motion') || id.includes('lucide-react')) {
              return 'ui-libs';
            }
          }
        }
      }
    }
  }
})
