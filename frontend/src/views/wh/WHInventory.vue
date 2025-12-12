<template>
  <div class="inventory" data-testid="inventory-page">
    <div class="header">
      <h1>Inventory Count</h1>
      <button v-if="!currentInventory" @click="createInventory" class="btn btn-primary" data-testid="start-inventory-button">
        Start New Inventory
      </button>
    </div>

    <div v-if="loading" class="loading">Loading...</div>

    <div v-else-if="currentInventory" class="content">
      <div class="info-card">
        <div class="info-row">
          <span class="label">Status:</span>
          <span :class="['status-badge', `status-${currentInventory.status.toLowerCase()}`]">
            {{ currentInventory.status }}
          </span>
        </div>
        <div class="info-row">
          <span class="label">Created:</span>
          <span>{{ formatDate(currentInventory.createdDate) }}</span>
        </div>
      </div>

      <div class="items-section">
        <h3>Items</h3>
        <table class="table" data-testid="inventory-table">
          <thead>
            <tr>
              <th>Product</th>
              <th>System Qty</th>
              <th>Actual Qty</th>
              <th>Difference</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in currentInventory.items" :key="item.id">
              <td>{{ item.productName }}</td>
              <td>{{ item.systemQuantity }}</td>
              <td>
                <input
                  v-if="currentInventory.status === 'DRAFT'"
                  v-model.number="item.actualQuantity"
                  type="number"
                  min="0"
                  class="qty-input"
                  data-testid="actual-quantity-input"
                />
                <span v-else>{{ item.actualQuantity }}</span>
              </td>
              <td :class="getDifferenceClass(item)" data-testid="difference">
                {{ item.actualQuantity - item.systemQuantity }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="actions">
        <button
          v-if="currentInventory.status === 'DRAFT'"
          @click="completeInventory"
          class="btn btn-primary"
          data-testid="complete-inventory-button"
        >
          Complete Inventory
        </button>
      </div>
    </div>

    <div v-else class="empty">
      No active inventory. Click "Start New Inventory" to begin.
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useDocument } from '../../composables/useDocument'
import { useFacilityStore } from '../../stores/facility'

const facilityStore = useFacilityStore()
const { loading, document: currentInventory, fetchAll, create, complete } = useDocument('inventory-acts')

async function loadInventory() {
  const result = await fetchAll(facilityStore.currentFacility?.id)
  if (result.success && result.data && result.data.length > 0) {
    // Get the most recent draft inventory
    const drafts = result.data.filter(inv => inv.status === 'DRAFT')
    if (drafts.length > 0) {
      currentInventory.value = drafts[0]
    }
  }
}

async function createInventory() {
  const result = await create({
    facilityId: facilityStore.currentFacility?.id
  })
  if (result.success) {
    currentInventory.value = result.data
  }
}

async function completeInventory() {
  await complete(currentInventory.value.id)
  currentInventory.value = null
  await loadInventory()
}

function getDifferenceClass(item) {
  const diff = item.actualQuantity - item.systemQuantity
  if (diff > 0) return 'positive'
  if (diff < 0) return 'negative'
  return ''
}

function formatDate(dateString) {
  return dateString ? new Date(dateString).toLocaleString('ru-RU') : '-'
}

onMounted(() => {
  loadInventory()
})
</script>

<style scoped>
.inventory {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 2rem;
}

.info-card {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  margin-bottom: 2rem;
}

.info-row {
  display: flex;
  padding: 0.75rem 0;
  border-bottom: 1px solid #e9ecef;
}

.info-row:last-child {
  border-bottom: none;
}

.label {
  font-weight: 600;
  min-width: 150px;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.875rem;
}

.status-draft {
  background: #e9ecef;
}

.status-completed {
  background: #d4edda;
}

.items-section {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  margin-bottom: 2rem;
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table th,
.table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e9ecef;
}

.table th {
  background: #f8f9fa;
  font-weight: 600;
}

.qty-input {
  width: 100px;
  padding: 0.25rem 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
}

.positive {
  color: #28a745;
  font-weight: 600;
}

.negative {
  color: #dc3545;
  font-weight: 600;
}

.actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.btn {
  padding: 0.5rem 1.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-primary {
  background: #28a745;
  color: white;
}

.loading,
.empty {
  padding: 2rem;
  text-align: center;
  color: #6c757d;
}
</style>
