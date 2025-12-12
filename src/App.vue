<template>
  <div id="app">
    <nav v-if="isAuthenticated" class="main-nav">
      <div class="nav-brand">
        <router-link to="/" class="brand-link">Warehouse</router-link>
      </div>

      <div class="nav-links">
        <router-link to="/" class="nav-link" data-testid="nav-products">Продукты</router-link>
        <router-link v-if="canEditProducts" to="/add" class="nav-link" data-testid="nav-add-product">+ Добавить</router-link>
        <router-link v-if="canAccessAnalytics" to="/analytics" class="nav-link" data-testid="nav-analytics">Аналитика</router-link>
        <router-link v-if="canAccessStatus" to="/status" class="nav-link" data-testid="nav-status">Статус</router-link>
      </div>

      <div class="nav-user">
        <div class="user-info">
          <span class="user-name">{{ currentUser?.fullName }}</span>
          <span class="user-role" :class="roleClass">{{ roleLabel }}</span>
        </div>
        <button class="logout-btn" title="Выйти" data-testid="logout-button" @click="handleLogout">Выход</button>
      </div>
    </nav>

    <router-view />
  </div>
</template>

<script>
import auth from './services/auth'

export default {
  name: 'App',

  data() {
    return {
      currentUser: null,
      authChecked: false
    }
  },

  computed: {
    isAuthenticated() {
      // Зависит от authChecked для реактивности
      return this.authChecked && auth.isAuthenticated()
    },

    canAccessStatus() {
      return auth.canAccess('system-status')
    },

    canAccessAnalytics() {
      return auth.canAccess('view-analytics')
    },

    canEditProducts() {
      return auth.canAccess('edit-products')
    },

    roleClass() {
      const role = this.currentUser?.role?.replace('ROLE_', '')?.toLowerCase()
      return role || ''
    },

    roleLabel() {
      const roles = {
        'SUPER_USER': 'Суперпользователь',
        'ADMIN': 'Администратор',
        'MANAGER': 'Менеджер',
        'EMPLOYEE': 'Сотрудник',
        'ANALYST': 'Аналитик'
      }
      const role = this.currentUser?.role?.replace('ROLE_', '')
      return roles[role] || role
    }
  },

  watch: {
    '$route': {
      handler() {
        // Даём время на сохранение токена после редиректа с login
        this.$nextTick(() => {
          this.updateUser()
        })
      },
      immediate: true
    }
  },

  methods: {
    handleLogout() {
      auth.logout()
      this.$router.push('/login')
    },

    updateUser() {
      this.currentUser = auth.getCurrentUser()
      // Переключаем флаг для триггера реактивности isAuthenticated
      this.authChecked = false
      this.$nextTick(() => {
        this.authChecked = true
      })
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', system-ui, sans-serif;
  line-height: 1.6;
  background-color: #f3f4f6;
}

#app {
  min-height: 100vh;
}

.main-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  height: 60px;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-brand { display: flex; align-items: center; }
.brand-link { color: white; text-decoration: none; font-size: 1.25rem; font-weight: 700; }

.nav-links { display: flex; gap: 0.5rem; }
.nav-link {
  color: rgba(255,255,255,0.85);
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  transition: all 0.2s;
}
.nav-link:hover { background: rgba(255,255,255,0.15); color: white; }
.nav-link.router-link-active { background: rgba(255,255,255,0.2); color: white; }

.nav-user { display: flex; align-items: center; gap: 1rem; }
.user-info { display: flex; flex-direction: column; align-items: flex-end; line-height: 1.2; }
.user-name { color: white; font-size: 0.9rem; font-weight: 500; }
.user-role {
  font-size: 0.7rem;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  text-transform: uppercase;
  font-weight: 600;
}
.user-role.super_user { background: rgba(239,68,68,0.3); color: #fecaca; }
.user-role.admin { background: rgba(245,158,11,0.3); color: #fef3c7; }
.user-role.manager { background: rgba(59,130,246,0.3); color: #bfdbfe; }
.user-role.employee { background: rgba(34,197,94,0.3); color: #bbf7d0; }
.user-role.analyst { background: rgba(139,92,246,0.3); color: #ddd6fe; }

.logout-btn {
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.3);
  color: white;
  padding: 0.4rem 0.8rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}
.logout-btn:hover { background: rgba(255,255,255,0.2); }

@media (max-width: 768px) {
  .main-nav {
    padding: 0 1rem;
    height: 56px;
  }
  .nav-links {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    display: flex;
    justify-content: space-around;
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    padding: 0.75rem 0;
    box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
    z-index: 100;
  }
  .nav-link {
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
  }
  .user-info {
    flex-direction: row;
    gap: 0.5rem;
    align-items: center;
  }
  .user-name {
    font-size: 0.8rem;
  }
  .user-role {
    font-size: 0.6rem;
  }
  .logout-btn {
    padding: 0.5rem 0.75rem;
    font-size: 0.8rem;
  }
  #app {
    padding-bottom: 60px;
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .nav-link {
    padding: 0.4rem 0.75rem;
    font-size: 0.9rem;
  }
}
</style>
