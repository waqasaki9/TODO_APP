import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const api = env.VITE_API_URL || 'http://localhost:8000'
  const ws = (env.VITE_WS_URL || api.replace(/^http/, 'ws'))

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: api,
          changeOrigin: true,
        },
        '/ws': {
          target: ws,
          ws: true,
        },
      },
    },
  }
})
