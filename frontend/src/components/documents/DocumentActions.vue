<template>
  <div class="document-actions">
    <div v-if="availableActions.length === 0" class="no-actions">
      Нет доступных действий
    </div>

    <div v-else class="actions-container">
      <button
        v-for="action in availableActions"
        :key="action.key"
        :class="['btn', action.class]"
        :data-testid="`${action.key}-button`"
        @click="handleAction(action.key)"
      >
        {{ action.label }}
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DocumentActions',

  props: {
    document: {
      type: Object,
      required: true
    },
    type: {
      type: String,
      required: true,
      validator: (value) => ['receipt', 'shipment', 'issue', 'inventory'].includes(value)
    }
  },

  emits: ['action'],

  computed: {
    availableActions() {
      const status = this.document.status
      const actions = []

      // Receipt actions
      if (this.type === 'receipt') {
        if (status === 'DRAFT') {
          actions.push(
            { key: 'edit', label: 'Редактировать', class: 'btn-secondary' },
            { key: 'delete', label: 'Удалить', class: 'btn-danger' },
            { key: 'approve', label: 'Утвердить', class: 'btn-primary' }
          )
        } else if (status === 'APPROVED') {
          actions.push(
            { key: 'confirm', label: 'Подтвердить', class: 'btn-primary' }
          )
        } else if (status === 'CONFIRMED') {
          actions.push(
            { key: 'complete', label: 'Завершить', class: 'btn-primary' }
          )
        }
      }

      // Shipment actions
      if (this.type === 'shipment') {
        if (status === 'DRAFT') {
          actions.push(
            { key: 'edit', label: 'Редактировать', class: 'btn-secondary' },
            { key: 'delete', label: 'Удалить', class: 'btn-danger' },
            { key: 'approve', label: 'Утвердить', class: 'btn-primary' }
          )
        } else if (status === 'APPROVED') {
          actions.push(
            { key: 'ship', label: 'Отгрузить', class: 'btn-primary' },
            { key: 'cancel', label: 'Отменить', class: 'btn-danger' }
          )
        } else if (status === 'SHIPPED') {
          actions.push(
            { key: 'deliver', label: 'Доставлено', class: 'btn-primary' }
          )
        }
      }

      // Issue act actions
      if (this.type === 'issue') {
        if (status === 'DRAFT') {
          actions.push(
            { key: 'edit', label: 'Редактировать', class: 'btn-secondary' },
            { key: 'delete', label: 'Удалить', class: 'btn-danger' },
            { key: 'complete', label: 'Завершить', class: 'btn-primary' }
          )
        }
      }

      // Inventory act actions
      if (this.type === 'inventory') {
        if (status === 'DRAFT') {
          actions.push(
            { key: 'edit', label: 'Редактировать', class: 'btn-secondary' },
            { key: 'delete', label: 'Удалить', class: 'btn-danger' },
            { key: 'approve', label: 'Утвердить', class: 'btn-primary' }
          )
        } else if (status === 'APPROVED') {
          actions.push(
            { key: 'complete', label: 'Завершить', class: 'btn-primary' }
          )
        }
      }

      return actions
    }
  },

  methods: {
    handleAction(action) {
      // Confirm destructive actions
      if (action === 'delete' || action === 'cancel') {
        const confirmText = action === 'delete'
          ? 'Удалить документ?'
          : 'Отменить документ?'

        if (!confirm(confirmText)) {
          return
        }
      }

      this.$emit('action', {
        action,
        documentId: this.document.id
      })
    }
  }
}
</script>

<style scoped>
.document-actions {
  width: 100%;
}

.no-actions {
  text-align: center;
  padding: 1rem;
  color: #6b7280;
  font-size: 0.875rem;
}

.actions-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: flex-end;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.btn:active {
  transform: translateY(0);
}

.btn-primary {
  background: #4f46e5;
  color: white;
}

.btn-primary:hover {
  background: #4338ca;
}

.btn-secondary {
  background: #f3f4f6;
  border: 2px solid #e5e7eb;
  color: #374151;
}

.btn-secondary:hover {
  background: #e5e7eb;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover {
  background: #dc2626;
}

@media (max-width: 768px) {
  .actions-container {
    flex-direction: column;
  }

  .btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
