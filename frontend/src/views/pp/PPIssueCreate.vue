<template>
  <div class="issue-create">
    <div class="header">
      <h1>New Customer Issue</h1>
      <button @click="goBack" class="btn btn-secondary">Back</button>
    </div>

    <form @submit.prevent="submitIssue" class="form">
      <div class="form-section">
        <h3>Customer Information</h3>

        <div class="form-group">
          <label>Customer Name *</label>
          <input v-model="form.customerName" type="text" required class="form-input" />
        </div>

        <div class="form-group">
          <label>Phone *</label>
          <input v-model="form.customerPhone" type="tel" required class="form-input" />
        </div>

        <div class="form-group">
          <label>Notes</label>
          <textarea v-model="form.notes" rows="3" class="form-input"></textarea>
        </div>
      </div>

      <div class="form-section">
        <div class="section-header">
          <h3>Items</h3>
          <button type="button" @click="addItem" class="btn btn-sm">Add Item</button>
        </div>

        <div v-if="form.items.length === 0" class="empty">
          No items added. Click "Add Item" to select products.
        </div>

        <div v-for="(item, index) in form.items" :key="index" class="item-row">
          <div class="form-group">
            <label>Product *</label>
            <select v-model="item.productId" required class="form-input">
              <option value="">Select product</option>
              <option v-for="p in availableProducts" :key="p.id" :value="p.id">
                {{ p.name }} (Available: {{ getStock(p.id) }})
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Quantity *</label>
            <input
              v-model.number="item.quantity"
              type="number"
              min="1"
              :max="getStock(item.productId)"
              required
              class="form-input"
            />
          </div>

          <button type="button" @click="removeItem(index)" class="btn btn-danger btn-sm">
            Remove
          </button>
        </div>
      </div>

      <div class="form-actions">
        <button type="submit" :disabled="loading || !isValid" class="btn btn-primary">
          {{ loading ? 'Creating...' : 'Create & Complete' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDocument } from '../../composables/useDocument'
import { useFacilityStore } from '../../stores/facility'
import { authFetch } from '../../services/auth'
import { getApiUrl } from '../../utils/apiConfig'

const router = useRouter()
const facilityStore = useFacilityStore()
const { loading, create } = useDocument('issue-acts')

const availableProducts = ref([])
const stockData = ref({})
const form = ref({
  customerName: '',
  customerPhone: '',
  notes: '',
  items: []
})

const isValid = computed(() => {
  return form.value.customerName.trim() !== '' &&
    form.value.customerPhone.trim() !== '' &&
    form.value.items.length > 0 &&
    form.value.items.every(item => item.productId && item.quantity > 0)
})

async function loadData() {
  const apiUrl = getApiUrl()

  // Load products
  const prodResp = await authFetch(`${apiUrl}/products`)
  if (prodResp.ok) availableProducts.value = await prodResp.json()

  // Load stock
  const stockResp = await authFetch(`${apiUrl}/stock/facility/${facilityStore.currentFacility?.id}`)
  if (stockResp.ok) {
    const stock = await stockResp.json()
    stockData.value = stock.reduce((acc, s) => {
      acc[s.productId] = s.availableQuantity
      return acc
    }, {})
  }
}

function getStock(productId) {
  return stockData.value[productId] || 0
}

function addItem() {
  form.value.items.push({ productId: '', quantity: 1 })
}

function removeItem(index) {
  form.value.items.splice(index, 1)
}

async function submitIssue() {
  const result = await create({
    facilityId: facilityStore.currentFacility?.id,
    customerName: form.value.customerName,
    customerPhone: form.value.customerPhone,
    notes: form.value.notes,
    items: form.value.items
  })

  if (result.success) {
    router.push(`/pp/issues/${result.data.id}`)
  }
}

function goBack() {
  router.push('/pp/issues')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.issue-create {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 2rem;
}

.form {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.form-section {
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid #e9ecef;
}

.form-section:last-of-type {
  border-bottom: none;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
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

.item-row {
  display: grid;
  grid-template-columns: 2fr 1fr auto;
  gap: 1rem;
  align-items: end;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.form-actions {
  text-align: right;
}

.btn {
  padding: 0.5rem 1rem;
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

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-sm {
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
}

.empty {
  padding: 2rem;
  text-align: center;
  color: #6c757d;
  background: #f8f9fa;
  border-radius: 4px;
}
</style>
