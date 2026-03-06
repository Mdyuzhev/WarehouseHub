<template>
  <div class="home-page">
    <section class="card" data-testid="products-section">
      <div class="card-header">
        <h2 data-testid="products-title">Продукты на складе</h2>
        <div class="card-actions">
          <select v-model="selectedCategory" class="filter-select" @change="loadProducts">
            <option value="">Все категории</option>
            <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
          </select>
          <button class="btn btn-secondary btn-refresh" :disabled="loading" @click="loadProducts" title="Обновить список">
            <span class="refresh-icon" :class="{ spinning: loading }">↻</span>
          </button>
        </div>
      </div>

      <div v-if="products.length === 0" class="empty">
        Нет продуктов
      </div>

      <ul v-else class="product-list" data-testid="products-list">
        <li v-for="product in products" :key="product.id" class="product-item" :data-testid="'product-item-' + product.id">
          <div class="product-info">
            <span class="product-name">{{ product.name }}</span>
            <span v-if="product.category" class="product-category">{{ product.category }}</span>
            <span v-if="product.description" class="product-description">{{ product.description }}</span>
          </div>
          <span class="product-quantity">x{{ product.quantity }}</span>
          <span class="product-price">{{ formatPrice(product.price) }} ₽</span>
          <button
            v-if="canEditProducts"
            class="btn btn-edit btn-small"
            :data-testid="'edit-product-' + product.id"
            @click="openEditModal(product)"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0; vertical-align: middle;"><path d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125"/></svg>
          </button>
          <button
            v-if="canEditProducts"
            class="btn btn-danger btn-small"
            :data-testid="'delete-product-' + product.id"
            @click="deleteProduct(product.id)"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0; vertical-align: middle;"><path d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"/></svg>
          </button>
        </li>
      </ul>

      <div v-if="message" :class="['message', messageType]">{{ message }}</div>
    </section>

    <!-- Edit Modal -->
    <div v-if="editProduct" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal">
        <h3>Редактировать товар</h3>
        <form @submit.prevent="saveProduct">
          <div class="form-group">
            <label>Название</label>
            <input v-model="editProduct.name" type="text" required>
          </div>
          <div class="form-group">
            <label>Количество</label>
            <input v-model.number="editProduct.quantity" type="number" min="0" required>
          </div>
          <div class="form-group">
            <label>Цена</label>
            <input v-model.number="editProduct.price" type="number" step="0.01" min="0" required>
          </div>
          <div class="form-group">
            <label>Категория</label>
            <select v-model="editProduct.category">
              <option value="">-- Без категории --</option>
              <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>Описание</label>
            <textarea v-model="editProduct.description" maxlength="100" rows="2"></textarea>
          </div>
          <div class="modal-actions">
            <button type="submit" class="btn btn-primary" :disabled="saving">
              {{ saving ? 'Сохранение...' : 'Сохранить' }}
            </button>
            <button type="button" class="btn btn-secondary" @click="closeEditModal">Отмена</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import auth from '../services/auth'
import { getApiUrl } from '../utils/apiConfig'

export default {
  name: 'HomePage',

  data() {
    return {
      apiUrl: getApiUrl(),
      products: [],
      loading: false,
      saving: false,
      message: '',
      messageType: 'success',
      canEditProducts: auth.canAccess('edit-products'),
      categories: ['Электроника', 'Одежда', 'Продукты', 'Бытовая техника', 'Мебель', 'Другое'],
      selectedCategory: '',
      editProduct: null
    }
  },

  mounted() {
    // Небольшая задержка для гарантии сохранения токена после редиректа с login
    this.$nextTick(() => {
      if (this.isReady()) {
        this.loadProducts()
      } else {
        // Повторная попытка через 100ms если токен ещё не готов
        setTimeout(() => this.loadProducts(), 100)
      }
    })
  },

  activated() {
    // Вызывается при возврате на страницу (если используется keep-alive)
    if (this.isReady()) {
      this.loadProducts()
    }
  },

  methods: {
    isReady() {
      return auth.isAuthenticated() && auth.getToken()
    },

    async loadProducts() {
      // Проверяем авторизацию перед запросом
      if (!this.isReady()) {
        return
      }
      this.loading = true
      try {
        let url = this.apiUrl + '/products'
        if (this.selectedCategory) {
          url += '?category=' + encodeURIComponent(this.selectedCategory)
        }
        const r = await auth.authFetch(url)
        if (r.ok) {
          this.products = await r.json()
        }
      } catch (e) {
        this.showMessage('Ошибка: ' + e.message, 'error')
      } finally {
        this.loading = false
      }
    },

    async deleteProduct(id) {
      if (!confirm('Удалить продукт?')) return
      this.loading = true
      try {
        const r = await auth.authFetch(this.apiUrl + '/products/' + id, { method: 'DELETE' })
        if (r.ok) {
          this.showMessage('Удалено', 'success')
          this.loadProducts()
        }
      } catch (e) {
        this.showMessage('Ошибка', 'error')
      } finally {
        this.loading = false
      }
    },

    openEditModal(product) {
      this.editProduct = { ...product }
    },

    closeEditModal() {
      this.editProduct = null
    },

    async saveProduct() {
      if (!this.editProduct) return
      this.saving = true
      try {
        const r = await auth.authFetch(this.apiUrl + '/products/' + this.editProduct.id, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.editProduct)
        })
        if (r.ok) {
          this.showMessage('Сохранено', 'success')
          this.closeEditModal()
          this.loadProducts()
        } else {
          this.showMessage('Ошибка сохранения', 'error')
        }
      } catch (e) {
        this.showMessage('Ошибка: ' + e.message, 'error')
      } finally {
        this.saving = false
      }
    },

    showMessage(text, type = 'success') {
      this.message = text
      this.messageType = type
      setTimeout(() => { this.message = '' }, 5000)
    },

    formatPrice(p) {
      return new Intl.NumberFormat('ru-RU', { minimumFractionDigits: 2 }).format(p)
    }
  }
}
</script>

<style scoped>
.home-page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1.5rem;
  max-width: 900px;
  margin: 0 auto;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.card-header h2 {
  font-size: 1.3rem;
  margin: 0;
}

.card-actions {
  display: flex;
  gap: 0.5rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  text-align: center;
}

.btn:disabled {
  opacity: 0.6;
}

.btn-primary {
  background: #4f46e5;
  color: white;
}

.btn-secondary {
  background: #f3f4f6;
  border: 2px solid #e5e7eb;
  color: #374151;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-edit {
  background: #f59e0b;
  color: white;
}

.filter-select {
  padding: 0.5rem 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.9rem;
  background: white;
}

.btn-refresh {
  width: 42px;
  height: 42px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
}

.refresh-icon {
  display: inline-block;
  transition: transform 0.3s ease;
}

.refresh-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.btn-small {
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
}

.message {
  margin-top: 1rem;
  padding: 1rem;
  border-radius: 8px;
}

.message.success {
  background: #dcfce7;
  color: #166534;
}

.message.error {
  background: #fee2e2;
  color: #991b1b;
}

.product-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.product-item {
  display: flex;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
  gap: 1rem;
}

.product-item:last-child {
  border-bottom: none;
}

.product-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.product-name {
  font-weight: 500;
}

.product-category {
  display: inline-block;
  font-size: 0.75rem;
  background: #e0e7ff;
  color: #4338ca;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-weight: 500;
}

.product-description {
  font-size: 0.85rem;
  color: #6b7280;
}

.product-quantity {
  color: #6b7280;
  min-width: 60px;
}

.product-price {
  color: #4f46e5;
  font-weight: 600;
  min-width: 100px;
  text-align: right;
}

.empty {
  text-align: center;
  color: #6b7280;
  padding: 2rem;
}

@media (max-width: 768px) {
  .home-page {
    padding: 1rem;
  }

  .card {
    padding: 1rem;
  }

  .card-header {
    flex-direction: column;
    align-items: stretch;
  }

  .card-actions {
    justify-content: stretch;
  }

  .card-actions .btn {
    flex: 1;
  }

  .product-item {
    flex-wrap: wrap;
    padding: 0.75rem;
  }

  .product-info {
    width: 100%;
    margin-bottom: 0.5rem;
  }

  .product-quantity,
  .product-price {
    min-width: auto;
  }

  .btn-small {
    margin-left: auto;
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .home-page {
    max-width: 800px;
  }
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  width: 90%;
  max-width: 400px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal h3 {
  margin: 0 0 1rem 0;
  font-size: 1.2rem;
}

.modal .form-group {
  margin-bottom: 1rem;
}

.modal .form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.25rem;
  font-size: 0.9rem;
}

.modal .form-group input,
.modal .form-group select,
.modal .form-group textarea {
  width: 100%;
  padding: 0.5rem;
  border: 2px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.9rem;
  box-sizing: border-box;
}

.modal .form-group input:focus,
.modal .form-group select:focus,
.modal .form-group textarea:focus {
  border-color: #4f46e5;
  outline: none;
}

.modal-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.modal-actions .btn {
  flex: 1;
  padding: 0.6rem 1rem;
}

@media (max-width: 768px) {
  .filter-select {
    width: 100%;
    margin-bottom: 0.5rem;
  }
}
</style>
