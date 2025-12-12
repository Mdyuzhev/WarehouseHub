<template>
  <div class="facility-selector">
    <div class="dropdown" :class="{ open: isOpen }">
      <button @click="toggleDropdown" class="dropdown-toggle" data-testid="facility-selector">
        <span v-if="facilityStore.currentFacility" class="facility-display">
          <span class="facility-icon">{{ getFacilityIcon(facilityStore.facilityType) }}</span>
          <span class="facility-text" data-testid="facility-code">
            {{ facilityStore.currentFacility.code }} — {{ facilityStore.currentFacility.name }}
          </span>
        </span>
        <span v-else class="facility-placeholder">Выбрать объект</span>
        <span class="dropdown-arrow">▼</span>
      </button>

      <div v-if="isOpen" class="dropdown-menu">
        <div v-for="type in facilityTypes" :key="type" class="facility-group">
          <div class="group-header">{{ type }}</div>
          <button
            v-for="facility in getFacilitiesByType(type)"
            :key="facility.id"
            @click="selectFacility(facility)"
            class="dropdown-item"
            :class="{ active: facilityStore.currentFacility?.id === facility.id }"
            :data-testid="`facility-option-${facility.code}`"
          >
            <span class="facility-icon">{{ getFacilityIcon(type) }}</span>
            <span class="facility-info">
              <span class="facility-code">{{ facility.code }}</span>
              <span class="facility-name">{{ facility.name }}</span>
            </span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useFacilityStore } from '../stores/facility'

const router = useRouter()
const facilityStore = useFacilityStore()
const isOpen = ref(false)

const facilityTypes = ['DC', 'WH', 'PP']

onMounted(async () => {
  await facilityStore.fetchFacilities()
})

function getFacilitiesByType(type) {
  return facilityStore.facilities.filter(f => f.type === type)
}

function getFacilityIcon(type) {
  const icons = {
    DC: '🏭',
    WH: '📦',
    PP: '🏪'
  }
  return icons[type] || '📍'
}

function toggleDropdown() {
  isOpen.value = !isOpen.value
}

function selectFacility(facility) {
  facilityStore.setCurrentFacility(facility)
  isOpen.value = false

  // Navigate to facility dashboard
  const dashboardRoutes = {
    DC: '/dc',
    WH: '/wh',
    PP: '/pp'
  }
  const targetRoute = dashboardRoutes[facility.type]
  if (targetRoute) {
    router.push(targetRoute)
  }
}

// Закрыть dropdown при клике вне
function handleClickOutside(event) {
  const dropdown = event.target.closest('.facility-selector')
  if (!dropdown) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.facility-selector {
  position: relative;
  min-width: 280px;
}

.dropdown {
  position: relative;
}

.dropdown-toggle {
  width: 100%;
  padding: 10px 16px;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: all 0.2s;
  font-size: 14px;
}

.dropdown-toggle:hover {
  border-color: #9ca3af;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.dropdown.open .dropdown-toggle {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.facility-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.facility-icon {
  font-size: 18px;
}

.facility-text {
  font-weight: 500;
  color: #1f2937;
}

.facility-placeholder {
  color: #9ca3af;
}

.dropdown-arrow {
  color: #6b7280;
  font-size: 12px;
  transition: transform 0.2s;
}

.dropdown.open .dropdown-arrow {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  max-height: 400px;
  overflow-y: auto;
  z-index: 1000;
}

.facility-group {
  border-bottom: 1px solid #f3f4f6;
}

.facility-group:last-child {
  border-bottom: none;
}

.group-header {
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  background: #f9fafb;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.dropdown-item {
  width: 100%;
  padding: 12px 16px;
  border: none;
  background: none;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: background 0.15s;
  text-align: left;
}

.dropdown-item:hover {
  background: #f3f4f6;
}

.dropdown-item.active {
  background: #eff6ff;
  color: #1e40af;
}

.dropdown-item.active .facility-code {
  color: #1e40af;
  font-weight: 600;
}

.facility-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.facility-code {
  font-weight: 500;
  font-size: 13px;
  color: #1f2937;
}

.facility-name {
  font-size: 12px;
  color: #6b7280;
}
</style>
