// =============================================================================
// useDocument Composable - API для работы с документами
// =============================================================================

import { ref } from 'vue'
import auth from '../services/auth'
import { getApiUrl } from '../utils/apiConfig'

/**
 * Composable для работы с документами (receipts, shipments, issue-acts, inventory-acts)
 *
 * @param {string} documentType - Тип документа: 'receipts', 'shipments', 'issue-acts', 'inventory-acts'
 * @returns {object} API методы и состояние
 */
export function useDocument(documentType) {
  const apiUrl = getApiUrl()
  const documents = ref([])
  const document = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Базовый URL для API
  const getBaseUrl = () => `${apiUrl}/${documentType}`

  /**
   * Получить все документы по объекту
   */
  const fetchAll = async (facilityId) => {
    loading.value = true
    error.value = null

    try {
      const response = await auth.authFetch(
        `${getBaseUrl()}/facility/${facilityId}`
      )

      if (!response.ok) {
        throw new Error(`Failed to fetch documents: ${response.status}`)
      }

      documents.value = await response.json()
      return { success: true, data: documents.value }
    } catch (err) {
      error.value = err.message
      console.error('Fetch documents error:', err)
      return { success: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  /**
   * Получить документ по ID
   */
  const fetchById = async (id) => {
    loading.value = true
    error.value = null

    try {
      const response = await auth.authFetch(`${getBaseUrl()}/${id}`)

      if (!response.ok) {
        throw new Error(`Failed to fetch document: ${response.status}`)
      }

      document.value = await response.json()
      return { success: true, data: document.value }
    } catch (err) {
      error.value = err.message
      console.error('Fetch document error:', err)
      return { success: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  /**
   * Создать новый документ
   */
  const create = async (data) => {
    loading.value = true
    error.value = null

    try {
      const response = await auth.authFetch(getBaseUrl(), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Failed to create document: ${response.status}`)
      }

      const created = await response.json()
      return { success: true, data: created }
    } catch (err) {
      error.value = err.message
      console.error('Create document error:', err)
      return { success: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  /**
   * Утвердить документ
   */
  const approve = async (id) => {
    loading.value = true
    error.value = null

    try {
      const response = await auth.authFetch(`${getBaseUrl()}/${id}/approve`, {
        method: 'POST'
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Failed to approve document: ${response.status}`)
      }

      const updated = await response.json()
      document.value = updated
      return { success: true, data: updated }
    } catch (err) {
      error.value = err.message
      console.error('Approve document error:', err)
      return { success: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  /**
   * Подтвердить документ (для receipts)
   */
  const confirm = async (id, data = null) => {
    loading.value = true
    error.value = null

    try {
      const options = {
        method: 'POST'
      }

      if (data) {
        options.headers = { 'Content-Type': 'application/json' }
        options.body = JSON.stringify(data)
      }

      const response = await auth.authFetch(`${getBaseUrl()}/${id}/confirm`, options)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Failed to confirm document: ${response.status}`)
      }

      const updated = await response.json()
      document.value = updated
      return { success: true, data: updated }
    } catch (err) {
      error.value = err.message
      console.error('Confirm document error:', err)
      return { success: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  /**
   * Завершить документ
   */
  const complete = async (id) => {
    loading.value = true
    error.value = null

    try {
      const response = await auth.authFetch(`${getBaseUrl()}/${id}/complete`, {
        method: 'POST'
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Failed to complete document: ${response.status}`)
      }

      const updated = await response.json()
      document.value = updated
      return { success: true, data: updated }
    } catch (err) {
      error.value = err.message
      console.error('Complete document error:', err)
      return { success: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  /**
   * Отгрузить документ (для shipments)
   */
  const ship = async (id) => {
    loading.value = true
    error.value = null

    try {
      const response = await auth.authFetch(`${getBaseUrl()}/${id}/ship`, {
        method: 'POST'
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Failed to ship document: ${response.status}`)
      }

      const updated = await response.json()
      document.value = updated
      return { success: true, data: updated }
    } catch (err) {
      error.value = err.message
      console.error('Ship document error:', err)
      return { success: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  /**
   * Доставить документ (для shipments)
   */
  const deliver = async (id) => {
    loading.value = true
    error.value = null

    try {
      const response = await auth.authFetch(`${getBaseUrl()}/${id}/deliver`, {
        method: 'POST'
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Failed to deliver document: ${response.status}`)
      }

      const updated = await response.json()
      document.value = updated
      return { success: true, data: updated }
    } catch (err) {
      error.value = err.message
      console.error('Deliver document error:', err)
      return { success: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  /**
   * Отменить документ (для shipments)
   */
  const cancel = async (id) => {
    loading.value = true
    error.value = null

    try {
      const response = await auth.authFetch(`${getBaseUrl()}/${id}/cancel`, {
        method: 'POST'
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Failed to cancel document: ${response.status}`)
      }

      const updated = await response.json()
      document.value = updated
      return { success: true, data: updated }
    } catch (err) {
      error.value = err.message
      console.error('Cancel document error:', err)
      return { success: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  /**
   * Удалить документ
   */
  const remove = async (id) => {
    loading.value = true
    error.value = null

    try {
      const response = await auth.authFetch(`${getBaseUrl()}/${id}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Failed to delete document: ${response.status}`)
      }

      return { success: true }
    } catch (err) {
      error.value = err.message
      console.error('Delete document error:', err)
      return { success: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    documents,
    document,
    loading,
    error,

    // Methods
    fetchAll,
    fetchById,
    create,
    approve,
    confirm,
    complete,
    ship,
    deliver,
    cancel,
    remove
  }
}
