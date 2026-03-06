<template>
  <div class="facility-selector">
    <div class="dropdown" :class="{ open: isOpen }">
      <button @click="toggleDropdown" class="dropdown-toggle" data-testid="facility-selector">
        <span v-if="facilityStore.currentFacility" class="facility-display">
          <span class="facility-icon" v-html="getFacilityIcon(facilityStore.facilityType)"></span>
          <span class="facility-text" data-testid="facility-code">
            {{ facilityStore.currentFacility.code }} — {{ facilityStore.currentFacility.name }}
          </span>
        </span>
        <span v-else class="facility-placeholder">Выбрать объект</span>
        <span class="dropdown-arrow"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m19.5 8.25-7.5 7.5-7.5-7.5"/></svg></span>
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
            <span class="facility-icon" v-html="getFacilityIcon(type)"></span>
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
  const svgAttrs = 'width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"'
  const icons = {
    DC: `<svg ${svgAttrs}><path d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008Zm0 3h.008v.008h-.008v-.008Zm0 3h.008v.008h-.008v-.008Z"/></svg>`,
    WH: `<svg ${svgAttrs}><path d="m20.25 7.5-.625 10.632a2.25 2.25 0 0 1-2.247 2.118H6.622a2.25 2.25 0 0 1-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125Z"/></svg>`,
    PP: `<svg ${svgAttrs}><path d="M13.5 21v-7.5a.75.75 0 0 1 .75-.75h3a.75.75 0 0 1 .75.75V21m-4.5 0H2.36m11.14 0H18m0 0h3.64m-1.39 0V9.349M3.75 21V9.349m0 0a3.001 3.001 0 0 0 3.75-.615A2.993 2.993 0 0 0 9.75 9.75c.896 0 1.7-.393 2.25-1.016a2.993 2.993 0 0 0 2.25 1.016 2.993 2.993 0 0 0 2.25-1.016 3.001 3.001 0 0 0 3.75.614m-16.5 0a3.004 3.004 0 0 1-.621-4.72l1.189-1.19A1.5 1.5 0 0 1 5.378 3h13.243a1.5 1.5 0 0 1 1.06.44l1.19 1.189a3 3 0 0 1-.621 4.72M6.75 18h3.75a.75.75 0 0 0 .75-.75V13.5a.75.75 0 0 0-.75-.75H6.75a.75.75 0 0 0-.75.75v3.75c0 .414.336.75.75.75Z"/></svg>`
  }
  return icons[type] || `<svg ${svgAttrs}><path d="M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"/><path d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1 1 15 0Z"/></svg>`
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
  display: flex;
  align-items: center;
  flex-shrink: 0;
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
  display: flex;
  align-items: center;
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
