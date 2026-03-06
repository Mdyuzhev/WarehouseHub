<template>
  <div class="dashboard" data-testid="dc-dashboard">
    <h1>DC Dashboard</h1>
    <p>Дашборд распределительного центра</p>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value" data-testid="receipts-count">{{ receiptsCount }}</div>
        <div class="stat-label">Приходные документы</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" data-testid="shipments-count">{{ shipmentsCount }}</div>
        <div class="stat-label">Расходные документы</div>
      </div>
    </div>

    <div class="nav-cards">
      <router-link to="/dc/receipts" class="nav-card" data-testid="receipts-link">
        <span class="nav-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3.75H6.912a2.25 2.25 0 0 0-2.15 1.588L2.35 13.177a2.25 2.25 0 0 0-.1.661V18a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18v-4.162c0-.224-.034-.447-.1-.661L19.24 5.338a2.25 2.25 0 0 0-2.15-1.588H15M2.25 13.5h3.86a2.25 2.25 0 0 1 2.012 1.244l.256.512a2.25 2.25 0 0 0 2.013 1.244h3.218a2.25 2.25 0 0 0 2.013-1.244l.256-.512a2.25 2.25 0 0 1 2.013-1.244h3.859M12 3v8.25m0 0-3-3m3 3 3-3"/></svg></span>
        <span class="nav-title">Приходные</span>
        <span class="nav-desc">Просмотр и создание приходных документов</span>
      </router-link>

      <router-link to="/dc/shipments" class="nav-card" data-testid="shipments-link">
        <span class="nav-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3.75H6.912a2.25 2.25 0 0 0-2.15 1.588L2.35 13.177a2.25 2.25 0 0 0-.1.661V18a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18v-4.162c0-.224-.034-.447-.1-.661L19.24 5.338a2.25 2.25 0 0 0-2.15-1.588H15M2.25 13.5h3.86a2.25 2.25 0 0 1 2.012 1.244l.256.512a2.25 2.25 0 0 0 2.013 1.244h3.218a2.25 2.25 0 0 0 2.013-1.244l.256-.512a2.25 2.25 0 0 1 2.013-1.244h3.859M12 3v8.25m0 0 3-3m-3 3-3-3"/></svg></span>
        <span class="nav-title">Расходные</span>
        <span class="nav-desc">Просмотр и создание расходных документов</span>
      </router-link>

      <router-link to="/dc/receipts/create" class="nav-card nav-card-action" data-testid="new-receipt-link">
        <span class="nav-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4.5v15m7.5-7.5h-15"/></svg></span>
        <span class="nav-title">Новый приход</span>
        <span class="nav-desc">Создать приходный документ</span>
      </router-link>

      <router-link to="/dc/shipments/create" class="nav-card nav-card-action" data-testid="new-shipment-link">
        <span class="nav-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4.5v15m7.5-7.5h-15"/></svg></span>
        <span class="nav-title">Новая отгрузка</span>
        <span class="nav-desc">Создать расходный документ</span>
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

async function loadStats() {
  const apiUrl = getApiUrl()
  const facilityId = facilityStore.currentFacility?.id

  if (!facilityId) return

  try {
    const [receiptsResp, shipmentsResp] = await Promise.all([
      authFetch(`${apiUrl}/receipts?facilityId=${facilityId}`),
      authFetch(`${apiUrl}/shipments?sourceFacilityId=${facilityId}`)
    ])

    if (receiptsResp.ok) {
      const data = await receiptsResp.json()
      receiptsCount.value = Array.isArray(data) ? data.length : 0
    }

    if (shipmentsResp.ok) {
      const data = await shipmentsResp.json()
      shipmentsCount.value = Array.isArray(data) ? data.length : 0
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
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
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
