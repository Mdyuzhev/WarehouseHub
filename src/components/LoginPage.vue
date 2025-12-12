<template>
  <div class="login-page">
    <div class="login-container">
      <!-- Логотип и заголовок -->
      <div class="login-header">
        <div class="logo">🏭</div>
        <h1>Warehouse</h1>
        <p class="subtitle">Система управления складом</p>
      </div>

      <!-- Форма входа -->
      <form class="login-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">
            <span class="icon">👤</span>
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
            data-testid="username-input"
          >
        </div>

        <div class="form-group">
          <label for="password">
            <span class="icon">🔒</span>
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
              data-testid="password-input"
            >
            <button
              type="button"
              class="toggle-password"
              :disabled="loading"
              @click="showPassword = !showPassword"
            >
              {{ showPassword ? '🙈' : '👁️' }}
            </button>
          </div>
        </div>

        <!-- Сообщение об ошибке -->
        <div v-if="error" class="error-message" data-testid="error-message">
          <span class="icon">⚠️</span>
          {{ error }}
        </div>

        <!-- Кнопка входа -->
        <button type="submit" class="login-btn" :disabled="loading" data-testid="login-button">
          <span v-if="loading" class="spinner" />
          {{ loading ? 'Вход...' : 'Войти в систему' }}
        </button>
      </form>

      <!-- Подсказка с тестовыми учётками -->
      <div class="demo-accounts">
        <p class="demo-title">🔑 Тестовые аккаунты:</p>
        <div class="demo-list">
          <button class="demo-btn" @click="fillDemo('ivanov', 'password123')">
            <span class="role super">Super</span>
            ivanov / password123 (Иванов А.П.)
          </button>
          <button class="demo-btn" @click="fillDemo('petrova', 'password123')">
            <span class="role admin">Admin</span>
            petrova / password123 (Петрова М.С.)
          </button>
          <button class="demo-btn" @click="fillDemo('sidorov', 'password123')">
            <span class="role manager">Manager</span>
            sidorov / password123 (Сидоров Д.А.)
          </button>
          <button class="demo-btn" @click="fillDemo('kozlova', 'password123')">
            <span class="role employee">Employee</span>
            kozlova / password123 (Козлова А.В.)
          </button>
        </div>
      </div>

      <!-- Футер -->
      <div class="login-footer">
        <p>DevOps Home Lab © 2025</p>
      </div>
    </div>
  </div>
</template>

<script>
import auth from '../services/auth'

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
          // Редирект на главную или на страницу, откуда пришли
          const redirect = this.$route.query.redirect || '/'
          this.$router.push(redirect)
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

    fillDemo(username, password) {
      this.username = username
      this.password = password
      this.error = null
    }
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
  font-size: 4rem;
  margin-bottom: 0.5rem;
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
  font-size: 1.25rem;
  padding: 0.25rem;
  opacity: 0.7;
  transition: opacity 0.2s;
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

.demo-accounts {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.demo-title {
  color: #888;
  font-size: 0.85rem;
  margin: 0 0 0.75rem 0;
  text-align: center;
}

.demo-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.demo-btn {
  width: 100%;
  padding: 0.625rem 1rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  color: #aaa;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  text-align: left;
}

.demo-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
  color: #fff;
}

.role {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
}

.role.super {
  background: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
}

.role.admin {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.role.manager {
  background: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
}

.role.user {
  background: rgba(34, 197, 94, 0.2);
  color: #4ade80;
}

.role.employee {
  background: rgba(34, 197, 94, 0.2);
  color: #4ade80;
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

  .logo {
    font-size: 3rem;
  }

  .login-header h1 {
    font-size: 1.5rem;
  }
}
</style>
