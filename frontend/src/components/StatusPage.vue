<template>
  <div class="status-page">
    <header class="status-header">
      <h1>System Status</h1>
      <p class="subtitle">Мониторинг состояния Warehouse System</p>
      <div class="last-updated">
        Последнее обновление: {{ lastUpdated }}
        <button class="refresh-btn" :disabled="loading" @click="refresh">
          {{ loading ? '...' : 'Обновить' }}
        </button>
      </div>
    </header>

    <main class="status-main">
      <!-- Overall Status -->
      <section class="status-card overall-status" :class="overallStatusClass">
        <div class="status-icon">{{ overallStatusIcon }}</div>
        <div class="status-info">
          <h2>Общий статус системы</h2>
          <span class="status-badge" :class="overallStatusClass">
            {{ health.status || 'Загрузка...' }}
          </span>
        </div>
      </section>

      <!-- Components Grid -->
      <section class="components-grid">
        <div
          v-for="(component, name) in health.components"
          :key="name"
          class="component-card"
          :class="getStatusClass(component.status)"
        >
          <div class="component-header">
            <span class="component-icon">{{ getComponentIcon(name) }}</span>
            <h3>{{ getComponentName(name) }}</h3>
          </div>

          <div class="component-status">
            <span class="status-dot" :class="getStatusClass(component.status)" />
            <span class="status-text">{{ component.status }}</span>
          </div>

          <div v-if="component.details || hasExtraInfo(component)" class="component-details">
            <div v-if="component.details?.database" class="detail-row">
              <span class="detail-label">База данных:</span>
              <span class="detail-value">{{ component.details.database }}</span>
            </div>

            <div v-if="component.details?.total" class="detail-row">
              <span class="detail-label">Всего:</span>
              <span class="detail-value">{{ formatBytes(component.details.total) }}</span>
            </div>

            <div v-if="component.details?.free" class="detail-row">
              <span class="detail-label">Свободно:</span>
              <span class="detail-value">{{ formatBytes(component.details.free) }}</span>
            </div>

            <!-- Disk Usage Bar -->
            <div v-if="component.details?.total && component.details?.free" class="usage-bar-container">
              <div class="usage-bar">
                <div
                  class="usage-bar-fill"
                  :style="{ width: getDiskUsagePercent(component.details) + '%' }"
                  :class="getDiskUsageClass(component.details)"
                />
              </div>
              <span class="usage-percent">{{ getDiskUsagePercent(component.details) }}% использовано</span>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- Error Message -->
    <div v-if="error" class="error-banner">
      {{ error }}
    </div>
  </div>
</template>

<script>
import { getHealthUrl } from '../utils/apiConfig'

export default {
  name: 'StatusPage',

  data() {
    return {
      health: {},
      loading: false,
      error: null,
      lastUpdated: 'Никогда',
      autoRefreshInterval: 30000,
      refreshTimer: null,
      apiUrl: getHealthUrl()
    }
  },

  computed: {
    overallStatusClass() {
      return this.getStatusClass(this.health.status)
    },
    overallStatusIcon() {
      const status = this.health.status
      if (status === 'UP') return '✓'
      if (status === 'DOWN') return '✗'
      if (status === 'UNKNOWN') return '?'
      return '...'
    }
  },

  mounted() {
    this.refresh()
    this.startAutoRefresh()
  },

  beforeUnmount() {
    this.stopAutoRefresh()
  },

  methods: {
    async refresh() {
      this.loading = true
      this.error = null

      try {
        const response = await fetch(this.apiUrl)
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        this.health = await response.json()
        this.lastUpdated = new Date().toLocaleTimeString('ru-RU')
      } catch (err) {
        this.error = `Не удалось получить статус: ${err.message}`
        console.error('Health check failed:', err)
      } finally {
        this.loading = false
      }
    },

    startAutoRefresh() {
      this.refreshTimer = setInterval(() => {
        this.refresh()
      }, this.autoRefreshInterval)
    },

    stopAutoRefresh() {
      if (this.refreshTimer) {
        clearInterval(this.refreshTimer)
        this.refreshTimer = null
      }
    },

    getStatusClass(status) {
      if (status === 'UP') return 'status-up'
      if (status === 'DOWN') return 'status-down'
      if (status === 'OUT_OF_SERVICE') return 'status-warning'
      return 'status-unknown'
    },

    getComponentIcon(name) {
      const icons = {
        db: 'DB',
        database: 'DB',
        diskSpace: 'HDD',
        ping: 'PING',
        livenessState: 'LIVE',
        readinessState: 'READY'
      }
      return icons[name] || name.substring(0, 4).toUpperCase()
    },

    getComponentName(name) {
      const names = {
        db: 'База данных',
        database: 'База данных',
        diskSpace: 'Дисковое пространство',
        ping: 'Ping',
        livenessState: 'Liveness Probe',
        readinessState: 'Readiness Probe'
      }
      return names[name] || name
    },

    hasExtraInfo(component) {
      return component.database || component.details
    },

    formatBytes(bytes) {
      if (!bytes) return 'N/A'
      const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
      if (bytes === 0) return '0 Bytes'
      const i = Math.floor(Math.log(bytes) / Math.log(1024))
      return parseFloat((bytes / Math.pow(1024, i)).toFixed(2)) + ' ' + sizes[i]
    },

    getDiskUsagePercent(details) {
      if (!details.total || !details.free) return 0
      const used = details.total - details.free
      return Math.round((used / details.total) * 100)
    },

    getDiskUsageClass(details) {
      const percent = this.getDiskUsagePercent(details)
      if (percent >= 90) return 'usage-critical'
      if (percent >= 70) return 'usage-warning'
      return 'usage-normal'
    }
  }
}
</script>

<style scoped>
.status-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  color: #eee;
  font-family: 'Segoe UI', system-ui, sans-serif;
}

.status-header {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  padding: 2rem;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.status-header h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  background: linear-gradient(90deg, #00d4ff, #7b2cbf);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  color: #888;
  margin-bottom: 1rem;
}




.last-updated {
  font-size: 0.9rem;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.refresh-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  color: #ddd;
  transition: all 0.3s;
}

.refresh-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.2);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.status-main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.status-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

/* Overall Status */
.overall-status {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  transition: all 0.3s;
}

.overall-status.status-up {
  border-color: #22c55e;
  box-shadow: 0 0 30px rgba(34, 197, 94, 0.2);
}

.overall-status.status-down {
  border-color: #ef4444;
  box-shadow: 0 0 30px rgba(239, 68, 68, 0.2);
}

.status-icon {
  font-size: 3rem;
  font-weight: bold;
}

.status-info h2 {
  margin-bottom: 0.5rem;
  font-size: 1.3rem;
}

.status-badge {
  display: inline-block;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: bold;
  font-size: 0.9rem;
}

.status-badge.status-up {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.status-badge.status-down {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.status-badge.status-warning {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.status-badge.status-unknown {
  background: rgba(107, 114, 128, 0.2);
  color: #6b7280;
}

/* Components Grid */
.components-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.component-card {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 1.25rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: all 0.3s;
}

.component-card:hover {
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.15);
}

.component-card.status-up {
  border-left: 3px solid #22c55e;
}

.component-card.status-down {
  border-left: 3px solid #ef4444;
}

.component-card.status-warning {
  border-left: 3px solid #f59e0b;
}

.component-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.component-icon {
  font-size: 0.8rem;
  font-weight: bold;
  background: rgba(255, 255, 255, 0.1);
  padding: 0.5rem;
  border-radius: 8px;
}

.component-header h3 {
  font-size: 1.1rem;
  margin: 0;
  color: #ddd;
}

.component-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.status-dot.status-up {
  background: #22c55e;
  box-shadow: 0 0 10px #22c55e;
}

.status-dot.status-down {
  background: #ef4444;
  box-shadow: 0 0 10px #ef4444;
}

.status-dot.status-warning {
  background: #f59e0b;
  box-shadow: 0 0 10px #f59e0b;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  font-weight: 600;
  font-size: 0.95rem;
}

.component-details {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  padding: 0.75rem;
  font-size: 0.85rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 0.25rem 0;
}

.detail-label {
  color: #888;
}

.detail-value {
  color: #ddd;
  font-family: monospace;
}

/* Disk Usage Bar */
.usage-bar-container {
  margin-top: 0.75rem;
}

.usage-bar {
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.usage-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.usage-bar-fill.usage-normal {
  background: linear-gradient(90deg, #22c55e, #4ade80);
}

.usage-bar-fill.usage-warning {
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
}

.usage-bar-fill.usage-critical {
  background: linear-gradient(90deg, #ef4444, #f87171);
}

.usage-percent {
  display: block;
  text-align: right;
  font-size: 0.75rem;
  color: #888;
  margin-top: 0.25rem;
}

/* Error Banner */
.error-banner {
  position: fixed;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(239, 68, 68, 0.9);
  color: white;
  padding: 1rem 2rem;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

/* Responsive */
@media (max-width: 640px) {
  .status-header h1 {
    font-size: 1.75rem;
  }

  .status-main {
    padding: 1rem;
  }

  .overall-status {
    flex-direction: column;
    text-align: center;
  }

  .components-grid {
    grid-template-columns: 1fr;
  }
}
</style>
