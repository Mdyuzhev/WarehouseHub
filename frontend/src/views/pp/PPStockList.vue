<template>
  <div class="stock-list">
    <h1>PP Stock</h1>

    <div class="filters">
      <label>
        <input type="checkbox" v-model="showLowStockOnly" @change="filterStock" />
        Show low stock alerts only
      </label>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="filteredStock.length === 0" class="empty">
      No stock data available
    </div>

    <div v-else class="stock-grid">
      <div
        v-for="item in filteredStock"
        :key="item.id"
        class="stock-card"
        :class="{ 'low-stock': item.isLowStock }"
      >
        <div class="product-name">{{ item.productName }}</div>
        <div class="product-sku">{{ item.productSku }}</div>
        <div class="stock-info">
          <div class="stock-row">
            <span class="label">Available:</span>
            <span class="value">{{ item.availableQuantity }}</span>
          </div>
          <div class="stock-row">
            <span class="label">Reserved:</span>
            <span class="value">{{ item.reservedQuantity }}</span>
          </div>
          <div v-if="item.isLowStock" class="alert">
            Low Stock Alert!
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useFacilityStore } from '../../stores/facility'
import { authFetch } from '../../services/auth'
import { getApiUrl } from '../../utils/apiConfig'

const facilityStore = useFacilityStore()
const loading = ref(false)
const stockData = ref([])
const showLowStockOnly = ref(false)

const filteredStock = computed(() => {
  if (showLowStockOnly.value) {
    return stockData.value.filter(item => item.isLowStock)
  }
  return stockData.value
})

async function loadStock() {
  loading.value = true
  const apiUrl = getApiUrl()
  const response = await authFetch(`${apiUrl}/stock/facility/${facilityStore.currentFacility?.id}`)
  if (response.ok) {
    stockData.value = await response.json()
  }
  loading.value = false
}

function filterStock() {
  // Triggers computed property update
}

onMounted(() => {
  loadStock()
})
</script>

<style scoped>
.stock-list {
  padding: 2rem;
}

h1 {
  margin-bottom: 1.5rem;
}

.filters {
  margin-bottom: 1.5rem;
}

.filters label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.stock-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.stock-card {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  border: 2px solid transparent;
  transition: border-color 0.2s;
}

.stock-card:hover {
  border-color: #007bff;
}

.stock-card.low-stock {
  border-color: #dc3545;
  background: #fff5f5;
}

.product-name {
  font-weight: 600;
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
  color: #212529;
}

.product-sku {
  font-size: 0.875rem;
  color: #6c757d;
  margin-bottom: 1rem;
}

.stock-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.stock-row {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #e9ecef;
}

.stock-row:last-child {
  border-bottom: none;
}

.stock-row .label {
  color: #6c757d;
  font-size: 0.875rem;
}

.stock-row .value {
  font-weight: 600;
  font-size: 1.25rem;
  color: #212529;
}

.alert {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #f8d7da;
  color: #721c24;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
  text-align: center;
}

.loading,
.empty {
  padding: 2rem;
  text-align: center;
  color: #6c757d;
}
</style>
