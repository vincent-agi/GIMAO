/**
 * Composable pour validation de formulaire par schéma
 * Supporte les formulaires simples et multi-steps
 */

import { ref, computed } from 'vue'
import { useValidationRules } from './useValidationRules'

export function useFormValidation(schema, options = {}) {
  const rules = useValidationRules()
  const errors = ref({})
  const currentStep = ref(options.initialStep || 1)

  /**
   * Construit les règles Vuetify pour un champ donné
   * @param {string} fieldName - Nom du champ
   * @param {number|null} step - Numéro de l'étape (null pour formulaires simples)
   * @returns {Array} - Tableau de règles Vuetify
   */
  const getFieldRules = (fieldName, step = null) => {
    let fieldSchema

    if (step !== null && schema[`step${step}`]) {
      // Formulaire multi-steps
      fieldSchema = schema[`step${step}`]?.[fieldName]
    } else {
      // Formulaire simple
      fieldSchema = schema[fieldName]
    }

    if (!fieldSchema) return []

    const fieldRules = []

    // Si le schéma est un tableau de noms de règles
    if (Array.isArray(fieldSchema)) {
      fieldSchema.forEach((rule) => {
        if (typeof rule === 'string') {
          // Règle simple : 'required', 'email', etc.
          if (rules[rule]) {
            fieldRules.push(rules[rule]())
          }
        } else if (typeof rule === 'object') {
          // Règle avec paramètres : { name: 'minLength', params: [3] }
          const ruleName = rule.name
          const params = rule.params || []
          const message = rule.message

          if (rules[ruleName]) {
            fieldRules.push(rules[ruleName](...params, message))
          }
        } else if (typeof rule === 'function') {
          // Règle personnalisée
          fieldRules.push(rule)
        }
      })
    }
    // Si le schéma est un objet avec propriétés
    else if (typeof fieldSchema === 'object') {
      Object.entries(fieldSchema).forEach(([ruleName, ruleConfig]) => {
        if (ruleName === 'required' && ruleConfig) {
          const message = typeof ruleConfig === 'string' ? ruleConfig : undefined
          fieldRules.push(rules.required(message))
        } else if (ruleName === 'email' && ruleConfig) {
          const message = typeof ruleConfig === 'string' ? ruleConfig : undefined
          fieldRules.push(rules.email(message))
        } else if (ruleName === 'minLength') {
          const min = typeof ruleConfig === 'number' ? ruleConfig : ruleConfig.value
          const message = ruleConfig.message
          fieldRules.push(rules.minLength(min, message))
        } else if (ruleName === 'maxLength') {
          const max = typeof ruleConfig === 'number' ? ruleConfig : ruleConfig.value
          const message = ruleConfig.message
          fieldRules.push(rules.maxLength(max, message))
        } else if (ruleName === 'numeric' && ruleConfig) {
          const message = typeof ruleConfig === 'string' ? ruleConfig : undefined
          fieldRules.push(rules.numeric(message))
        } else if (ruleName === 'positive' && ruleConfig) {
          const message = typeof ruleConfig === 'string' ? ruleConfig : undefined
          fieldRules.push(rules.positive(message))
        } else if (ruleName === 'min') {
          const min = typeof ruleConfig === 'number' ? ruleConfig : ruleConfig.value
          const message = ruleConfig.message
          fieldRules.push(rules.min(min, message))
        } else if (ruleName === 'max') {
          const max = typeof ruleConfig === 'number' ? ruleConfig : ruleConfig.value
          const message = ruleConfig.message
          fieldRules.push(rules.max(max, message))
        } else if (ruleName === 'pattern') {
          const regex = ruleConfig.value
          const message = ruleConfig.message
          fieldRules.push(rules.pattern(regex, message))
        } else if (ruleName === 'custom' && typeof ruleConfig === 'function') {
          fieldRules.push(ruleConfig)
        }
      })
    }

    return fieldRules
  }

  /**
   * Valide un champ spécifique
   * @param {string} fieldName - Nom du champ
   * @param {any} value - Valeur du champ
   * @param {number|null} step - Numéro de l'étape
   * @returns {boolean} - true si valide
   */
  const validateField = (fieldName, value, step = null) => {
    const fieldRules = getFieldRules(fieldName, step)
    errors.value[fieldName] = []

    for (const rule of fieldRules) {
      const result = rule(value)
      if (result !== true) {
        errors.value[fieldName].push(result)
        return false
      }
    }

    return true
  }

  /**
   * Valide une étape complète
   * @param {number} step - Numéro de l'étape
   * @param {Object} formData - Données du formulaire
   * @returns {boolean} - true si l'étape est valide
   */
  const validateStep = (step, formData) => {
    const stepSchema = schema[`step${step}`]
    if (!stepSchema) return true

    let isValid = true
    errors.value = {}

    Object.keys(stepSchema).forEach((fieldName) => {
      const fieldValid = validateField(fieldName, formData[fieldName], step)
      if (!fieldValid) {
        isValid = false
      }
    })

    return isValid
  }

  /**
   * Valide tout le formulaire
   * @param {Object} formData - Données du formulaire
   * @returns {boolean} - true si le formulaire est valide
   */
  const validateAll = (formData) => {
    errors.value = {}
    let isValid = true

    // Si multi-steps
    if (Object.keys(schema).some((key) => key.startsWith('step'))) {
      const stepKeys = Object.keys(schema).filter((key) => key.startsWith('step'))
      stepKeys.forEach((stepKey) => {
        const stepNumber = parseInt(stepKey.replace('step', ''))
        const stepValid = validateStep(stepNumber, formData)
        if (!stepValid) {
          isValid = false
        }
      })
    }
    // Sinon formulaire simple
    else {
      console.log('Validating simple form')
      Object.keys(schema).forEach((fieldName) => {
        const fieldValid = validateField(fieldName, formData[fieldName])
        console.log(`Field ${fieldName} valid: ${fieldValid}`)
        if (!fieldValid) {
          isValid = false
        }
      })
    }

    return isValid
  }

  /**
   * Réinitialise les erreurs
   */
  const clearErrors = () => {
    errors.value = {}
  }

  /**
   * Obtient les erreurs pour un champ
   * @param {string} fieldName - Nom du champ
   * @returns {Array} - Liste des erreurs
   */
  const getFieldErrors = (fieldName) => {
    return errors.value[fieldName] || []
  }

  /**
   * Vérifie si un champ a des erreurs
   * @param {string} fieldName - Nom du champ
   * @returns {boolean}
   */
  const hasFieldError = (fieldName) => {
    return errors.value[fieldName] && errors.value[fieldName].length > 0
  }

  /**
   * Compte le nombre total de steps dans le schéma
   * @returns {number}
   */
  const totalSteps = computed(() => {
    return Object.keys(schema).filter((key) => key.startsWith('step')).length
  })

  /**
   * Vérifie si un step est valide
   * @param {number} step
   * @param {Object} formData
   * @returns {boolean}
   */
  const isStepValid = (step, formData) => {
    return validateStep(step, formData)
  }

  /**
   * Vérifie si un champ est requis dans le schéma de validation
   * @param {string} fieldName - Nom du champ
   * @param {number|null} step - Numéro de l'étape (null pour formulaires simples)
   * @returns {boolean} - true si le champ est requis
   */
  const isFieldRequired = (fieldName, step = null) => {
    let fieldSchema

    if (step !== null && schema[`step${step}`]) {
      // Formulaire multi-steps
      fieldSchema = schema[`step${step}`]?.[fieldName]
    } else {
      // Formulaire simple
      fieldSchema = schema[fieldName]
    }

    if (!fieldSchema) return false

    // Si le schéma est un tableau
    if (Array.isArray(fieldSchema)) {
      return fieldSchema.some((rule) => {
        if (typeof rule === 'string' && rule === 'required') return true
        if (typeof rule === 'object' && rule.name === 'required') return true
        return false
      })
    }

    // Si le schéma est un objet
    if (typeof fieldSchema === 'object') {
      return fieldSchema.required === true || typeof fieldSchema.required === 'string'
    }

    return false
  }

  return {
    getFieldRules,
    validateField,
    validateStep,
    validateAll,
    clearErrors,
    getFieldErrors,
    hasFieldError,
    errors,
    currentStep,
    totalSteps,
    isStepValid,
    isFieldRequired,
  }
}

/**
 * Hook pour créer un formulaire avec validation
 * @param {Object} initialData - Données initiales du formulaire
 * @param {Object} validationSchema - Schéma de validation
 * @returns {Object} État du formulaire et fonctions
 */
export function useForm(initialData = {}, validationSchema = {}) {
  const formData = ref(initialData)
  const errorMessage = ref('')
  const successMessage = ref('')
  const loading = ref(false)

  const validation = useFormValidation(validationSchema)

  const resetForm = () => {
    formData.value = { ...initialData }
    errorMessage.value = ''
    successMessage.value = ''
    validation.clearErrors()
  }

  const setError = (message) => {
    errorMessage.value = message
    successMessage.value = ''
  }

  const setSuccess = (message) => {
    successMessage.value = message
    errorMessage.value = ''
  }

  const clearMessages = () => {
    errorMessage.value = ''
    successMessage.value = ''
  }

  return {
    formData,
    errorMessage,
    successMessage,
    loading,
    validation,
    resetForm,
    setError,
    setSuccess,
    clearMessages,
  }
}
