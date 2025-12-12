import { createRouter, createWebHistory } from 'vue-router'
import auth from '../services/auth'

import HomePage from '../components/HomePage.vue'
import AddProductPage from '../components/AddProductPage.vue'
import LoginPage from '../components/LoginPage.vue'
const StatusPage = () => import('../components/StatusPage.vue')
const AnalyticsPage = () => import('../components/AnalyticsPage.vue')

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginPage,
    meta: { requiresAuth: false, title: 'Вход в систему' }
  },
  {
    path: '/',
    name: 'Home',
    component: HomePage,
    meta: {
      requiresAuth: true,
      title: 'Продукты'
    }
  },
  {
    path: '/add',
    name: 'AddProduct',
    component: AddProductPage,
    meta: {
      requiresAuth: true,
      requiredPermission: 'edit-products',
      title: 'Добавить продукт'
    }
  },
  {
    path: '/status',
    name: 'Status',
    component: StatusPage,
    meta: {
      requiresAuth: true,
      requiredRoles: ['SUPER_USER', 'ADMIN'],
      title: 'Статус системы'
    }
  },
  {
    path: '/analytics',
    name: 'Analytics',
    component: AnalyticsPage,
    meta: {
      requiresAuth: true,
      requiredRoles: ['SUPER_USER', 'ADMIN', 'MANAGER', 'ANALYST'],
      title: 'Аналитика'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation Guard
router.beforeEach((to, from, next) => {
  const requiresAuth = to.meta.requiresAuth !== false
  const requiredRoles = to.meta.requiredRoles
  const isAuthenticated = auth.isAuthenticated()

  document.title = to.meta.title ? `${to.meta.title} | Warehouse` : 'Warehouse'

  // Не авторизован — на логин
  if (requiresAuth && !isAuthenticated) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  // Проверка ролей
  if (requiredRoles && !auth.hasRole(requiredRoles)) {
    // Нет доступа — на главную
    next({ path: '/' })
    return
  }

  // Уже залогинен и идёт на логин — на главную
  if (to.path === '/login' && isAuthenticated) {
    next('/')
    return
  }

  next()
})

export default router
