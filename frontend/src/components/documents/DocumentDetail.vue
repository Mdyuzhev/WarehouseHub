<template>
  <div class="document-detail">
    <div v-if="!document" class="empty">
      Документ не найден
    </div>

    <div v-else class="detail-container">
      <!-- Header -->
      <div class="detail-header">
        <div class="header-left">
          <h2 class="doc-title">{{ documentTitle }}</h2>
          <p class="doc-number">{{ document.documentNumber }}</p>
        </div>
        <div class="header-right">
          <DocumentStatusBadge :status="document.status" :type="type" />
        </div>
      </div>

      <!-- Info Section -->
      <div class="detail-section">
        <h3 class="section-title">Информация</h3>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">Дата создания:</span>
            <span class="info-value">{{ formatDate(document.createdAt) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Объект:</span>
            <span class="info-value">{{ document.facilityName || '-' }}</span>
          </div>
          <div v-if="document.supplierName" class="info-item">
            <span class="info-label">Поставщик:</span>
            <span class="info-value">{{ document.supplierName }}</span>
          </div>
          <div v-if="document.destination" class="info-item">
            <span class="info-label">Получатель:</span>
            <span class="info-value">{{ document.destination }}</span>
          </div>
          <div v-if="document.notes" class="info-item full-width">
            <span class="info-label">Примечания:</span>
            <span class="info-value">{{ document.notes }}</span>
          </div>
        </div>
      </div>

      <!-- Items Table -->
      <div class="detail-section">
        <h3 class="section-title">Позиции документа</h3>
        <DocumentItemsTable
          :items="document.items || []"
          :type="type"
          :editable="false"
        />
      </div>

      <!-- History Timeline -->
      <div v-if="document.history && document.history.length > 0" class="detail-section">
        <h3 class="section-title">История изменений</h3>
        <div class="timeline">
          <div
            v-for="(event, idx) in document.history"
            :key="idx"
            class="timeline-item"
          >
            <div class="timeline-marker"></div>
            <div class="timeline-content">
              <div class="timeline-status">{{ event.status }}</div>
              <div class="timeline-date">{{ formatDateTime(event.timestamp) }}</div>
              <div v-if="event.username" class="timeline-user">{{ event.username }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="detail-section">
        <DocumentActions
          :document="document"
          :type="type"
          @action="$emit('action', $event)"
        />
      </div>
    </div>
  </div>
</template>

<script>
import DocumentStatusBadge from './DocumentStatusBadge.vue'
import DocumentItemsTable from './DocumentItemsTable.vue'
import DocumentActions from './DocumentActions.vue'

export default {
  name: 'DocumentDetail',

  components: {
    DocumentStatusBadge,
    DocumentItemsTable,
    DocumentActions
  },

  props: {
    document: {
      type: Object,
      default: null
    },
    type: {
      type: String,
      required: true,
      validator: (value) => ['receipt', 'shipment', 'issue', 'inventory'].includes(value)
    }
  },

  emits: ['action'],

  computed: {
    documentTitle() {
      const titles = {
        'receipt': 'Приходная накладная',
        'shipment': 'Расходная накладная',
        'issue': 'Акт списания',
        'inventory': 'Акт инвентаризации'
      }
      return titles[this.type] || 'Документ'
    }
  },

  methods: {
    formatDate(dateStr) {
      if (!dateStr) return '-'
      const date = new Date(dateStr)
      return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      })
    },

    formatDateTime(dateStr) {
      if (!dateStr) return '-'
      const date = new Date(dateStr)
      return date.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
  }
}
</script>

<style scoped>
.document-detail {
  width: 100%;
}

.empty {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

.detail-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1.5rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.header-left {
  flex: 1;
}

.doc-title {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #111827;
}

.doc-number {
  margin: 0;
  font-size: 0.875rem;
  color: #6b7280;
}

.detail-section {
  padding: 1.5rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.section-title {
  margin: 0 0 1rem 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #374151;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.info-value {
  font-size: 0.875rem;
  color: #111827;
}

/* Timeline */
.timeline {
  position: relative;
  padding-left: 2rem;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 0.5rem;
  top: 0.5rem;
  bottom: 0.5rem;
  width: 2px;
  background: #e5e7eb;
}

.timeline-item {
  position: relative;
  padding-bottom: 1.5rem;
}

.timeline-item:last-child {
  padding-bottom: 0;
}

.timeline-marker {
  position: absolute;
  left: -1.5rem;
  top: 0.25rem;
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 50%;
  background: #4f46e5;
  border: 2px solid white;
  box-shadow: 0 0 0 2px #e5e7eb;
}

.timeline-content {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.timeline-status {
  font-weight: 600;
  color: #111827;
  font-size: 0.875rem;
}

.timeline-date {
  font-size: 0.75rem;
  color: #6b7280;
}

.timeline-user {
  font-size: 0.75rem;
  color: #4f46e5;
}

@media (max-width: 768px) {
  .detail-header {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }

  .detail-section {
    padding: 1rem;
  }

  .doc-title {
    font-size: 1.25rem;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
