<template>
  <div class="receipts-list">
    <h1>PP Receipts</h1>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="receipts.length === 0" class="empty">
      No receipts found (auto-created from WH shipments)
    </div>

    <table v-else class="table">
      <thead>
        <tr>
          <th>Document Number</th>
          <th>Source (WH)</th>
          <th>Status</th>
          <th>Created Date</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="receipt in receipts" :key="receipt.id">
          <td>{{ receipt.documentNumber }}</td>
          <td>{{ receipt.sourceFacilityName }}</td>
          <td>
            <span :class="['status-badge', `status-${receipt.status.toLowerCase()}`]">
              {{ receipt.status }}
            </span>
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
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDocument } from '../../composables/useDocument'
import { useFacilityStore } from '../../stores/facility'

const router = useRouter()
const facilityStore = useFacilityStore()
const { loading, documents: receipts, fetchAll } = useDocument('receipts')

async function loadReceipts() {
  if (!facilityStore.currentFacility?.id) return
  await fetchAll(facilityStore.currentFacility.id)
}

function viewDetail(id) {
  router.push(`/pp/receipts/${id}`)
}

function formatDate(dateString) {
  return dateString ? new Date(dateString).toLocaleDateString('ru-RU') : '-'
}

onMounted(() => {
  loadReceipts()
})
</script>

<style scoped>
.receipts-list {
  padding: 2rem;
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
}

.status-in_transit {
  background: #fff3cd;
  color: #856404;
}

.status-confirmed {
  background: #d4edda;
  color: #155724;
}

.btn-sm {
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.loading,
.empty {
  padding: 2rem;
  text-align: center;
  color: #6c757d;
}
</style>
