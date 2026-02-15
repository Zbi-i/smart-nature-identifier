import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// --- 新增：引入 Element Plus 及其样式 ---
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// 引入所有图标
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

const app = createApp(App)

app.use(createPinia())
app.use(router)

// --- 新增：注册 Element Plus ---
app.use(ElementPlus)

// --- 新增：注册所有图标 ---
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')
