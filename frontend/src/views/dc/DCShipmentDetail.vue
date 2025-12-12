<template>
  <div class="shipment-detail">
    <div class="header">
      <h1>Shipment {{ shipment?.documentNumber }}</h1>
      <button @click="goBack" class="btn btn-secondary">Back</button>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">Error: {{ error }}</div>

    <div v-else-if="shipment" class="content">
      <div class="info-card">
        <div class="info-row">
          <span class="label">Status:</span>
          <span :class="['status-badge', `status-${shipment.status.toLowerCase()}`]">
            {{ shipment.status }}
          </span>
        </div>
        <div class="info-row">
          <span class="label">Destination:</span>
          <span>{{ shipment.destinationFacilityName }}</span>
        </div>
        <div class="info-row">
          <span class="label">Created Date:</span>
          <span>{{ formatDate(shipment.createdDate) }}</span>
        </div>
        <div v-if="shipment.shippedDate" class="info-row">
          <span class="label">Shipped Date:</span>
          <span>{{ formatDate(shipment.shippedDate) }}</span>
        </div>
        <div v-if="shipment.deliveredDate" class="info-row">
          <span class="label">Delivered Date:</span>
          <span>{{ formatDate(shipment.deliveredDate) }}</span>
        </div>
        <div v-if="shipment.linkedReceiptId" class="info-row">
          <span class="label">Linked Receipt:</span>
          <span>
            <a :href="`/wh/receipts/${shipment.linkedReceiptId}`" class="link">
              Receipt #{{ shipment.linkedReceiptId }}
            </a>
          </span>
        </div>
        <div v-if="shipment.notes" class="info-row">
          <span class="label">Notes:</span>
          <span>{{ shipment.notes }}</span>
        </div>
      </div>

      <div class="items-section">
        <h3>Items</h3>
        <table class="table">
          <thead>
            <tr>
              <th>Product</th>
              <th>SKU</th>
              <th>Quantity</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in shipment.items" :key="item.id">
              <td>{{ item.productName }}</td>
              <td>{{ item.productSku }}</td>
              <td>{{ item.quantity }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="actions">
        <button
          v-if="shipment.status === 'DRAFT'"
          @click="performAction('approve')"
          :disabled="actionLoading"
          class="btn btn-primary"
        >
          Approve & Reserve Stock
        </button>

        <button
          v-if="shipment.status === 'APPROVED'"
          @click="performAction('ship')"
          :disabled="actionLoading"
          class="btn btn-primary"
        >
          Mark as Shipped
        </button>

        <button
          v-if="shipment.status === 'SHIPPED'"
          @click="performAction('deliver')"
          :disabled="actionLoading"
          class="btn btn-success"
        >
          Mark as Delivered
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
const { loading, error, data, fetchDocument, updateDocument } = useDocument()

const shipment = ref(null)
const actionLoading = ref(false)

async function loadShipment() {
  const result = await fetchDocument('/shipments', route.params.id)
  if (result.success) {
    shipment.value = data.value
  }
}

async function performAction(action) {
  actionLoading.value = true
  const result = await updateDocument('/shipments', route.params.id, action)
  actionLoading.value = false

  if (result.success) {
    await loadShipment()
  }
}

function formatDate(dateString) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('ru-RU')
}

function goBack() {
  router.push('/dc/shipments')
}

onMounted(() => {
  loadShipment()
})
</script>

<style scoped>
.shipment-detail {
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

.status-approved {
  background: #d1ecf1;
  color: #0c5460;
}

.status-shipped {
  background: #fff3cd;
  color: #856404;
}

.status-delivered {
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
