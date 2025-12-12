<template>
  <div class="receipt-detail">
    <div class="header">
      <h1>Receipt {{ receipt?.documentNumber }}</h1>
      <button @click="goBack" class="btn btn-secondary">Back</button>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">Error: {{ error }}</div>

    <div v-else-if="receipt" class="content">
      <div class="info-card">
        <div class="info-row">
          <span class="label">Status:</span>
          <span :class="['status-badge', `status-${receipt.status.toLowerCase()}`]">
            {{ receipt.status }}
          </span>
        </div>
        <div class="info-row">
          <span class="label">Source:</span>
          <span>{{ receipt.supplierName || receipt.sourceFacilityName || '-' }}</span>
        </div>
        <div v-if="receipt.linkedShipmentId" class="info-row">
          <span class="label">Linked Shipment:</span>
          <span>
            <a :href="`/dc/shipments/${receipt.linkedShipmentId}`" class="link">
              Shipment #{{ receipt.linkedShipmentId }}
            </a>
          </span>
        </div>
        <div class="info-row">
          <span class="label">Created Date:</span>
          <span>{{ formatDate(receipt.createdDate) }}</span>
        </div>
        <div v-if="receipt.notes" class="info-row">
          <span class="label">Notes:</span>
          <span>{{ receipt.notes }}</span>
        </div>
      </div>

      <div class="items-section">
        <h3>Items</h3>
        <table class="table">
          <thead>
            <tr>
              <th>Product</th>
              <th>SKU</th>
              <th>Expected Qty</th>
              <th v-if="receipt.status !== 'DRAFT'">Actual Qty</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in receipt.items" :key="item.id">
              <td>{{ item.productName }}</td>
              <td>{{ item.productSku }}</td>
              <td>{{ item.expectedQuantity }}</td>
              <td v-if="receipt.status !== 'DRAFT'">
                <input
                  v-if="showActualInput && receipt.status === 'IN_TRANSIT'"
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
          v-if="showActualInput && receipt.status === 'IN_TRANSIT'"
          @click="confirmReceipt"
          :disabled="actionLoading"
          class="btn btn-success"
        >
          Save & Confirm
        </button>

        <button
          v-if="receipt.status === 'CONFIRMED'"
          @click="completeReceipt"
          :disabled="actionLoading"
          class="btn btn-primary"
        >
          Complete
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
const { loading, error, document: receipt, fetchById, confirm, complete } = useDocument('receipts')

const actionLoading = ref(false)
const showActualInput = ref(false)
const actualQuantities = ref({})

async function loadReceipt() {
  const result = await fetchById(route.params.id)
  if (result.success && result.data) {
    // Initialize actual quantities
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

  actionLoading.value = true
  const result = await confirm(route.params.id, { items })
  actionLoading.value = false

  if (result.success) {
    showActualInput.value = false
  }
}

async function completeReceipt() {
  actionLoading.value = true
  await complete(route.params.id)
  actionLoading.value = false
}

function toggleActualInput() {
  showActualInput.value = !showActualInput.value
}

function formatDate(dateString) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('ru-RU')
}

function goBack() {
  router.push('/wh/receipts')
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
  align-items: center;
  margin-bottom: 2rem;
}

.content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.info-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  padding: 1.5rem;
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
  color: #495057;
}

.link {
  color: #007bff;
  text-decoration: none;
}

.link:hover {
  text-decoration: underline;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 500;
}

.status-draft {
  background: #e9ecef;
  color: #495057;
}

.status-in_transit {
  background: #fff3cd;
  color: #856404;
}

.status-confirmed {
  background: #d4edda;
  color: #155724;
}

.status-completed {
  background: #d4edda;
  color: #155724;
}

.items-section {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  padding: 1.5rem;
}

.items-section h3 {
  margin-bottom: 1rem;
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
  font-size: 1rem;
}

.btn:hover {
  opacity: 0.9;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-success {
  background: #28a745;
  color: white;
}

.loading,
.error {
  padding: 2rem;
  text-align: center;
}

.error {
  color: #dc3545;
}
</style>
