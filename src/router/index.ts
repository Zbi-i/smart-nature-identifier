import { createRouter, createWebHistory } from 'vue-router'
// 如果你没有 HomeView，我们直接让它什么都不做，或者指向 App 的一部分
// 但在你的单页应用里，最简单的消除警告的方法是：

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../App.vue') // 暂时指向 App.vue 防止警告
    }
  ]
})

export default router
