<template>
  <div class="issue-detail">
    <div class="header">
      <h1>Issue {{ issue?.documentNumber }}</h1>
      <button @click="goBack" class="btn btn-secondary">Back</button>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="issue" class="content">
      <div class="info-card">
        <div class="info-row">
          <span class="label">Status:</span>
          <span :class="['status-badge', `status-${issue.status.toLowerCase()}`]">
            {{ issue.status }}
          </span>
        </div>
        <div class="info-row">
          <span class="label">Customer:</span>
          <span>{{ issue.customerName }}</span>
        </div>
        <div class="info-row">
          <span class="label">Phone:</span>
          <span>{{ issue.customerPhone }}</span>
        </div>
        <div class="info-row">
          <span class="label">Created:</span>
          <span>{{ formatDate(issue.createdDate) }}</span>
        </div>
        <div v-if="issue.completedDate" class="info-row">
          <span class="label">Completed:</span>
          <span>{{ formatDate(issue.completedDate) }}</span>
        </div>
        <div v-if="issue.notes" class="info-row">
          <span class="label">Notes:</span>
          <span>{{ issue.notes }}</span>
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
            <tr v-for="item in issue.items" :key="item.id">
              <td>{{ item.productName }}</td>
              <td>{{ item.productSku }}</td>
              <td>{{ item.quantity }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="actions">
        <button
          v-if="issue.status === 'DRAFT'"
          @click="completeIssue"
          :disabled="actionLoading"
          class="btn btn-primary"
        >
          Complete & Deduct Stock
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
const { loading, document: issue, fetchById, complete } = useDocument('issue-acts')
const actionLoading = ref(false)

async function loadIssue() {
  await fetchById(route.params.id)
}

async function completeIssue() {
  actionLoading.value = true
  await complete(route.params.id)
  actionLoading.value = false
}

function formatDate(dateString) {
  return dateString ? new Date(dateString).toLocaleString('ru-RU') : '-'
}

function goBack() {
  router.push('/pp/issues')
}

onMounted(() => {
  loadIssue()
})
</script>

<style scoped>
.issue-detail {
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

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #28a745;
  color: white;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.loading {
  padding: 2rem;
  text-align: center;
}
</style>
