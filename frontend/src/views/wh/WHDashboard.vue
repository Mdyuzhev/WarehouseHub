<template>
  <div class="dashboard" data-testid="wh-dashboard">
    <h1>WH Dashboard</h1>
    <p>Дашборд склада</p>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value" data-testid="receipts-count">{{ receiptsCount }}</div>
        <div class="stat-label">Входящие поставки</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" data-testid="shipments-count">{{ shipmentsCount }}</div>
        <div class="stat-label">Исходящие отгрузки</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" data-testid="stock-count">{{ stockCount }}</div>
        <div class="stat-label">Позиций на складе</div>
      </div>
    </div>

    <div class="nav-cards">
      <router-link to="/wh/receipts" class="nav-card" data-testid="receipts-link">
        <span class="nav-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3.75H6.912a2.25 2.25 0 0 0-2.15 1.588L2.35 13.177a2.25 2.25 0 0 0-.1.661V18a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18v-4.162c0-.224-.034-.447-.1-.661L19.24 5.338a2.25 2.25 0 0 0-2.15-1.588H15M2.25 13.5h3.86a2.25 2.25 0 0 1 2.012 1.244l.256.512a2.25 2.25 0 0 0 2.013 1.244h3.218a2.25 2.25 0 0 0 2.013-1.244l.256-.512a2.25 2.25 0 0 1 2.013-1.244h3.859M12 3v8.25m0 0-3-3m3 3 3-3"/></svg></span>
        <span class="nav-title">Входящие</span>
        <span class="nav-desc">Поставки с DC</span>
      </router-link>

      <router-link to="/wh/shipments" class="nav-card" data-testid="shipments-link">
        <span class="nav-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3.75H6.912a2.25 2.25 0 0 0-2.15 1.588L2.35 13.177a2.25 2.25 0 0 0-.1.661V18a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18v-4.162c0-.224-.034-.447-.1-.661L19.24 5.338a2.25 2.25 0 0 0-2.15-1.588H15M2.25 13.5h3.86a2.25 2.25 0 0 1 2.012 1.244l.256.512a2.25 2.25 0 0 0 2.013 1.244h3.218a2.25 2.25 0 0 0 2.013-1.244l.256-.512a2.25 2.25 0 0 1 2.013-1.244h3.859M12 3v8.25m0 0 3-3m-3 3-3-3"/></svg></span>
        <span class="nav-title">Исходящие</span>
        <span class="nav-desc">Отгрузки на PP</span>
      </router-link>

      <router-link to="/wh/stock" class="nav-card" data-testid="stock-link">
        <span class="nav-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m20.25 7.5-.625 10.632a2.25 2.25 0 0 1-2.247 2.118H6.622a2.25 2.25 0 0 1-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125Z"/></svg></span>
        <span class="nav-title">Остатки</span>
        <span class="nav-desc">Текущие остатки на складе</span>
      </router-link>

      <router-link to="/wh/inventory" class="nav-card" data-testid="inventory-link">
        <span class="nav-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25ZM6.75 12h.008v.008H6.75V12Zm0 3h.008v.008H6.75V15Zm0 3h.008v.008H6.75V18Z"/></svg></span>
        <span class="nav-title">Инвентаризация</span>
        <span class="nav-desc">Проведение инвентаризации</span>
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
const shipmentsCount = ref(0)
const stockCount = ref(0)

async function loadStats() {
  const apiUrl = getApiUrl()
  const facilityId = facilityStore.currentFacility?.id

  if (!facilityId) return

  try {
    const [receiptsResp, shipmentsResp, stockResp] = await Promise.all([
      authFetch(`${apiUrl}/receipts?facilityId=${facilityId}`),
      authFetch(`${apiUrl}/shipments?sourceFacilityId=${facilityId}`),
      authFetch(`${apiUrl}/stock/facility/${facilityId}`)
    ])

    if (receiptsResp.ok) {
      const data = await receiptsResp.json()
      receiptsCount.value = Array.isArray(data) ? data.length : 0
    }

    if (shipmentsResp.ok) {
      const data = await shipmentsResp.json()
      shipmentsCount.value = Array.isArray(data) ? data.length : 0
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

.nav-icon {
  margin-bottom: 0.5rem;
  color: #2c3e50;
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
