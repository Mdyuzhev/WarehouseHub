// =============================================================================
// useFormValidation Composable - валидация форм документов
// =============================================================================

import { ref, computed } from 'vue'

/**
 * Composable для валидации форм документов
 *
 * @param {object} rules - Правила валидации
 * @returns {object} Методы валидации и состояние ошибок
 */
export function useFormValidation(rules = {}) {
  const errors = ref({})

  /**
   * Проверка всех правил
   */
  const validate = (formData) => {
    errors.value = {}
    let valid = true

    // Валидация facilityId
    if (rules.facilityId && rules.facilityId.required) {
      if (!formData.facilityId) {
        errors.value.facilityId = 'Объект обязателен для выбора'
        valid = false
      }
    }

    // Валидация items
    if (rules.items) {
      if (rules.items.required) {
        if (!formData.items || formData.items.length === 0) {
          errors.value.items = 'Необходимо добавить хотя бы одну позицию'
          valid = false
        }
      }

      if (rules.items.min && formData.items) {
        if (formData.items.length < rules.items.min) {
          errors.value.items = `Минимум ${rules.items.min} позиций`
          valid = false
        }
      }

      // Валидация каждой позиции
      if (formData.items && formData.items.length > 0) {
        formData.items.forEach((item, index) => {
          // Проверка productId
          if (rules.itemProductId && rules.itemProductId.required) {
            if (!item.productId && !item.product?.id) {
              errors.value[`item_${index}_product`] = 'Товар обязателен'
              valid = false
            }
          }

          // Проверка quantity
          if (rules.itemQuantity) {
            const qty = item.quantity || item.expectedQuantity || 0

            if (rules.itemQuantity.required && (!qty || qty <= 0)) {
              errors.value[`item_${index}_quantity`] = 'Количество обязательно'
              valid = false
            }

            if (rules.itemQuantity.min !== undefined && qty < rules.itemQuantity.min) {
              errors.value[`item_${index}_quantity`] = `Минимум ${rules.itemQuantity.min}`
              valid = false
            }

            if (rules.itemQuantity.max !== undefined && qty > rules.itemQuantity.max) {
              errors.value[`item_${index}_quantity`] = `Максимум ${rules.itemQuantity.max}`
              valid = false
            }
          }
        })
      }
    }

    // Валидация supplierName
    if (rules.supplierName) {
      if (rules.supplierName.required && !formData.supplierName) {
        errors.value.supplierName = 'Поставщик обязателен'
        valid = false
      }

      if (rules.supplierName.maxLength && formData.supplierName) {
        if (formData.supplierName.length > rules.supplierName.maxLength) {
          errors.value.supplierName = `Максимум ${rules.supplierName.maxLength} символов`
          valid = false
        }
      }
    }

    // Валидация destination
    if (rules.destination) {
      if (rules.destination.required && !formData.destination) {
        errors.value.destination = 'Получатель обязателен'
        valid = false
      }

      if (rules.destination.maxLength && formData.destination) {
        if (formData.destination.length > rules.destination.maxLength) {
          errors.value.destination = `Максимум ${rules.destination.maxLength} символов`
          valid = false
        }
      }
    }

    // Валидация notes
    if (rules.notes && rules.notes.maxLength && formData.notes) {
      if (formData.notes.length > rules.notes.maxLength) {
        errors.value.notes = `Максимум ${rules.notes.maxLength} символов`
        valid = false
      }
    }

    return valid
  }

  /**
   * Валидация отдельного поля
   */
  const validateField = (fieldName, value, fieldRules) => {
    if (!fieldRules) return true

    delete errors.value[fieldName]

    if (fieldRules.required && !value) {
      errors.value[fieldName] = 'Обязательное поле'
      return false
    }

    if (fieldRules.min !== undefined && value < fieldRules.min) {
      errors.value[fieldName] = `Минимум ${fieldRules.min}`
      return false
    }

    if (fieldRules.max !== undefined && value > fieldRules.max) {
      errors.value[fieldName] = `Максимум ${fieldRules.max}`
      return false
    }

    if (fieldRules.maxLength !== undefined && value && value.length > fieldRules.maxLength) {
      errors.value[fieldName] = `Максимум ${fieldRules.maxLength} символов`
      return false
    }

    if (fieldRules.pattern && !fieldRules.pattern.test(value)) {
      errors.value[fieldName] = fieldRules.message || 'Неверный формат'
      return false
    }

    return true
  }

  /**
   * Очистить ошибки
   */
  const clearErrors = () => {
    errors.value = {}
  }

  /**
   * Очистить ошибку конкретного поля
   */
  const clearFieldError = (fieldName) => {
    delete errors.value[fieldName]
  }

  /**
   * Установить ошибку вручную
   */
  const setError = (fieldName, message) => {
    errors.value[fieldName] = message
  }

  /**
   * Проверка валидности формы
   */
  const isValid = computed(() => {
    return Object.keys(errors.value).length === 0
  })

  /**
   * Есть ли ошибка у поля
   */
  const hasError = (fieldName) => {
    return !!errors.value[fieldName]
  }

  /**
   * Получить ошибку поля
   */
  const getError = (fieldName) => {
    return errors.value[fieldName]
  }

  return {
    errors,
    isValid,
    validate,
    validateField,
    clearErrors,
    clearFieldError,
    setError,
    hasError,
    getError
  }
}

/**
 * Готовые правила валидации для разных типов документов
 */
export const documentValidationRules = {
  // Правила для Receipt (приходная накладная)
  receipt: {
    facilityId: { required: true },
    items: { required: true, min: 1 },
    itemProductId: { required: true },
    itemQuantity: { required: true, min: 1 },
    supplierName: { maxLength: 255 },
    notes: { maxLength: 1000 }
  },

  // Правила для Shipment (расходная накладная)
  shipment: {
    facilityId: { required: true },
    items: { required: true, min: 1 },
    itemProductId: { required: true },
    itemQuantity: { required: true, min: 1 },
    destination: { required: true, maxLength: 255 },
    notes: { maxLength: 1000 }
  },

  // Правила для Issue Act (акт списания)
  issue: {
    facilityId: { required: true },
    items: { required: true, min: 1 },
    itemProductId: { required: true },
    itemQuantity: { required: true, min: 1 },
    notes: { maxLength: 1000 }
  },

  // Правила для Inventory Act (акт инвентаризации)
  inventory: {
    facilityId: { required: true },
    items: { required: true, min: 1 },
    itemProductId: { required: true },
    itemQuantity: { required: true, min: 0 },
    notes: { maxLength: 1000 }
  }
}
