import { defineConfig } from 'vite'
// IMPORTANT: use the SWC plugin, not the default esbuild-based one
import react from '@vitejs/plugin-react-swc'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,     // so you can open from your laptop at http://<pi-ip>:5173
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000', // Flask on the same Pi
        changeOrigin: true
      }
    }
  },
  // Avoid esbuild pre-bundling in dev (this is what usually SIGILLs on Pi)
  optimizeDeps: {
    disabled: true
  },
  // Optional: for 'npm run build' to avoid esbuild minify
  build: {
    minify: 'terser'
  }
})
