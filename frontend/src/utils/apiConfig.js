// =============================================================================
// API Configuration - единая точка конфигурации API URL
// =============================================================================

/**
 * Определяет API URL в зависимости от окружения
 * Использует глобальную переменную window.__API_URL__ установленную в index.html
 * @returns {string} Base API URL
 */
export function getApiUrl() {
  // Приоритет 1: env переменная (для тестов)
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }

  // Runtime определение - ВСЕГДА читаем из глобальной переменной
  // Используем eval чтобы Rollup точно не смог оптимизировать
  // eslint-disable-next-line no-eval
  return eval('window.__API_URL__') || 'http://192.168.1.74:30080/api'
}

/**
 * Определяет URL для health check
 * @returns {string} Health endpoint URL
 */
export function getHealthUrl() {
  const apiUrl = getApiUrl()
  // Убираем /api в конце и добавляем /actuator/health
  // Используем slice вместо replace для надёжности
  if (apiUrl.endsWith('/api')) {
    return apiUrl.slice(0, -4) + '/actuator/health'
  }
  return apiUrl.replace(/\/api$/, '/actuator/health')
}

/**
 * Определяет базовый URL без /api
 * @returns {string} Base URL
 */
export function getBaseUrl() {
  const apiUrl = getApiUrl()
  // Используем slice вместо replace для надёжности
  if (apiUrl.endsWith('/api')) {
    return apiUrl.slice(0, -4)
  }
  return apiUrl.replace(/\/api$/, '')
}

export default {
  getApiUrl,
  getHealthUrl,
  getBaseUrl
}
