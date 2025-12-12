<template>
  <div class="issues-list">
    <div class="header">
      <h1>Customer Issues</h1>
      <button @click="goToCreate" class="btn btn-primary">New Issue</button>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="issues.length === 0" class="empty">
      No customer issues found
    </div>

    <table v-else class="table">
      <thead>
        <tr>
          <th>Document Number</th>
          <th>Customer</th>
          <th>Phone</th>
          <th>Status</th>
          <th>Created Date</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="issue in issues" :key="issue.id">
          <td>{{ issue.documentNumber }}</td>
          <td>{{ issue.customerName }}</td>
          <td>{{ issue.customerPhone }}</td>
          <td>
            <span :class="['status-badge', `status-${issue.status.toLowerCase()}`]">
              {{ issue.status }}
            </span>
          </td>
          <td>{{ formatDate(issue.createdDate) }}</td>
          <td>
            <button @click="viewDetail(issue.id)" class="btn btn-sm">View</button>
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
const { loading, documents: issues, fetchAll } = useDocument('issue-acts')

async function loadIssues() {
  if (!facilityStore.currentFacility?.id) return
  await fetchAll(facilityStore.currentFacility.id)
}

function goToCreate() {
  router.push('/pp/issues/create')
}

function viewDetail(id) {
  router.push(`/pp/issues/${id}`)
}

function formatDate(dateString) {
  return dateString ? new Date(dateString).toLocaleDateString('ru-RU') : '-'
}

onMounted(() => {
  loadIssues()
})
</script>

<style scoped>
.issues-list {
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
}

.status-draft {
  background: #e9ecef;
}

.status-completed {
  background: #d4edda;
}

.loading,
.empty {
  padding: 2rem;
  text-align: center;
  color: #6c757d;
}
</style>
