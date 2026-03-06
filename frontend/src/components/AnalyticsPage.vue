<template>
  <div class="analytics-page">
    <!-- Header -->
    <div class="page-header">
      <h1>Аналитика в реальном времени</h1>
      <div class="connection-status" :class="{ connected: wsConnected }">
        <span class="status-dot"></span>
        {{ wsConnected ? 'Подключено' : 'Отключено' }}
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon events"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z"/></svg></div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_events }}</div>
          <div class="stat-label">Всего событий</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon audit"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125"/></svg></div>
        <div class="stat-content">
          <div class="stat-value">{{ auditTotal }}</div>
          <div class="stat-label">Аудит операций</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon notifications"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0"/></svg></div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.notifications?.total || 0 }}</div>
          <div class="stat-label">Уведомлений</div>
        </div>
      </div>

      <div class="stat-card warning">
        <div class="stat-icon stock"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"/></svg></div>
        <div class="stat-content">
          <div class="stat-value">{{ stockAlerts }}</div>
          <div class="stat-label">Алерты склада</div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="content-grid">
      <!-- Live Feed -->
      <section class="card live-feed">
        <div class="card-header">
          <h2>Live Feed</h2>
          <span class="event-count">{{ events.length }} событий</span>
        </div>

        <div class="feed-list" ref="feedList">
          <TransitionGroup name="feed">
            <div
              v-for="event in events"
              :key="event.timestamp + event.name"
              class="feed-item"
              :class="getEventClass(event)"
            >
              <div class="event-icon">{{ getEventIcon(event) }}</div>
              <div class="event-content">
                <div class="event-title">
                  {{ formatEventTitle(event) }}
                </div>
                <div class="event-meta">
                  <span v-if="event.user" class="event-user">{{ event.user }}</span>
                  <span class="event-time">{{ formatTime(event.timestamp) }}</span>
                </div>
              </div>
            </div>
          </TransitionGroup>

          <div v-if="events.length === 0" class="feed-empty">
            <span class="empty-icon"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3.75H6.912a2.25 2.25 0 0 0-2.15 1.588L2.35 13.177a2.25 2.25 0 0 0-.1.661V18a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18v-4.162c0-.224-.034-.447-.1-.661L19.24 5.338a2.25 2.25 0 0 0-2.15-1.588H15M2.25 13.5h3.86a2.25 2.25 0 0 1 2.012 1.244l.256.512a2.25 2.25 0 0 0 2.013 1.244h3.218a2.25 2.25 0 0 0 2.013-1.244l.256-.512a2.25 2.25 0 0 1 2.013-1.244h3.859M12 3v8.25m0 0-3-3m3 3 3-3"/></svg></span>
            <p>Ожидание событий...</p>
          </div>
        </div>
      </section>

      <!-- Charts Panel -->
      <section class="card charts-panel">
        <div class="card-header">
          <h2>Статистика</h2>
          <select v-model="chartPeriod" class="period-select">
            <option value="hourly">По часам</option>
            <option value="daily">По дням</option>
          </select>
        </div>

        <!-- Audit Breakdown -->
        <div class="chart-section">
          <h3>Операции аудита</h3>
          <div class="bar-chart">
            <div
              v-for="(value, key) in stats.audit"
              :key="key"
              class="bar-item"
            >
              <div class="bar-label">{{ auditLabels[key] || key }}</div>
              <div class="bar-container">
                <div
                  class="bar-fill"
                  :class="'bar-' + key"
                  :style="{ width: getBarWidth(value, maxAuditValue) + '%' }"
                ></div>
              </div>
              <div class="bar-value">{{ value }}</div>
            </div>
          </div>
        </div>

        <!-- Time Chart (simplified) -->
        <div class="chart-section">
          <h3>{{ chartPeriod === 'hourly' ? 'Последние 24 часа' : 'Последние 7 дней' }}</h3>
          <div class="time-chart">
            <div
              v-for="(item, idx) in timeData"
              :key="idx"
              class="time-bar"
              :title="item.label + ': ' + item.total + ' событий'"
            >
              <div
                class="time-bar-fill"
                :style="{ height: getBarHeight(item.total, maxTimeValue) + '%' }"
              ></div>
              <div class="time-label">{{ item.shortLabel }}</div>
            </div>
          </div>
        </div>

        <!-- Stock Alerts -->
        <div class="chart-section alerts-section" v-if="stockAlerts > 0">
          <h3>Алерты склада</h3>
          <div class="alerts-breakdown">
            <div class="alert-item low-stock">
              <span class="alert-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"/></svg></span>
              <span class="alert-label">Low Stock</span>
              <span class="alert-value">{{ stats.notifications?.low_stock || 0 }}</span>
            </div>
            <div class="alert-item out-of-stock">
              <span class="alert-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18.364 18.364A9 9 0 0 0 5.636 5.636m12.728 12.728A9 9 0 0 1 5.636 5.636m12.728 12.728L5.636 5.636"/></svg></span>
              <span class="alert-label">Out of Stock</span>
              <span class="alert-value">{{ stats.notifications?.out_of_stock || 0 }}</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import auth from '../services/auth'

export default {
  name: 'AnalyticsPage',

  data() {
    return {
      wsConnected: false,
      ws: null,
      stats: {
        total_events: 0,
        audit: {
          create: 0,
          update: 0,
          delete: 0,
          login: 0,
          logout: 0
        },
        notifications: {
          total: 0,
          low_stock: 0,
          out_of_stock: 0
        }
      },
      events: [],
      hourlyData: [],
      dailyData: [],
      chartPeriod: 'hourly',
      reconnectAttempts: 0,
      maxReconnectAttempts: 5,
      reconnectTimeout: null,
      auditLabels: {
        create: 'Создание',
        update: 'Обновление',
        delete: 'Удаление',
        login: 'Вход',
        logout: 'Выход'
      }
    }
  },

  computed: {
    auditTotal() {
      const a = this.stats.audit || {}
      return (a.create || 0) + (a.update || 0) + (a.delete || 0) + (a.login || 0) + (a.logout || 0)
    },

    stockAlerts() {
      const n = this.stats.notifications || {}
      return (n.low_stock || 0) + (n.out_of_stock || 0)
    },

    maxAuditValue() {
      const values = Object.values(this.stats.audit || {})
      return Math.max(...values, 1)
    },

    timeData() {
      const data = this.chartPeriod === 'hourly' ? this.hourlyData : this.dailyData
      return data.map(item => ({
        ...item,
        label: this.chartPeriod === 'hourly' ? item.hour : item.date,
        shortLabel: this.chartPeriod === 'hourly'
          ? item.hour?.split(' ')[1]?.replace(':00', 'ч') || ''
          : item.date?.split('-').slice(1).join('/') || '',
        total: item.stats?.total || 0
      }))
    },

    maxTimeValue() {
      const values = this.timeData.map(d => d.total)
      return Math.max(...values, 1)
    }
  },

  mounted() {
    this.loadInitialData()
    this.connectWebSocket()
  },

  beforeUnmount() {
    this.disconnectWebSocket()
  },

  methods: {
    getAnalyticsUrl() {
      // Analytics service URL - внутри кластера или через ingress
      // eslint-disable-next-line no-eval
      return eval('window.__ANALYTICS_URL__') || 'http://192.168.1.74:30090'
    },

    async loadInitialData() {
      try {
        const baseUrl = this.getAnalyticsUrl()

        // Load stats
        const statsRes = await fetch(`${baseUrl}/api/stats`)
        if (statsRes.ok) {
          const data = await statsRes.json()
          this.stats = {
            total_events: data.total_events || 0,
            audit: data.audit || {},
            notifications: data.notifications || {}
          }
        }

        // Load events
        const eventsRes = await fetch(`${baseUrl}/api/events?limit=50`)
        if (eventsRes.ok) {
          this.events = await eventsRes.json()
        }

        // Load hourly
        const hourlyRes = await fetch(`${baseUrl}/api/hourly?hours=24`)
        if (hourlyRes.ok) {
          this.hourlyData = await hourlyRes.json()
        }

        // Load daily
        const dailyRes = await fetch(`${baseUrl}/api/daily?days=7`)
        if (dailyRes.ok) {
          this.dailyData = await dailyRes.json()
        }
      } catch (e) {
        console.error('Failed to load analytics data:', e)
      }
    },

    connectWebSocket() {
      try {
        const baseUrl = this.getAnalyticsUrl()
        const wsUrl = baseUrl.replace('http', 'ws') + '/ws'

        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          this.wsConnected = true
          this.reconnectAttempts = 0
          console.log('Analytics WebSocket connected')
        }

        this.ws.onclose = () => {
          this.wsConnected = false
          console.log('Analytics WebSocket disconnected')
          this.scheduleReconnect()
        }

        this.ws.onerror = (e) => {
          console.error('WebSocket error:', e)
        }

        this.ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data)
            this.handleMessage(msg)
          } catch (e) {
            console.error('Failed to parse message:', e)
          }
        }
      } catch (e) {
        console.error('Failed to connect WebSocket:', e)
        this.scheduleReconnect()
      }
    },

    disconnectWebSocket() {
      if (this.reconnectTimeout) {
        clearTimeout(this.reconnectTimeout)
      }
      if (this.ws) {
        this.ws.close()
        this.ws = null
      }
    },

    scheduleReconnect() {
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.log('Max reconnect attempts reached')
        return
      }

      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000)
      this.reconnectAttempts++

      this.reconnectTimeout = setTimeout(() => {
        console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`)
        this.connectWebSocket()
      }, delay)
    },

    handleMessage(msg) {
      switch (msg.type) {
        case 'init':
          // Initial stats from server
          if (msg.stats) {
            this.updateStats(msg.stats)
          }
          break

        case 'stats':
          // Stats update
          if (msg.data) {
            this.updateStats(msg.data)
          }
          break

        case 'event':
          // New event
          if (msg.data) {
            this.addEvent(msg.data)
          }
          break
      }
    },

    updateStats(data) {
      this.stats = {
        total_events: data.total_events || this.stats.total_events,
        audit: {
          create: data.total_create || this.stats.audit.create,
          update: data.total_update || this.stats.audit.update,
          delete: data.total_delete || this.stats.audit.delete,
          login: data.total_login || this.stats.audit.login,
          logout: data.total_logout || this.stats.audit.logout
        },
        notifications: {
          total: data.total_notifications || this.stats.notifications.total,
          low_stock: data.total_low_stock || this.stats.notifications.low_stock,
          out_of_stock: data.total_out_of_stock || this.stats.notifications.out_of_stock
        }
      }
    },

    addEvent(event) {
      // Add to beginning of array
      this.events.unshift(event)
      // Keep only last 50 events
      if (this.events.length > 50) {
        this.events.pop()
      }

      // Update stats locally
      this.stats.total_events++

      if (event.type === 'audit') {
        const key = event.event?.toLowerCase()
        if (key && this.stats.audit[key] !== undefined) {
          this.stats.audit[key]++
        }
      } else if (event.type === 'notification') {
        this.stats.notifications.total++
        const key = event.event?.toLowerCase()
        if (key && this.stats.notifications[key] !== undefined) {
          this.stats.notifications[key]++
        }
      }
    },

    getEventClass(event) {
      if (event.type === 'notification') {
        return event.event === 'OUT_OF_STOCK' ? 'event-danger' : 'event-warning'
      }
      const classes = {
        'CREATE': 'event-success',
        'UPDATE': 'event-info',
        'DELETE': 'event-danger',
        'LOGIN': 'event-info',
        'LOGOUT': 'event-muted'
      }
      return classes[event.event] || ''
    },

    getEventIcon(event) {
      if (event.type === 'notification') {
        return event.event === 'OUT_OF_STOCK' ? '\u2716' : '\u2193'
      }
      const icons = {
        'CREATE': '+',
        'UPDATE': '\u270E',
        'DELETE': '\u2716',
        'LOGIN': '\u2192',
        'LOGOUT': '\u2190'
      }
      return icons[event.event] || '\u2022'
    },

    formatEventTitle(event) {
      if (event.type === 'notification') {
        return `${event.event === 'OUT_OF_STOCK' ? 'Закончился' : 'Мало'}: ${event.name}`
      }

      const actions = {
        'CREATE': 'Создан',
        'UPDATE': 'Обновлён',
        'DELETE': 'Удалён',
        'LOGIN': 'Вход',
        'LOGOUT': 'Выход'
      }
      const action = actions[event.event] || event.event
      return `${action}: ${event.name || event.entity || ''}`
    },

    formatTime(timestamp) {
      if (!timestamp) return ''
      try {
        const date = new Date(timestamp)
        return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
      } catch {
        return timestamp
      }
    },

    getBarWidth(value, max) {
      return Math.round((value / max) * 100)
    },

    getBarHeight(value, max) {
      return Math.round((value / max) * 100)
    }
  }
}
</script>

<style scoped>
.analytics-page {
  padding: 1.5rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.page-header h1 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
  background: #fef2f2;
  color: #991b1b;
}

.connection-status.connected {
  background: #dcfce7;
  color: #166534;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.stat-card.warning {
  border-left: 4px solid #f59e0b;
}

.stat-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f4f6;
  border-radius: 10px;
}

.stat-icon.events { background: #dbeafe; }
.stat-icon.audit { background: #e0e7ff; }
.stat-icon.notifications { background: #fef3c7; }
.stat-icon.stock { background: #fee2e2; }

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1f2937;
  line-height: 1;
}

.stat-label {
  font-size: 0.85rem;
  color: #6b7280;
  margin-top: 0.25rem;
}

/* Content Grid */
.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

.card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e5e7eb;
}

.card-header h2 {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
}

.event-count {
  font-size: 0.85rem;
  color: #6b7280;
  background: #f3f4f6;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
}

/* Live Feed */
.feed-list {
  max-height: 500px;
  overflow-y: auto;
}

.feed-item {
  display: flex;
  gap: 0.75rem;
  padding: 0.875rem 1.25rem;
  border-bottom: 1px solid #f3f4f6;
  transition: background 0.2s;
}

.feed-item:hover {
  background: #f9fafb;
}

.event-icon {
  font-size: 1.25rem;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f4f6;
  border-radius: 8px;
  flex-shrink: 0;
}

.event-success .event-icon { background: #dcfce7; }
.event-info .event-icon { background: #dbeafe; }
.event-warning .event-icon { background: #fef3c7; }
.event-danger .event-icon { background: #fee2e2; }
.event-muted .event-icon { background: #f3f4f6; }

.event-content {
  flex: 1;
  min-width: 0;
}

.event-title {
  font-weight: 500;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.event-meta {
  display: flex;
  gap: 0.75rem;
  font-size: 0.8rem;
  color: #6b7280;
  margin-top: 0.25rem;
}

.event-user::before {
  content: '\2192 ';
}

.feed-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: #9ca3af;
}

.empty-icon {
  margin-bottom: 0.5rem;
  color: #9ca3af;
}

/* Feed animation */
.feed-enter-active {
  transition: all 0.3s ease;
}

.feed-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.feed-leave-active {
  transition: all 0.2s ease;
}

.feed-leave-to {
  opacity: 0;
}

/* Charts Panel */
.period-select {
  padding: 0.4rem 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.85rem;
  background: white;
}

.chart-section {
  padding: 1.25rem;
  border-bottom: 1px solid #f3f4f6;
}

.chart-section:last-child {
  border-bottom: none;
}

.chart-section h3 {
  font-size: 0.9rem;
  font-weight: 600;
  color: #6b7280;
  margin: 0 0 1rem 0;
}

/* Bar Chart */
.bar-chart {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.bar-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.bar-label {
  width: 100px;
  font-size: 0.85rem;
  color: #6b7280;
}

.bar-container {
  flex: 1;
  height: 24px;
  background: #f3f4f6;
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.bar-create { background: #10b981; }
.bar-update { background: #3b82f6; }
.bar-delete { background: #ef4444; }
.bar-login { background: #8b5cf6; }
.bar-logout { background: #6b7280; }

.bar-value {
  width: 40px;
  text-align: right;
  font-weight: 600;
  font-size: 0.9rem;
  color: #1f2937;
}

/* Time Chart */
.time-chart {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 120px;
  padding-top: 1rem;
}

.time-bar {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

.time-bar-fill {
  width: 100%;
  background: linear-gradient(to top, #4f46e5, #818cf8);
  border-radius: 4px 4px 0 0;
  min-height: 2px;
  transition: height 0.3s ease;
}

.time-label {
  font-size: 0.65rem;
  color: #9ca3af;
  margin-top: 0.25rem;
  white-space: nowrap;
}

/* Alerts Section */
.alerts-breakdown {
  display: flex;
  gap: 1rem;
}

.alert-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  border-radius: 8px;
}

.alert-item.low-stock {
  background: #fef3c7;
}

.alert-item.out-of-stock {
  background: #fee2e2;
}

.alert-icon {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.alert-label {
  flex: 1;
  font-size: 0.85rem;
  font-weight: 500;
}

.alert-value {
  font-size: 1.25rem;
  font-weight: 700;
}

/* Responsive */
@media (max-width: 768px) {
  .analytics-page {
    padding: 1rem;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .stat-card {
    padding: 1rem;
  }

  .stat-icon {
    width: 40px;
    height: 40px;
    font-size: 1.5rem;
  }

  .stat-value {
    font-size: 1.5rem;
  }

  .bar-label {
    width: 80px;
    font-size: 0.75rem;
  }

  .time-label {
    display: none;
  }

  .alerts-breakdown {
    flex-direction: column;
  }
}
</style>
