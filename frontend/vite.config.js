import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      // 将所有以 /api 开头的请求，代理到后端的 8000 端口
      '/api': {
        target: 'http://127.0.0.1:8000', // 这是您 FastAPI 后端的地址
        changeOrigin: true, // 必须设置为 true
      }
    }
  }
})