<template>
  <div class="add-product-page">
    <section class="card">
      <h2>Добавить продукт</h2>
      <form class="form" @submit.prevent="createProduct">
        <div class="form-group">
          <label>Название</label>
          <input v-model="newProduct.name" type="text" required :disabled="loading">
        </div>
        <div class="form-group">
          <label>Количество</label>
          <input v-model.number="newProduct.quantity" type="number" min="0" required :disabled="loading">
        </div>
        <div class="form-group">
          <label>Цена</label>
          <input v-model.number="newProduct.price" type="number" step="0.01" min="0" required :disabled="loading">
        </div>
        <div class="form-group">
          <label>Категория</label>
          <select v-model="newProduct.category" :disabled="loading">
            <option value="">-- Выберите категорию --</option>
            <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>Описание <span class="char-count">{{ newProduct.description.length }}/100</span></label>
          <textarea
            v-model="newProduct.description"
            maxlength="100"
            rows="3"
            placeholder="Краткое описание товара"
            :disabled="loading"
          ></textarea>
        </div>
        <div class="form-actions">
          <button type="submit" class="btn btn-primary" :disabled="loading">
            {{ loading ? 'Сохранение...' : 'Создать' }}
          </button>
          <router-link to="/" class="btn btn-secondary">К списку</router-link>
        </div>
      </form>
      <div v-if="message" :class="['message', messageType]">{{ message }}</div>
    </section>
  </div>
</template>

<script>
import auth from '../services/auth'
import { getApiUrl } from '../utils/apiConfig'

export default {
  name: 'AddProductPage',

  data() {
    return {
      apiUrl: getApiUrl(),
      newProduct: { name: '', quantity: null, price: null, description: '', category: '' },
      categories: ['Электроника', 'Одежда', 'Продукты', 'Бытовая техника', 'Мебель', 'Другое'],
      loading: false,
      message: '',
      messageType: 'success'
    }
  },

  methods: {
    async createProduct() {
      if (!this.newProduct.name) {
        this.showMessage('Заполните поля', 'error')
        return
      }
      this.loading = true
      try {
        const r = await auth.authFetch(this.apiUrl + '/products', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.newProduct)
        })
        if (r.ok) {
          this.showMessage('Продукт создан!', 'success')
          this.newProduct = { name: '', quantity: null, price: null, description: '', category: '' }
          setTimeout(() => this.$router.push('/'), 1500)
        } else {
          this.showMessage('Ошибка создания', 'error')
        }
      } catch (e) {
        this.showMessage('Ошибка: ' + e.message, 'error')
      } finally {
        this.loading = false
      }
    },

    showMessage(text, type = 'success') {
      this.message = text
      this.messageType = type
      setTimeout(() => { this.message = '' }, 5000)
    }
  }
}
</script>

<style scoped>
.add-product-page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1.5rem;
  max-width: 600px;
  margin: 0 auto;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.card h2 {
  font-size: 1.3rem;
  margin-bottom: 1rem;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 600;
}

.form-group input,
.form-group select {
  padding: 0.75rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 1rem;
  background: white;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  border-color: #4f46e5;
  outline: none;
}

.form-group textarea {
  padding: 0.75rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 1rem;
  font-family: inherit;
  resize: vertical;
  min-height: 80px;
}

.char-count {
  font-weight: normal;
  font-size: 0.85rem;
  color: #6b7280;
  margin-left: 0.5rem;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
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

@media (max-width: 768px) {
  .add-product-page {
    padding: 1rem;
  }

  .card {
    padding: 1rem;
  }

  .form-actions {
    flex-direction: column;
  }

  .form-actions .btn {
    width: 100%;
  }
}
</style>
