import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    host: '0.0.0.0', // 允许通过 IP 访问
    proxy: {
      '/douyin': 'http://127.0.0.1:5555',
      '/files': 'http://127.0.0.1:5555',
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
})
