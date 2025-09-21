import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

// 路由配置
const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '仪表板', requiresAuth: true }
  },
  {
    path: '/nodes',
    name: 'Nodes',
    component: () => import('@/views/Nodes.vue'),
    meta: { title: '节点管理', requiresAuth: true }
  },
  {
    path: '/subscriptions',
    name: 'Subscriptions',
    component: () => import('@/views/Subscriptions.vue'),
    meta: { title: '订阅管理', requiresAuth: true }
  },
  {
    path: '/output',
    name: 'Output',
    component: () => import('@/views/Output.vue'),
    meta: { title: '输出配置', requiresAuth: true }
  },
  {
    path: '/monitoring',
    name: 'Monitoring',
    component: () => import('@/views/Monitoring.vue'),
    meta: { title: '监控检测', requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: '系统设置', requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { title: '个人资料', requiresAuth: true }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '页面不存在' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  
  // 初始化用户状态（如果还没有初始化）
  if (!userStore.user && userStore.token) {
    await userStore.init()
  }
  
  // 检查是否需要验证
  if (to.meta.requiresAuth !== false) {
    if (!userStore.isLoggedIn) {
      // 未登录则跳转到登录页
      next('/login')
      return
    }
  } else if (to.path === '/login' && userStore.isLoggedIn) {
    // 已登录则跳转到仪表板
    next('/dashboard')
    return
  }
  
  next()
})

export default router