<template>
  <div class="stock-list">
    <h1>WH Stock</h1>

    <div class="filters">
      <label>
        <input type="checkbox" v-model="showLowStockOnly" @change="filterStock" />
        Show low stock only
      </label>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="filteredStock.length === 0" class="empty">
      No stock data available
    </div>

    <table v-else class="table">
      <thead>
        <tr>
          <th>Product</th>
          <th>SKU</th>
          <th>Total Quantity</th>
          <th>Reserved</th>
          <th>Available</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in filteredStock" :key="item.id" :class="{ 'low-stock': item.isLowStock }">
          <td>{{ item.productName }}</td>
          <td>{{ item.productSku }}</td>
          <td>{{ item.quantity }}</td>
          <td>{{ item.reservedQuantity }}</td>
          <td>{{ item.availableQuantity }}</td>
          <td>
            <button @click="adjustStock(item)" class="btn btn-sm">Adjust</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="showAdjustModal" class="modal">
      <div class="modal-content">
        <h3>Adjust Stock: {{ selectedItem?.productName }}</h3>
        <div class="form-group">
          <label>Adjustment Quantity</label>
          <input v-model.number="adjustment" type="number" class="form-input" />
          <small>Positive to add, negative to subtract</small>
        </div>
        <div class="form-group">
          <label>Reason</label>
          <textarea v-model="adjustmentReason" rows="3" class="form-input"></textarea>
        </div>
        <div class="modal-actions">
          <button @click="saveAdjustment" class="btn btn-primary">Save</button>
          <button @click="closeModal" class="btn btn-secondary">Cancel</button>
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
const showAdjustModal = ref(false)
const selectedItem = ref(null)
const adjustment = ref(0)
const adjustmentReason = ref('')

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

function adjustStock(item) {
  selectedItem.value = item
  adjustment.value = 0
  adjustmentReason.value = ''
  showAdjustModal.value = true
}

async function saveAdjustment() {
  const apiUrl = getApiUrl()
  const response = await authFetch(`${apiUrl}/stock/${selectedItem.value.id}/adjust`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      quantity: adjustment.value,
      reason: adjustmentReason.value
    })
  })

  if (response.ok) {
    closeModal()
    await loadStock()
  }
}

function closeModal() {
  showAdjustModal.value = false
  selectedItem.value = null
}

onMounted(() => {
  loadStock()
})
</script>

<style scoped>
.stock-list {
  padding: 2rem;
}

.filters {
  margin-bottom: 1.5rem;
}

.table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.table th,
.table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.table th {
  background: #f8f9fa;
  font-weight: 600;
}

.low-stock {
  background: #fff3cd;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-sm {
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
  background: #007bff;
  color: white;
}

.btn-primary {
  background: #28a745;
  color: white;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  min-width: 400px;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.loading,
.empty {
  padding: 2rem;
  text-align: center;
  color: #6c757d;
}
</style>
