<template>
  <div class="login-page">
    <div class="login-container">
      <!-- Логотип и заголовок -->
      <div class="login-header">
        <div class="logo"><svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008Zm0 3h.008v.008h-.008v-.008Zm0 3h.008v.008h-.008v-.008Z"/></svg></div>
        <h1>Warehouse</h1>
        <p class="subtitle">Система управления складом</p>
      </div>

      <!-- Форма входа -->
      <form class="login-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">
            <span class="icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0; vertical-align: middle;"><path d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z"/></svg></span>
            Имя пользователя
          </label>
          <input
            id="username"
            v-model="username"
            type="text"
            placeholder="Введите логин..."
            required
            :disabled="loading"
            autocomplete="username"
            data-testid="username"
          >
        </div>

        <div class="form-group">
          <label for="password">
            <span class="icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0; vertical-align: middle;"><path d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z"/></svg></span>
            Пароль
          </label>
          <div class="password-input">
            <input
              id="password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="Введите пароль..."
              required
              :disabled="loading"
              autocomplete="current-password"
              data-testid="password"
            >
            <button
              type="button"
              class="toggle-password"
              :disabled="loading"
              @click="showPassword = !showPassword"
            >
              <svg v-if="showPassword" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.451 10.451 0 0 1 12 4.5c4.756 0 8.773 3.162 10.065 7.498a10.522 10.522 0 0 1-4.293 5.774M6.228 6.228 3 3m3.228 3.228 3.65 3.65m7.894 7.894L21 21m-3.228-3.228-3.65-3.65m0 0a3 3 0 1 0-4.243-4.243m4.242 4.242L9.88 9.88"/></svg>
              <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z"/><path d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"/></svg>
            </button>
          </div>
        </div>

        <!-- Сообщение об ошибке -->
        <div v-if="error" class="error-message" data-testid="error-message">
          <span class="icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0; vertical-align: middle;"><path d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"/></svg></span>
          {{ error }}
        </div>

        <!-- Кнопка входа -->
        <button type="submit" class="login-btn" :disabled="loading" data-testid="login-button">
          <span v-if="loading" class="spinner" />
          {{ loading ? 'Вход...' : 'Войти в систему' }}
        </button>
      </form>

      <!-- Футер -->
      <div class="login-footer">
        <p>DevOps Home Lab © 2025</p>
      </div>
    </div>
  </div>
</template>

<script>
import auth from '../services/auth'
import { useFacilityStore } from '../stores/facility'

// API URL
function getApi() {
  // eslint-disable-next-line no-new-func
  const getUrl = new Function('return window.__API_URL__')
  return getUrl() || '/api'
}

export default {
  name: 'LoginPage',

  data() {
    return {
      username: '',
      password: '',
      showPassword: false,
      loading: false,
      error: null
    }
  },

  // Если уже авторизован — редирект на главную
  created() {
    if (auth.isAuthenticated()) {
      this.$router.push('/')
    }
  },

  methods: {
    async handleLogin() {
      this.error = null
      this.loading = true

      try {
        const result = await auth.login(this.username, this.password)

        if (result.success) {
          // Небольшая задержка для гарантии синхронизации localStorage
          await new Promise(resolve => setTimeout(resolve, 50))

          // Получить полную информацию о пользователе
          const userInfo = await this.fetchUserInfo()

          // Если у пользователя есть привязанный facility
          if (userInfo && userInfo.facilityId && userInfo.facilityType) {
            const facilityStore = useFacilityStore()
            // Установить facility в store
            facilityStore.setCurrentFacility({
              id: userInfo.facilityId,
              code: userInfo.facilityCode || `${userInfo.facilityType}-${userInfo.facilityId}`,
              name: userInfo.facilityName || 'Объект',
              type: userInfo.facilityType
            })

            // Redirect на dashboard по типу facility
            const dashboardRoutes = {
              DC: '/dc',
              WH: '/wh',
              PP: '/pp'
            }
            const targetRoute = dashboardRoutes[userInfo.facilityType] || '/'
            this.$router.push(targetRoute)
          } else {
            // Нет привязанного facility — на главную
            const redirect = this.$route.query.redirect || '/'
            this.$router.push(redirect)
          }
        } else {
          this.error = result.error
        }
      } catch (err) {
        this.error = 'Ошибка подключения к серверу'
        console.error('Login error:', err)
      } finally {
        this.loading = false
      }
    },

    async fetchUserInfo() {
      try {
        const token = localStorage.getItem('warehouse_auth_token')
        const response = await fetch(`${getApi()}/auth/me`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          return await response.json()
        }
      } catch (err) {
        console.error('Failed to fetch user info:', err)
      }
      return null
    },

  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  padding: 1rem;
}

.login-container {
  width: 100%;
  max-width: 420px;
  min-height: calc(100vh - 2rem);
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 2.5rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.logo {
  margin-bottom: 0.5rem;
  color: #00d4ff;
}

.login-header h1 {
  font-size: 2rem;
  color: #fff;
  margin: 0 0 0.5rem 0;
  background: linear-gradient(90deg, #00d4ff, #7b2cbf);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  color: #888;
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  color: #ccc;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.form-group label .icon {
  font-size: 1rem;
}

.form-group input {
  width: 100%;
  padding: 0.875rem 1rem;
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: #fff;
  font-size: 1rem;
  transition: all 0.3s;
  box-sizing: border-box;
}

.form-group input::placeholder {
  color: #666;
}

.form-group input:focus {
  outline: none;
  border-color: #00d4ff;
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
}

.form-group input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.password-input {
  position: relative;
  display: flex;
}

.password-input input {
  padding-right: 3rem;
}

.toggle-password {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  opacity: 0.7;
  transition: opacity 0.2s;
  color: #ccc;
  display: flex;
  align-items: center;
}

.toggle-password:hover {
  opacity: 1;
}

.toggle-password:disabled {
  cursor: not-allowed;
}

.error-message {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  color: #f87171;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.login-btn {
  width: 100%;
  padding: 1rem;
  background: linear-gradient(135deg, #00d4ff, #7b2cbf);
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(0, 212, 255, 0.3);
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.login-footer {
  margin-top: auto;
  padding-top: 2rem;
  text-align: center;
}

.login-footer p {
  color: #555;
  font-size: 0.8rem;
  margin: 0;
}

@media (max-width: 480px) {
  .login-container {
    padding: 1.5rem;
    min-height: calc(100vh - 2rem);
  }

  .logo svg {
    width: 48px;
    height: 48px;
  }

  .login-header h1 {
    font-size: 1.5rem;
  }
}
</style>
