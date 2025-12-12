<template>
  <div class="dashboard" data-testid="pp-dashboard">
    <h1>PP Dashboard</h1>
    <p>Дашборд пункта выдачи</p>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value" data-testid="receipts-count">{{ receiptsCount }}</div>
        <div class="stat-label">Входящие поставки</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" data-testid="issues-count">{{ issuesCount }}</div>
        <div class="stat-label">Выдачи клиентам</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" data-testid="stock-count">{{ stockCount }}</div>
        <div class="stat-label">Позиций на складе</div>
      </div>
    </div>

    <div class="nav-cards">
      <router-link to="/pp/receipts" class="nav-card" data-testid="receipts-link">
        <span class="nav-icon">📥</span>
        <span class="nav-title">Входящие</span>
        <span class="nav-desc">Поставки с WH</span>
      </router-link>

      <router-link to="/pp/issues" class="nav-card" data-testid="issues-link">
        <span class="nav-icon">🛒</span>
        <span class="nav-title">Выдачи</span>
        <span class="nav-desc">Выдача товаров клиентам</span>
      </router-link>

      <router-link to="/pp/stock" class="nav-card" data-testid="stock-link">
        <span class="nav-icon">📦</span>
        <span class="nav-title">Остатки</span>
        <span class="nav-desc">Текущие остатки</span>
      </router-link>

      <router-link to="/pp/issues/create" class="nav-card nav-card-action" data-testid="new-issue-link">
        <span class="nav-icon">➕</span>
        <span class="nav-title">Новая выдача</span>
        <span class="nav-desc">Выдать товар клиенту</span>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useFacilityStore } from '../../stores/facility'
import { authFetch } from '../../services/auth'
import { getApiUrl } from '../../utils/apiConfig'

const facilityStore = useFacilityStore()
const receiptsCount = ref(0)
const issuesCount = ref(0)
const stockCount = ref(0)

async function loadStats() {
  const apiUrl = getApiUrl()
  const facilityId = facilityStore.currentFacility?.id

  if (!facilityId) return

  try {
    const [receiptsResp, issuesResp, stockResp] = await Promise.all([
      authFetch(`${apiUrl}/receipts?facilityId=${facilityId}`),
      authFetch(`${apiUrl}/issue-acts?facilityId=${facilityId}`),
      authFetch(`${apiUrl}/stock/facility/${facilityId}`)
    ])

    if (receiptsResp.ok) {
      const data = await receiptsResp.json()
      receiptsCount.value = Array.isArray(data) ? data.length : 0
    }

    if (issuesResp.ok) {
      const data = await issuesResp.json()
      issuesCount.value = Array.isArray(data) ? data.length : 0
    }

    if (stockResp.ok) {
      const data = await stockResp.json()
      stockCount.value = Array.isArray(data) ? data.length : 0
    }
  } catch (e) {
    console.error('Failed to load stats:', e)
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.dashboard {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1.5rem;
  margin: 2rem 0;
}

.stat-card {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  text-align: center;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: #2c3e50;
}

.stat-label {
  color: #6c757d;
  margin-top: 0.5rem;
}

.nav-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
}

.nav-card {
  display: flex;
  flex-direction: column;
  padding: 1.5rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  text-decoration: none;
  color: inherit;
  transition: transform 0.2s, box-shadow 0.2s;
}

.nav-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.nav-card-action {
  border: 2px dashed #28a745;
  background: #f8fff8;
}

.nav-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.nav-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #2c3e50;
}

.nav-desc {
  font-size: 0.875rem;
  color: #6c757d;
  margin-top: 0.5rem;
}
</style>
