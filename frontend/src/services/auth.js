// =============================================================================
// Auth Service - интеграция с реальным API
// =============================================================================

// API URL читается из глобальной переменной установленной в index.html
// Используем Function constructor чтобы Rollup не мог оптимизировать
function getApi() {
  // eslint-disable-next-line no-new-func
  const getUrl = new Function('return window.__API_URL__')
  return getUrl() || '/api'
}

const TOKEN_KEY = 'warehouse_auth_token'
const USER_KEY = 'warehouse_user'

/**
 * Авторизация пользователя через API
 */
export async function login(username, password) {
  try {
    const response = await fetch(`${getApi()}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })

    if (!response.ok) {
      const error = await response.json()
      return { success: false, error: error.error || 'Ошибка авторизации' }
    }

    const data = await response.json()
    
    // Сохраняем токен и данные пользователя
    localStorage.setItem(TOKEN_KEY, data.token)
    localStorage.setItem(USER_KEY, JSON.stringify({
      username: data.username,
      fullName: data.fullName,
      role: data.role
    }))

    return { success: true, user: data }
  } catch (error) {
    console.error('Login error:', error)
    return { success: false, error: 'Ошибка подключения к серверу' }
  }
}

/**
 * Выход из системы
 */
export function logout() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

/**
 * Проверка авторизации
 */
export function isAuthenticated() {
  const token = localStorage.getItem(TOKEN_KEY)
  if (!token) return false

  try {
    // Проверяем срок действия токена (JWT payload)
    const payload = JSON.parse(atob(token.split('.')[1]))
    if (payload.exp && payload.exp * 1000 < Date.now()) {
      logout()
      return false
    }
    return true
  } catch {
    return false
  }
}

/**
 * Получение текущего пользователя
 */
export function getCurrentUser() {
  const userStr = localStorage.getItem(USER_KEY)
  if (!userStr) return null

  try {
    return JSON.parse(userStr)
  } catch {
    return null
  }
}

/**
 * Получение токена
 */
export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

/**
 * Проверка роли пользователя
 */
export function hasRole(roles) {
  const user = getCurrentUser()
  if (!user) return false

  const userRole = user.role.replace('ROLE_', '')
  
  if (Array.isArray(roles)) {
    return roles.includes(userRole)
  }
  return userRole === roles
}

/**
 * Проверка доступа к функции по ролевой модели
 */
export function canAccess(feature) {
  const user = getCurrentUser()
  if (!user) return false

  const role = user.role.replace('ROLE_', '')

  const permissions = {
    // Статус системы - только SUPER_USER и ADMIN
    'system-status': ['SUPER_USER', 'ADMIN'],
    
    // Управление пользователями - только SUPER_USER и ADMIN
    'user-management': ['SUPER_USER', 'ADMIN'],
    
    // Просмотр товаров - все
    'view-products': ['SUPER_USER', 'ADMIN', 'MANAGER', 'EMPLOYEE'],
    
    // Редактирование товаров - только SUPER_USER и EMPLOYEE
    'edit-products': ['SUPER_USER', 'EMPLOYEE'],
    
    // Отчёты - SUPER_USER, ADMIN, MANAGER
    'view-reports': ['SUPER_USER', 'ADMIN', 'MANAGER'],

    // Аналитика - SUPER_USER, ADMIN, MANAGER, ANALYST (WH-121)
    'view-analytics': ['SUPER_USER', 'ADMIN', 'MANAGER', 'ANALYST']
  }

  const allowedRoles = permissions[feature]
  return allowedRoles ? allowedRoles.includes(role) : false
}

/**
 * Заголовки авторизации для fetch
 */
export function getAuthHeaders() {
  const token = getToken()
  return token ? { 'Authorization': `Bearer ${token}` } : {}
}

/**
 * Fetch с авторизацией
 */
export async function authFetch(url, options = {}) {
  const headers = {
    ...options.headers,
    ...getAuthHeaders()
  }

  const response = await fetch(url, { ...options, headers })

  // Если 401 - разлогиниваем
  if (response.status === 401) {
    logout()
    window.location.href = '/login'
    throw new Error('Session expired')
  }

  return response
}

export default {
  login,
  logout,
  isAuthenticated,
  getCurrentUser,
  getToken,
  hasRole,
  canAccess,
  getAuthHeaders,
  authFetch
}
