// =============================================================================
// Facility Store - управление текущим объектом (DC/WH/PP)
// =============================================================================

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// API URL
function getApi() {
  // eslint-disable-next-line no-new-func
  const getUrl = new Function('return window.__API_URL__')
  return getUrl() || '/api'
}

const FACILITY_KEY = 'warehouse_current_facility'

export const useFacilityStore = defineStore('facility', () => {
  // State
  const currentFacility = ref(null)
  const facilities = ref([])
  const loading = ref(false)

  // Восстановить из localStorage при инициализации
  const stored = localStorage.getItem(FACILITY_KEY)
  if (stored) {
    try {
      currentFacility.value = JSON.parse(stored)
    } catch (e) {
      console.error('Failed to parse stored facility:', e)
    }
  }

  // Getters
  const facilityType = computed(() => {
    return currentFacility.value?.type || null
  })

  const facilityCode = computed(() => {
    return currentFacility.value?.code || null
  })

  const hasFacility = computed(() => {
    return currentFacility.value !== null
  })

  // Actions
  async function fetchFacilities() {
    loading.value = true
    try {
      const token = localStorage.getItem('warehouse_auth_token')
      const response = await fetch(`${getApi()}/facilities`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch facilities')
      }

      facilities.value = await response.json()
      return { success: true }
    } catch (error) {
      console.error('Fetch facilities error:', error)
      return { success: false, error: error.message }
    } finally {
      loading.value = false
    }
  }

  function setCurrentFacility(facility) {
    currentFacility.value = facility
    // Сохранить в localStorage
    if (facility) {
      localStorage.setItem(FACILITY_KEY, JSON.stringify(facility))
    } else {
      localStorage.removeItem(FACILITY_KEY)
    }
  }

  function clearFacility() {
    currentFacility.value = null
    localStorage.removeItem(FACILITY_KEY)
  }

  return {
    // State
    currentFacility,
    facilities,
    loading,
    // Getters
    facilityType,
    facilityCode,
    hasFacility,
    // Actions
    fetchFacilities,
    setCurrentFacility,
    clearFacility
  }
})
