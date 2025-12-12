<template>
  <div class="shipment-create">
    <div class="header">
      <h1>Create Shipment</h1>
      <button @click="goBack" class="btn btn-secondary">Back</button>
    </div>

    <div v-if="error" class="error-message">{{ error }}</div>

    <form @submit.prevent="submitShipment" class="form">
      <div class="form-section">
        <h3>Shipment Information</h3>

        <div class="form-group">
          <label>Destination Facility (WH) *</label>
          <select v-model="form.destinationFacilityId" required class="form-input">
            <option value="">Select warehouse</option>
            <option v-for="facility in warehouses" :key="facility.id" :value="facility.id">
              {{ facility.name }} ({{ facility.code }})
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>Notes</label>
          <textarea
            v-model="form.notes"
            rows="3"
            placeholder="Additional notes"
            class="form-input"
          ></textarea>
        </div>
      </div>

      <div class="form-section">
        <div class="section-header">
          <h3>Items</h3>
          <button type="button" @click="addItem" class="btn btn-sm">Add Item</button>
        </div>

        <div v-if="form.items.length === 0" class="empty">
          No items added. Click "Add Item" to add products.
        </div>

        <div v-for="(item, index) in form.items" :key="index" class="item-row">
          <div class="form-group">
            <label>Product *</label>
            <select v-model="item.productId" @change="updateAvailableStock(index)" required class="form-input">
              <option value="">Select product</option>
              <option v-for="product in products" :key="product.id" :value="product.id">
                {{ product.name }} ({{ product.sku }})
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Quantity *</label>
            <input
              v-model.number="item.quantity"
              type="number"
              min="1"
              :max="item.availableStock || 999999"
              required
              class="form-input"
            />
            <small v-if="item.availableStock !== null" class="stock-info">
              Available: {{ item.availableStock }}
            </small>
          </div>

          <button type="button" @click="removeItem(index)" class="btn btn-danger btn-sm">
            Remove
          </button>
        </div>
      </div>

      <div class="form-actions">
        <button type="submit" :disabled="loading || !isValid" class="btn btn-primary">
          {{ loading ? 'Creating...' : 'Create Shipment' }}
        </button>
        <button type="button" @click="goBack" class="btn btn-secondary">Cancel</button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDocument } from '../../composables/useDocument'
import { useFacilityStore } from '../../stores/facility'

const router = useRouter()
const facilityStore = useFacilityStore()
const { loading, error, createDocument, fetchDocuments } = useDocument()

const warehouses = ref([])
const products = ref([])
const stockData = ref({})

const form = ref({
  destinationFacilityId: '',
  notes: '',
  items: []
})

const isValid = computed(() => {
  return form.value.destinationFacilityId !== '' &&
    form.value.items.length > 0 &&
    form.value.items.every(item =>
      item.productId &&
      item.quantity > 0 &&
      item.quantity <= (item.availableStock || 999999)
    )
})

async function loadWarehouses() {
  const result = await fetchDocuments('/facilities', {
    type: 'WH',
    parentId: facilityStore.currentFacility?.id
  })
  if (result.success && result.data) {
    warehouses.value = result.data
  }
}

async function loadProducts() {
  const result = await fetchDocuments('/products', {
    facilityId: facilityStore.currentFacility?.id
  })
  if (result.success && result.data) {
    products.value = result.data
  }
}

async function loadStock() {
  const result = await fetchDocuments('/stock', {
    facilityId: facilityStore.currentFacility?.id
  })
  if (result.success && result.data) {
    stockData.value = result.data.reduce((acc, stock) => {
      acc[stock.productId] = stock.availableQuantity
      return acc
    }, {})
  }
}

function updateAvailableStock(index) {
  const item = form.value.items[index]
  if (item.productId) {
    item.availableStock = stockData.value[item.productId] || 0
  }
}

function addItem() {
  form.value.items.push({
    productId: '',
    quantity: 1,
    availableStock: null
  })
}

function removeItem(index) {
  form.value.items.splice(index, 1)
}

async function submitShipment() {
  const payload = {
    sourceFacilityId: facilityStore.currentFacility?.id,
    destinationFacilityId: form.value.destinationFacilityId,
    notes: form.value.notes,
    items: form.value.items.map(item => ({
      productId: item.productId,
      quantity: item.quantity
    }))
  }

  const result = await createDocument('/shipments', payload)
  if (result.success) {
    router.push(`/dc/shipments/${result.data.id}`)
  }
}

function goBack() {
  router.push('/dc/shipments')
}

onMounted(() => {
  loadWarehouses()
  loadProducts()
  loadStock()
})
</script>

<style scoped>
.shipment-create {
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

.error-message {
  padding: 1rem;
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  color: #721c24;
  margin-bottom: 1.5rem;
}

.form {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  padding: 2rem;
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
  color: #495057;
}

.form-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 1rem;
}

.form-input:focus {
  outline: none;
  border-color: #80bdff;
  box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
}

.stock-info {
  display: block;
  margin-top: 0.25rem;
  color: #6c757d;
  font-size: 0.875rem;
}

.item-row {
  display: grid;
  grid-template-columns: 1fr 200px auto;
  gap: 1rem;
  align-items: end;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
}

.btn {
  padding: 0.5rem 1rem;
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
