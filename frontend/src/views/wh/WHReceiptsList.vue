<template>
  <div class="receipts-list">
    <h1>WH Receipts</h1>

    <div class="filters">
      <select v-model="statusFilter" @change="loadReceipts" class="filter-select">
        <option value="">All Statuses</option>
        <option value="DRAFT">Draft</option>
        <option value="IN_TRANSIT">In Transit</option>
        <option value="CONFIRMED">Confirmed</option>
        <option value="COMPLETED">Completed</option>
      </select>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">Error: {{ error }}</div>

    <div v-else-if="receipts.length === 0" class="empty">
      No receipts found (including auto-created from shipments)
    </div>

    <table v-else class="table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Document Number</th>
          <th>Source</th>
          <th>Status</th>
          <th>Auto-Created</th>
          <th>Created Date</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="receipt in receipts" :key="receipt.id">
          <td>{{ receipt.id }}</td>
          <td>{{ receipt.documentNumber }}</td>
          <td>{{ receipt.supplierName || receipt.sourceFacilityName || '-' }}</td>
          <td>
            <span :class="['status-badge', `status-${receipt.status.toLowerCase()}`]">
              {{ receipt.status }}
            </span>
          </td>
          <td>
            <span v-if="receipt.linkedShipmentId" class="badge badge-info">Yes</span>
            <span v-else class="badge badge-secondary">No</span>
          </td>
          <td>{{ formatDate(receipt.createdDate) }}</td>
          <td>
            <button @click="viewDetail(receipt.id)" class="btn btn-sm">View</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDocument } from '../../composables/useDocument'
import { useFacilityStore } from '../../stores/facility'

const router = useRouter()
const facilityStore = useFacilityStore()
const { loading, error, documents: receipts, fetchAll } = useDocument('receipts')

const statusFilter = ref('')

async function loadReceipts() {
  if (!facilityStore.currentFacility?.id) return
  await fetchAll(facilityStore.currentFacility.id)
}

function viewDetail(id) {
  router.push(`/wh/receipts/${id}`)
}

function formatDate(dateString) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('ru-RU')
}

onMounted(() => {
  loadReceipts()
})
</script>

<style scoped>
.receipts-list {
  padding: 2rem;
}

h1 {
  margin-bottom: 2rem;
}

.filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.filter-select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  background: #007bff;
  color: white;
}

.btn:hover {
  background: #0056b3;
}

.btn-sm {
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
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

.table tbody tr:hover {
  background: #f8f9fa;
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

.badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.badge-info {
  background: #d1ecf1;
  color: #0c5460;
}

.badge-secondary {
  background: #e9ecef;
  color: #6c757d;
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
