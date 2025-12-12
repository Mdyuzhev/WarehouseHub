import { createRouter, createWebHistory } from 'vue-router'
import auth from '../services/auth'
import { useFacilityStore } from '../stores/facility'

import HomePage from '../components/HomePage.vue'
import AddProductPage from '../components/AddProductPage.vue'
import LoginPage from '../components/LoginPage.vue'
const StatusPage = () => import('../components/StatusPage.vue')
const AnalyticsPage = () => import('../components/AnalyticsPage.vue')

// DC views
const DCDashboard = () => import('../views/dc/DCDashboard.vue')
const DCReceiptsList = () => import('../views/dc/DCReceiptsList.vue')
const DCReceiptCreate = () => import('../views/dc/DCReceiptCreate.vue')
const DCReceiptDetail = () => import('../views/dc/DCReceiptDetail.vue')
const DCShipmentsList = () => import('../views/dc/DCShipmentsList.vue')
const DCShipmentCreate = () => import('../views/dc/DCShipmentCreate.vue')
const DCShipmentDetail = () => import('../views/dc/DCShipmentDetail.vue')

// WH views
const WHDashboard = () => import('../views/wh/WHDashboard.vue')
const WHReceiptsList = () => import('../views/wh/WHReceiptsList.vue')
const WHReceiptDetail = () => import('../views/wh/WHReceiptDetail.vue')
const WHShipmentsList = () => import('../views/wh/WHShipmentsList.vue')
const WHShipmentCreate = () => import('../views/wh/WHShipmentCreate.vue')
const WHShipmentDetail = () => import('../views/wh/WHShipmentDetail.vue')
const WHStockList = () => import('../views/wh/WHStockList.vue')
const WHInventory = () => import('../views/wh/WHInventory.vue')

// PP views
const PPDashboard = () => import('../views/pp/PPDashboard.vue')
const PPReceiptsList = () => import('../views/pp/PPReceiptsList.vue')
const PPReceiptDetail = () => import('../views/pp/PPReceiptDetail.vue')
const PPIssuesList = () => import('../views/pp/PPIssuesList.vue')
const PPIssueCreate = () => import('../views/pp/PPIssueCreate.vue')
const PPIssueDetail = () => import('../views/pp/PPIssueDetail.vue')
const PPStockList = () => import('../views/pp/PPStockList.vue')

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
  // DC routes
  {
    path: '/dc',
    name: 'DCDashboard',
    component: DCDashboard,
    meta: {
      requiresAuth: true,
      requiredFacilityType: 'DC',
      title: 'DC Dashboard'
    }
  },
  {
    path: '/dc/receipts',
    name: 'DCReceiptsList',
    component: DCReceiptsList,
    meta: {
      requiresAuth: true,
      requiredFacilityType: 'DC',
      title: 'DC Receipts'
    }
  },
  {
    path: '/dc/receipts/create',
    name: 'DCReceiptCreate',
    component: DCReceiptCreate,
    meta: {
      requiresAuth: true,
      requiredFacilityType: 'DC',
      title: 'Create Receipt'
    }
  },
  {
    path: '/dc/receipts/:id',
    name: 'DCReceiptDetail',
    component: DCReceiptDetail,
    meta: {
      requiresAuth: true,
      requiredFacilityType: 'DC',
      title: 'Receipt Detail'
    }
  },
  {
    path: '/dc/shipments',
    name: 'DCShipmentsList',
    component: DCShipmentsList,
    meta: {
      requiresAuth: true,
      requiredFacilityType: 'DC',
      title: 'DC Shipments'
    }
  },
  {
    path: '/dc/shipments/create',
    name: 'DCShipmentCreate',
    component: DCShipmentCreate,
    meta: {
      requiresAuth: true,
      requiredFacilityType: 'DC',
      title: 'Create Shipment'
    }
  },
  {
    path: '/dc/shipments/:id',
    name: 'DCShipmentDetail',
    component: DCShipmentDetail,
    meta: {
      requiresAuth: true,
      requiredFacilityType: 'DC',
      title: 'Shipment Detail'
    }
  },
  // WH routes
  {
    path: '/wh',
    name: 'WHDashboard',
    component: WHDashboard,
    meta: {
      requiresAuth: true,
      requiredFacilityType: 'WH',
      title: 'WH Dashboard'
    }
  },
  {
    path: '/wh/receipts',
    name: 'WHReceiptsList',
    component: WHReceiptsList,
    meta: {
      requiresAuth: true,
      requiredFacilityType: 'WH',
      title: 'WH Receipts'
    }
  },
  {
    path: '/wh/receipts/:id',
    name: 'WHReceiptDetail',
    component: WHReceiptDetail,
    meta: {
      requiresAuth: true,
      requiredFacilityType: 'WH',
      title: 'Receipt Detail'
    }
  },
  {
    path: '/wh/shipments',
    name: 'WHShipmentsList',
    component: WHShipmentsList,
    meta: {
      requiresAuth: true,
      requiredFacilityType: 'WH',
      title: 'WH Shipments'
    }
  },
  {
    path: '/wh/shipments/create',
    name: 'WHShipmentCreate',
    component: WHShipmentCreate,
    meta: {
      requiresAuth: true,
      requiredFacilityType: 'WH',
      title: 'Create Shipment'
    }
  },
  {
    path: '/wh/shipments/:id',
    name: 'WHShipmentDetail',
    component: WHShipmentDetail,
    meta: {
      requiresAuth: true,
      requiredFacilityType: 'WH',
      title: 'Shipment Detail'
    }
  },
  {
    path: '/wh/stock',
    name: 'WHStockList',
    component: WHStockList,
    meta: {
      requiresAuth: true,
      requiredFacilityType: 'WH',
      title: 'WH Stock'
    }
  },
  {
    path: '/wh/inventory',
    name: 'WHInventory',
    component: WHInventory,
    meta: {
      requiresAuth: true,
      requiredFacilityType: 'WH',
      title: 'Inventory Count'
    }
  },
  // PP routes
  {
    path: '/pp',
    name: 'PPDashboard',
    component: PPDashboard,
    meta: {
      requiresAuth: true,
      requiredFacilityType: 'PP',
      title: 'PP Dashboard'
    }
  },
  {
    path: '/pp/receipts',
    name: 'PPReceiptsList',
    component: PPReceiptsList,
    meta: {
      requiresAuth: true,
      requiredFacilityType: 'PP',
      title: 'PP Receipts'
    }
  },
  {
    path: '/pp/receipts/:id',
    name: 'PPReceiptDetail',
    component: PPReceiptDetail,
    meta: {
      requiresAuth: true,
      requiredFacilityType: 'PP',
      title: 'Receipt Detail'
    }
  },
  {
    path: '/pp/issues',
    name: 'PPIssuesList',
    component: PPIssuesList,
    meta: {
      requiresAuth: true,
      requiredFacilityType: 'PP',
      title: 'PP Issues'
    }
  },
  {
    path: '/pp/issues/create',
    name: 'PPIssueCreate',
    component: PPIssueCreate,
    meta: {
      requiresAuth: true,
      requiredFacilityType: 'PP',
      title: 'Create Issue'
    }
  },
  {
    path: '/pp/issues/:id',
    name: 'PPIssueDetail',
    component: PPIssueDetail,
    meta: {
      requiresAuth: true,
      requiredFacilityType: 'PP',
      title: 'Issue Detail'
    }
  },
  {
    path: '/pp/stock',
    name: 'PPStockList',
    component: PPStockList,
    meta: {
      requiresAuth: true,
      requiredFacilityType: 'PP',
      title: 'PP Stock'
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
  const requiredFacilityType = to.meta.requiredFacilityType
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

  // Проверка facility type
  if (requiredFacilityType) {
    const facilityStore = useFacilityStore()
    if (!facilityStore.hasFacility) {
      // Нет выбранного facility — на главную
      alert('Выберите объект для продолжения')
      next({ path: '/' })
      return
    }
    if (facilityStore.facilityType !== requiredFacilityType) {
      // Неправильный тип facility
      alert(`Этот раздел доступен только для ${requiredFacilityType}`)
      next({ path: '/' })
      return
    }
  }

  // Уже залогинен и идёт на логин — на главную
  if (to.path === '/login' && isAuthenticated) {
    next('/')
    return
  }

  next()
})

export default router
