<template>
  <div class="document-list">
    <div v-if="loading" class="loading">
      Загрузка...
    </div>

    <div v-else-if="documents.length === 0" class="empty">
      Нет документов
    </div>

    <table v-else class="documents-table">
      <thead>
        <tr>
          <th @click="toggleSort('documentNumber')" class="sortable">
            № документа
            <span class="sort-icon">{{ getSortIcon('documentNumber') }}</span>
          </th>
          <th @click="toggleSort('createdAt')" class="sortable">
            Дата
            <span class="sort-icon">{{ getSortIcon('createdAt') }}</span>
          </th>
          <th>Статус</th>
          <th>Позиций</th>
          <th>Количество</th>
          <th>Действия</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="doc in sortedDocuments" :key="doc.id">
          <td class="doc-number">{{ doc.documentNumber }}</td>
          <td>{{ formatDate(doc.createdAt) }}</td>
          <td>
            <DocumentStatusBadge :status="doc.status" :type="type" />
          </td>
          <td class="text-center">{{ doc.items?.length || 0 }}</td>
          <td class="text-center">{{ calculateTotalQuantity(doc.items) }}</td>
          <td class="actions">
            <button
              class="btn btn-small btn-view"
              @click="$emit('view', doc.id)"
              title="Просмотр"
            >
              👁️
            </button>
            <button
              v-if="doc.status === 'DRAFT'"
              class="btn btn-small btn-edit"
              @click="$emit('edit', doc.id)"
              title="Редактировать"
            >
              ✏️
            </button>
            <button
              v-if="hasActions(doc)"
              class="btn btn-small btn-action"
              @click="$emit('action', { id: doc.id, action: 'menu' })"
              title="Действия"
            >
              ⋮
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import DocumentStatusBadge from './DocumentStatusBadge.vue'

export default {
  name: 'DocumentList',

  components: {
    DocumentStatusBadge
  },

  props: {
    documents: {
      type: Array,
      required: true,
      default: () => []
    },
    type: {
      type: String,
      required: true,
      validator: (value) => ['receipt', 'shipment', 'issue', 'inventory'].includes(value)
    },
    loading: {
      type: Boolean,
      default: false
    }
  },

  emits: ['view', 'edit', 'action'],

  data() {
    return {
      sortBy: 'createdAt',
      sortDesc: true
    }
  },

  computed: {
    sortedDocuments() {
      const docs = [...this.documents]

      docs.sort((a, b) => {
        let aVal = a[this.sortBy]
        let bVal = b[this.sortBy]

        if (this.sortBy === 'createdAt') {
          aVal = new Date(aVal).getTime()
          bVal = new Date(bVal).getTime()
        }

        if (aVal < bVal) return this.sortDesc ? 1 : -1
        if (aVal > bVal) return this.sortDesc ? -1 : 1
        return 0
      })

      return docs
    }
  },

  methods: {
    toggleSort(field) {
      if (this.sortBy === field) {
        this.sortDesc = !this.sortDesc
      } else {
        this.sortBy = field
        this.sortDesc = true
      }
    },

    getSortIcon(field) {
      if (this.sortBy !== field) return '↕'
      return this.sortDesc ? '↓' : '↑'
    },

    formatDate(dateStr) {
      if (!dateStr) return '-'
      const date = new Date(dateStr)
      return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      })
    },

    calculateTotalQuantity(items) {
      if (!items || items.length === 0) return 0
      return items.reduce((sum, item) => {
        const qty = item.quantity || item.expectedQuantity || 0
        return sum + qty
      }, 0)
    },

    hasActions(doc) {
      // Показываем кнопку действий если статус не финальный
      const finalStatuses = ['COMPLETED', 'DELIVERED']
      return !finalStatuses.includes(doc.status)
    }
  }
}
</script>

<style scoped>
.document-list {
  width: 100%;
}

.loading,
.empty {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

.documents-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.documents-table thead {
  background: #f9fafb;
  border-bottom: 2px solid #e5e7eb;
}

.documents-table th {
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.875rem;
  color: #374151;
  white-space: nowrap;
}

.documents-table th.sortable {
  cursor: pointer;
  user-select: none;
}

.documents-table th.sortable:hover {
  background: #f3f4f6;
}

.sort-icon {
  display: inline-block;
  margin-left: 0.25rem;
  opacity: 0.5;
  font-size: 0.75rem;
}

.documents-table th.sortable:hover .sort-icon {
  opacity: 1;
}

.documents-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #f3f4f6;
  font-size: 0.875rem;
}

.documents-table tbody tr:hover {
  background: #f9fafb;
}

.doc-number {
  font-weight: 500;
  color: #4f46e5;
}

.text-center {
  text-align: center;
}

.actions {
  display: flex;
  gap: 0.25rem;
  justify-content: flex-end;
}

.btn {
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-small {
  padding: 0.375rem 0.5rem;
  font-size: 0.875rem;
}

.btn-view {
  background: #e0e7ff;
  color: #4338ca;
}

.btn-view:hover {
  background: #c7d2fe;
}

.btn-edit {
  background: #fed7aa;
  color: #9a3412;
}

.btn-edit:hover {
  background: #fdba74;
}

.btn-action {
  background: #f3f4f6;
  color: #374151;
  font-weight: 700;
  line-height: 1;
}

.btn-action:hover {
  background: #e5e7eb;
}

@media (max-width: 768px) {
  .documents-table {
    font-size: 0.75rem;
  }

  .documents-table th,
  .documents-table td {
    padding: 0.5rem;
  }

  .btn-small {
    padding: 0.25rem 0.375rem;
    font-size: 0.75rem;
  }
}
</style>
