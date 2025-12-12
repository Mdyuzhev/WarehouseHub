<template>
  <div class="receipt-create">
    <div class="header">
      <h1>Create Receipt</h1>
      <button @click="goBack" class="btn btn-secondary">Back</button>
    </div>

    <div v-if="error" class="error-message">{{ error }}</div>

    <form @submit.prevent="submitReceipt" class="form">
      <div class="form-section">
        <h3>Receipt Information</h3>

        <div class="form-group">
          <label>Supplier Name *</label>
          <input
            v-model="form.supplierName"
            type="text"
            required
            placeholder="Enter supplier name"
            class="form-input"
          />
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
            <select v-model="item.productId" required class="form-input">
              <option value="">Select product</option>
              <option v-for="product in products" :key="product.id" :value="product.id">
                {{ product.name }} ({{ product.sku }})
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Expected Quantity *</label>
            <input
              v-model.number="item.expectedQuantity"
              type="number"
              min="1"
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
          {{ loading ? 'Creating...' : 'Create Receipt' }}
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

const products = ref([])
const form = ref({
  supplierName: '',
  notes: '',
  items: []
})

const isValid = computed(() => {
  return form.value.supplierName.trim() !== '' &&
    form.value.items.length > 0 &&
    form.value.items.every(item => item.productId && item.expectedQuantity > 0)
})

async function loadProducts() {
  const result = await fetchDocuments('/products', {
    facilityId: facilityStore.currentFacility?.id
  })
  if (result.success && result.data) {
    products.value = result.data
  }
}

function addItem() {
  form.value.items.push({
    productId: '',
    expectedQuantity: 1
  })
}

function removeItem(index) {
  form.value.items.splice(index, 1)
}

async function submitReceipt() {
  const payload = {
    facilityId: facilityStore.currentFacility?.id,
    supplierName: form.value.supplierName,
    notes: form.value.notes,
    items: form.value.items
  }

  const result = await createDocument('/receipts', payload)
  if (result.success) {
    router.push(`/dc/receipts/${result.data.id}`)
  }
}

function goBack() {
  router.push('/dc/receipts')
}

onMounted(() => {
  loadProducts()
})
</script>

<style scoped>
.receipt-create {
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
