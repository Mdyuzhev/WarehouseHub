<template>
  <div class="shipments-list">
    <div class="header">
      <h1>WH Shipments</h1>
      <button @click="goToCreate" class="btn btn-primary" data-testid="create-button">Create Shipment</button>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">Error: {{ error }}</div>

    <div v-else-if="shipments.length === 0" class="empty">
      No shipments found
    </div>

    <table v-else class="table" data-testid="shipments-table">
      <thead>
        <tr>
          <th>Document Number</th>
          <th>Destination (PP)</th>
          <th>Status</th>
          <th>Created Date</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="shipment in shipments" :key="shipment.id" data-testid="shipment-row">
          <td>{{ shipment.documentNumber }}</td>
          <td>{{ shipment.destinationFacilityName }}</td>
          <td>
            <span :class="['status-badge', `status-${shipment.status.toLowerCase()}`]">
              {{ shipment.status }}
            </span>
          </td>
          <td>{{ formatDate(shipment.createdDate) }}</td>
          <td>
            <button @click="viewDetail(shipment.id)" class="btn btn-sm">View</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDocument } from '../../composables/useDocument'
import { useFacilityStore } from '../../stores/facility'

const router = useRouter()
const facilityStore = useFacilityStore()
const { loading, error, documents: shipments, fetchAll } = useDocument('shipments')

async function loadShipments() {
  if (!facilityStore.currentFacility?.id) return
  await fetchAll(facilityStore.currentFacility.id)
}

function goToCreate() {
  router.push('/wh/shipments/create')
}

function viewDetail(id) {
  router.push(`/wh/shipments/${id}`)
}

function formatDate(dateString) {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('ru-RU')
}

onMounted(() => {
  loadShipments()
})
</script>

<style scoped>
.shipments-list {
  padding: 2rem;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-primary {
  background: #28a745;
  color: white;
}

.btn-sm {
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
  background: #007bff;
  color: white;
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

.status-shipped {
  background: #fff3cd;
  color: #856404;
}

.status-delivered {
  background: #d4edda;
  color: #155724;
}

.loading,
.error,
.empty {
  padding: 2rem;
  text-align: center;
  color: #6c757d;
}

.error {
  color: #dc3545;
}
</style>
