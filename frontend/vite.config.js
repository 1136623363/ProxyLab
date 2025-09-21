import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// 从配置文件读取配置
const FRONTEND_PORT = process.env.VITE_DEV_SERVER_PORT || 3000
const BACKEND_PORT = process.env.VITE_BACKEND_PORT || 8001
const BACKEND_HOST = process.env.VITE_BACKEND_HOST || 'localhost'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: parseInt(FRONTEND_PORT),
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: `http://${BACKEND_HOST}:${BACKEND_PORT}`,
        changeOrigin: true,
        secure: false
      },
      '/auth': {
        target: `http://${BACKEND_HOST}:${BACKEND_PORT}`,
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false
  }
})
