<template>
  <div class="shipment-create">
    <div class="header">
      <h1>Create Shipment to PP</h1>
      <button @click="goBack" class="btn btn-secondary">Back</button>
    </div>

    <form @submit.prevent="submitShipment" class="form">
      <div class="form-group">
        <label>Destination (PP) *</label>
        <select v-model="form.destinationFacilityId" required class="form-input">
          <option value="">Select production point</option>
          <option v-for="pp in productionPoints" :key="pp.id" :value="pp.id">
            {{ pp.name }} ({{ pp.code }})
          </option>
        </select>
      </div>

      <div class="form-group">
        <label>Notes</label>
        <textarea v-model="form.notes" rows="3" class="form-input"></textarea>
      </div>

      <h3>Items</h3>
      <button type="button" @click="addItem" class="btn btn-sm">Add Item</button>

      <div v-for="(item, index) in form.items" :key="index" class="item-row">
        <select v-model="item.productId" required class="form-input">
          <option value="">Select product</option>
          <option v-for="p in products" :key="p.id" :value="p.id">
            {{ p.name }} (Stock: {{ getStock(p.id) }})
          </option>
        </select>
        <input v-model.number="item.quantity" type="number" min="1" required class="form-input" />
        <button type="button" @click="removeItem(index)" class="btn btn-danger btn-sm">Remove</button>
      </div>

      <div class="form-actions">
        <button type="submit" :disabled="loading" class="btn btn-primary">
          {{ loading ? 'Creating...' : 'Create' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDocument } from '../../composables/useDocument'
import { useFacilityStore } from '../../stores/facility'
import { authFetch } from '../../services/auth'
import { getApiUrl } from '../../utils/apiConfig'

const router = useRouter()
const facilityStore = useFacilityStore()
const { loading, create } = useDocument('shipments')

const productionPoints = ref([])
const products = ref([])
const stock = ref({})
const form = ref({
  destinationFacilityId: '',
  notes: '',
  items: []
})

async function loadData() {
  const apiUrl = getApiUrl()

  // Load PP facilities
  const ppResp = await authFetch(`${apiUrl}/facilities?type=PP&parentId=${facilityStore.currentFacility?.id}`)
  if (ppResp.ok) productionPoints.value = await ppResp.json()

  // Load products and stock
  const prodResp = await authFetch(`${apiUrl}/products`)
  if (prodResp.ok) products.value = await prodResp.json()

  const stockResp = await authFetch(`${apiUrl}/stock/facility/${facilityStore.currentFacility?.id}`)
  if (stockResp.ok) {
    const stockData = await stockResp.json()
    stock.value = stockData.reduce((acc, s) => {
      acc[s.productId] = s.availableQuantity
      return acc
    }, {})
  }
}

function getStock(productId) {
  return stock.value[productId] || 0
}

function addItem() {
  form.value.items.push({ productId: '', quantity: 1 })
}

function removeItem(index) {
  form.value.items.splice(index, 1)
}

async function submitShipment() {
  const result = await create({
    sourceFacilityId: facilityStore.currentFacility?.id,
    destinationFacilityId: form.value.destinationFacilityId,
    notes: form.value.notes,
    items: form.value.items
  })

  if (result.success) {
    router.push(`/wh/shipments/${result.data.id}`)
  }
}

function goBack() {
  router.push('/wh/shipments')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.shipment-create {
  padding: 2rem;
  max-width: 800px;
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
  margin-top: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.form-actions {
  margin-top: 2rem;
  text-align: right;
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
</style>
