import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
    // 关键配置 1：强制去重
    // 这告诉 Vite："不管有多少个地方引用了 tfjs，都只给我用同一个副本"
    // 这完美解决了 backend undefined 的报错
    dedupe: ['@tensorflow/tfjs']
  },
  optimizeDeps: {
    // 关键配置 2：强制预构建
    // 这告诉 Vite："把 tfjs 打包成一个大文件，不要拆成几千个小文件"
    // 这完美解决了 net::ERR_BLOCKED_BY_CLIENT 和白屏问题
    include: ['@tensorflow/tfjs', '@tensorflow-models/mobilenet']
  },
  build: {
    commonjsOptions: {
      transformMixedEsModules: true
    }
  }
})
