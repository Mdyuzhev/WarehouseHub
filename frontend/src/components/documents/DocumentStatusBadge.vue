<template>
  <span :class="['status-badge', statusClass]" data-testid="status-badge">
    <span class="status-icon">{{ statusIcon }}</span>
    <span class="status-text">{{ statusText }}</span>
  </span>
</template>

<script>
export default {
  name: 'DocumentStatusBadge',

  props: {
    status: {
      type: String,
      required: true,
      validator: (value) => [
        'DRAFT', 'APPROVED', 'CONFIRMED', 'COMPLETED', 'SHIPPED', 'DELIVERED'
      ].includes(value)
    },
    type: {
      type: String,
      required: true,
      validator: (value) => ['receipt', 'shipment', 'issue', 'inventory'].includes(value)
    }
  },

  computed: {
    statusClass() {
      const classes = {
        'DRAFT': 'status-draft',
        'APPROVED': 'status-approved',
        'CONFIRMED': 'status-confirmed',
        'COMPLETED': 'status-completed',
        'SHIPPED': 'status-shipped',
        'DELIVERED': 'status-delivered'
      }
      return classes[this.status] || 'status-draft'
    },

    statusIcon() {
      const icons = {
        'DRAFT': '✏️',
        'APPROVED': '✓',
        'CONFIRMED': '✓✓',
        'COMPLETED': '✓✓✓',
        'SHIPPED': '🚚',
        'DELIVERED': '📦'
      }
      return icons[this.status] || '•'
    },

    statusText() {
      const texts = {
        'DRAFT': 'Черновик',
        'APPROVED': 'Утверждён',
        'CONFIRMED': 'Подтверждён',
        'COMPLETED': 'Завершён',
        'SHIPPED': 'Отгружен',
        'DELIVERED': 'Доставлен'
      }
      return texts[this.status] || this.status
    }
  }
}
</script>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.status-icon {
  font-size: 0.875rem;
  line-height: 1;
}

.status-text {
  line-height: 1;
}

/* Colors by status */
.status-draft {
  background: #f3f4f6;
  color: #6b7280;
}

.status-approved {
  background: #dbeafe;
  color: #1e40af;
}

.status-confirmed {
  background: #d1fae5;
  color: #065f46;
}

.status-completed {
  background: #6ee7b7;
  color: #064e3b;
}

.status-shipped {
  background: #fed7aa;
  color: #9a3412;
}

.status-delivered {
  background: #d1fae5;
  color: #065f46;
}
</style>
