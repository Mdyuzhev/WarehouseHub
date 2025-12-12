<template>
  <div class="items-table">
    <div v-if="items.length === 0" class="empty">
      Нет позиций
    </div>

    <table v-else class="table">
      <thead>
        <tr>
          <th>Товар</th>
          <th v-if="showExpected" class="text-right">
            {{ expectedLabel }}
          </th>
          <th v-if="showActual" class="text-right">
            {{ actualLabel }}
          </th>
          <th v-if="showSimpleQty" class="text-right">Количество</th>
          <th v-if="showDifference" class="text-right">Разница</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, idx) in items" :key="idx">
          <td class="product-name">
            {{ item.productName || item.product?.name || '-' }}
          </td>

          <!-- Expected quantity -->
          <td v-if="showExpected" class="text-right">
            {{ item.expectedQuantity || 0 }}
          </td>

          <!-- Actual quantity (editable or readonly) -->
          <td v-if="showActual" class="text-right">
            <input
              v-if="editable"
              v-model.number="item.actualQuantity"
              type="number"
              min="0"
              class="qty-input"
              @input="$emit('update:items', items)"
            >
            <span v-else>{{ item.actualQuantity || 0 }}</span>
          </td>

          <!-- Simple quantity (for shipments) -->
          <td v-if="showSimpleQty" class="text-right">
            {{ item.quantity || 0 }}
          </td>

          <!-- Difference -->
          <td v-if="showDifference" class="text-right" :class="getDifferenceClass(item)">
            {{ calculateDifference(item) }}
          </td>
        </tr>
      </tbody>

      <!-- Summary row -->
      <tfoot v-if="showSummary">
        <tr>
          <td class="summary-label">Итого:</td>
          <td v-if="showExpected" class="text-right summary-value">
            {{ totalExpected }}
          </td>
          <td v-if="showActual" class="text-right summary-value">
            {{ totalActual }}
          </td>
          <td v-if="showSimpleQty" class="text-right summary-value">
            {{ totalQuantity }}
          </td>
          <td v-if="showDifference" class="text-right summary-value" :class="totalDifferenceClass">
            {{ totalDifference }}
          </td>
        </tr>
      </tfoot>
    </table>
  </div>
</template>

<script>
export default {
  name: 'DocumentItemsTable',

  props: {
    items: {
      type: Array,
      required: true,
      default: () => []
    },
    type: {
      type: String,
      required: true,
      validator: (value) => ['receipt', 'shipment', 'issue', 'inventory'].includes(value)
    },
    editable: {
      type: Boolean,
      default: false
    }
  },

  emits: ['update:items'],

  computed: {
    showExpected() {
      return this.type === 'receipt' || this.type === 'inventory'
    },

    showActual() {
      return this.type === 'receipt' || this.type === 'inventory'
    },

    showSimpleQty() {
      return this.type === 'shipment' || this.type === 'issue'
    },

    showDifference() {
      return this.type === 'receipt' || this.type === 'inventory'
    },

    showSummary() {
      return this.items.length > 0
    },

    expectedLabel() {
      return this.type === 'inventory' ? 'По системе' : 'Ожидаемое'
    },

    actualLabel() {
      return this.type === 'inventory' ? 'Фактически' : 'Фактическое'
    },

    totalExpected() {
      return this.items.reduce((sum, item) => sum + (item.expectedQuantity || 0), 0)
    },

    totalActual() {
      return this.items.reduce((sum, item) => sum + (item.actualQuantity || 0), 0)
    },

    totalQuantity() {
      return this.items.reduce((sum, item) => sum + (item.quantity || 0), 0)
    },

    totalDifference() {
      const diff = this.totalActual - this.totalExpected
      return diff > 0 ? `+${diff}` : diff
    },

    totalDifferenceClass() {
      const diff = this.totalActual - this.totalExpected
      if (diff > 0) return 'difference-positive'
      if (diff < 0) return 'difference-negative'
      return ''
    }
  },

  methods: {
    calculateDifference(item) {
      const expected = item.expectedQuantity || 0
      const actual = item.actualQuantity || 0
      const diff = actual - expected

      if (diff === 0) return '0'
      return diff > 0 ? `+${diff}` : diff
    },

    getDifferenceClass(item) {
      const expected = item.expectedQuantity || 0
      const actual = item.actualQuantity || 0

      if (actual > expected) return 'difference-positive'
      if (actual < expected) return 'difference-negative'
      return ''
    }
  }
}
</script>

<style scoped>
.items-table {
  width: 100%;
  overflow-x: auto;
}

.empty {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

.table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.table thead {
  background: #f9fafb;
  border-bottom: 2px solid #e5e7eb;
}

.table th {
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.875rem;
  color: #374151;
  white-space: nowrap;
}

.table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #f3f4f6;
  font-size: 0.875rem;
}

.table tbody tr:hover {
  background: #f9fafb;
}

.table tfoot {
  background: #f9fafb;
  border-top: 2px solid #e5e7eb;
  font-weight: 600;
}

.text-right {
  text-align: right;
}

.product-name {
  font-weight: 500;
  color: #111827;
}

.qty-input {
  width: 100%;
  max-width: 100px;
  padding: 0.375rem 0.5rem;
  border: 2px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.875rem;
  text-align: right;
}

.qty-input:focus {
  border-color: #4f46e5;
  outline: none;
}

.difference-positive {
  color: #16a34a;
  font-weight: 600;
}

.difference-negative {
  color: #dc2626;
  font-weight: 600;
}

.summary-label {
  font-weight: 600;
  color: #374151;
}

.summary-value {
  font-weight: 600;
  color: #111827;
}

@media (max-width: 768px) {
  .table {
    font-size: 0.75rem;
  }

  .table th,
  .table td {
    padding: 0.5rem;
  }

  .qty-input {
    max-width: 80px;
    font-size: 0.75rem;
  }
}
</style>
