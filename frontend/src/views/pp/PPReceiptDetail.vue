<template>
  <div class="receipt-detail">
    <div class="header">
      <h1>Receipt {{ receipt?.documentNumber }}</h1>
      <button @click="goBack" class="btn btn-secondary">Back</button>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="receipt" class="content">
      <div class="info-card">
        <div class="info-row">
          <span class="label">Status:</span>
          <span :class="['status-badge', `status-${receipt.status.toLowerCase()}`]">
            {{ receipt.status }}
          </span>
        </div>
        <div class="info-row">
          <span class="label">Source (WH):</span>
          <span>{{ receipt.sourceFacilityName }}</span>
        </div>
        <div class="info-row">
          <span class="label">Created:</span>
          <span>{{ formatDate(receipt.createdDate) }}</span>
        </div>
      </div>

      <div class="items-section">
        <h3>Items</h3>
        <table class="table">
          <thead>
            <tr>
              <th>Product</th>
              <th>Expected Qty</th>
              <th v-if="receipt.status !== 'DRAFT'">Actual Qty</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in receipt.items" :key="item.id">
              <td>{{ item.productName }}</td>
              <td>{{ item.expectedQuantity }}</td>
              <td v-if="receipt.status !== 'DRAFT'">
                <input
                  v-if="showActualInput"
                  v-model.number="actualQuantities[item.id]"
                  type="number"
                  min="0"
                  class="qty-input"
                />
                <span v-else>{{ item.actualQuantity || '-' }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="actions">
        <button
          v-if="receipt.status === 'IN_TRANSIT'"
          @click="toggleActualInput"
          class="btn btn-secondary"
        >
          {{ showActualInput ? 'Cancel' : 'Confirm Receipt' }}
        </button>

        <button
          v-if="showActualInput"
          @click="confirmReceipt"
          class="btn btn-success"
        >
          Save & Confirm
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useDocument } from '../../composables/useDocument'

const router = useRouter()
const route = useRoute()
const { loading, document: receipt, fetchById, confirm } = useDocument('receipts')

const showActualInput = ref(false)
const actualQuantities = ref({})

async function loadReceipt() {
  const result = await fetchById(route.params.id)
  if (result.success && result.data) {
    result.data.items.forEach(item => {
      actualQuantities.value[item.id] = item.actualQuantity || item.expectedQuantity
    })
  }
}

async function confirmReceipt() {
  const items = receipt.value.items.map(item => ({
    id: item.id,
    actualQuantity: actualQuantities.value[item.id]
  }))

  await confirm(route.params.id, { items })
  showActualInput.value = false
}

function toggleActualInput() {
  showActualInput.value = !showActualInput.value
}

function formatDate(dateString) {
  return dateString ? new Date(dateString).toLocaleString('ru-RU') : '-'
}

function goBack() {
  router.push('/pp/receipts')
}

onMounted(() => {
  loadReceipt()
})
</script>

<style scoped>
.receipt-detail {
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

.status-in_transit {
  background: #fff3cd;
}

.status-confirmed {
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

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-success {
  background: #28a745;
  color: white;
}

.loading {
  padding: 2rem;
  text-align: center;
}
</style>
