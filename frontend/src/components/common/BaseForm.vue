<template>
  <FormContainer
    :title="title"
    :subtitle="subtitle"
    :cols="cols"
    :md="md"
    :lg="lg"
    :xl="xl"
    :justify="justify"
    :fluid="fluid"
    :elevation="elevation"
    :container-class="containerClass"
    :card-class="cardClass"
    :title-class="titleClass"
    :subtitle-class="subtitleClass"
    :content-class="contentClass"
    :show-actions="true"
  >
    <!-- Alerts -->
    <FormAlert
      v-if="displayErrorMessage"
      :message="displayErrorMessage"
      type="error"
      :dismissible="dismissibleAlerts"
      @close="clearError"
    />

    <!-- Erreurs de validation -->
    <FormAlert
      v-if="validationErrors.length > 0"
      type="error"
      :dismissible="dismissibleAlerts"
      @close="clearValidationErrors"
    >
      <template #default>
        <div class="text-subtitle-2 font-weight-bold mb-2">
          Veuillez corriger les erreurs suivantes :
        </div>
        <ul class="pl-4">
          <li v-for="(error, index) in validationErrors" :key="index">
            {{ error }}
          </li>
        </ul>
      </template>
    </FormAlert>

    <FormAlert v-if="loading && loadingMessage" :message="loadingMessage" type="info" />

    <FormAlert
      v-if="displaySuccessMessage"
      :message="displaySuccessMessage"
      type="success"
      :dismissible="dismissibleAlerts"
      @close="clearSuccess"
    />

    <!-- Form - Utilise v-form seulement si pas de validationSchema (formulaires simples) -->
    <v-form
      v-if="!validationSchema || Object.keys(validationSchema).length === 0"
      ref="formRef"
      v-model="formValid"
    >
      <!-- Slot pour le contenu du formulaire -->
      <slot
        :form-data="formData"
        :is-loading="loading"
        :is-valid="formValid"
        :reset-form="resetForm"
        :reset-validation="resetValidation"
        :validation="validation"
        :is-field-required="validation?.isFieldRequired"
      ></slot>

      <!-- Actions -->
      <FormActions
        v-if="showActions"
        :submit-button-text="submitButtonText"
        :submit-button-color="submitButtonColor"
        :submit-button-class="submitButtonClass"
        :submit-button-variant="submitButtonVariant"
        :submit-disabled="!formValid || loading || customDisabled"
        :show-cancel-button="showCancelButton"
        :cancel-button-text="cancelButtonText"
        :cancel-button-color="cancelButtonColor"
        :cancel-button-class="cancelButtonClass"
        :cancel-button-variant="cancelButtonVariant"
        :show-reset-button="showResetButton"
        :reset-button-text="resetButtonText"
        :reset-button-color="resetButtonColor"
        :reset-button-class="resetButtonClass"
        :reset-button-variant="resetButtonVariant"
        :loading="loading"
        :container-class="actionsContainerClass"
        :spacer="actionsSpacer"
        :custom-cancel-action="customCancelAction"
        @cancel="handleCancel"
        @reset="handleReset"
        @submit="handleSubmit"
      />
    </v-form>

    <!-- Pour les formulaires avec validationSchema (steppers), pas de v-form wrapper -->
    <div v-else>
      <!-- Slot pour le contenu du formulaire -->
      <slot
        :form-data="formData"
        :is-loading="loading"
        :is-valid="formValid"
        :reset-form="resetForm"
        :reset-validation="resetValidation"
        :validation="validation"
        :is-field-required="validation?.isFieldRequired"
      ></slot>

      <!-- Actions -->
      <FormActions
        v-if="showActions"
        :submit-button-text="submitButtonText"
        :submit-button-color="submitButtonColor"
        :submit-button-class="submitButtonClass"
        :submit-button-variant="submitButtonVariant"
        :submit-disabled="loading || customDisabled"
        :show-cancel-button="showCancelButton"
        :cancel-button-text="cancelButtonText"
        :cancel-button-color="cancelButtonColor"
        :cancel-button-class="cancelButtonClass"
        :cancel-button-variant="cancelButtonVariant"
        :show-reset-button="showResetButton"
        :reset-button-text="resetButtonText"
        :reset-button-color="resetButtonColor"
        :reset-button-class="resetButtonClass"
        :reset-button-variant="resetButtonVariant"
        :loading="loading"
        :container-class="actionsContainerClass"
        :spacer="actionsSpacer"
        :custom-cancel-action="customCancelAction"
        @cancel="handleCancel"
        @reset="handleReset"
        @submit="handleSubmit"
      />
    </div>
  </FormContainer>
</template>

<script setup>
  /**
   * BaseForm — conteneur générique pour tous les formulaires de l'application.
   *
   * Gère les alertes d'erreur/succès, l'état de chargement, la validation via `useFormValidation`,
   * et les boutons Enregistrer/Annuler. Expose la validation via le slot default avec `v-slot="{ validation }"`
   * pour que les formulaires multi-étapes puissent appeler `validation.validateStep(n, formData)`.
   *
   * Slots :
   *   default  ({ validation })  — contenu du formulaire.
   *   actions                    — surcharge totale des boutons d'action.
   *
   * Évènements émis :
   *   submit         — clic sur Enregistrer (après validation réussie).
   *   cancel         — clic sur Annuler.
   *   reset          — clic sur Réinitialiser (si affiché).
   *   clear-error    — fermeture de l'alerte d'erreur.
   *   clear-success  — fermeture de l'alerte de succès.
   */
  import { ref, computed } from 'vue'
  import { FormAlert, FormActions, FormContainer } from '.'
  import { useFormValidation } from '@/composables/useFormValidation'

  const props = defineProps({
    // Titre et sous-titre
    title: {
      type: String,
      required: true,
    },
    subtitle: {
      type: String,
      default: '',
    },

    // Données du formulaire
    modelValue: {
      type: Object,
      default: () => ({}),
    },

    // Messages
    loading: {
      type: Boolean,
      default: false,
    },
    errorMessage: {
      type: String,
      default: '',
    },
    successMessage: {
      type: String,
      default: '',
    },
    loadingMessage: {
      type: String,
      default: 'Chargement...',
    },
    dismissibleAlerts: {
      type: Boolean,
      default: false,
    },

    // Boutons de soumission
    submitButtonText: {
      type: String,
      default: 'Enregistrer',
    },
    submitButtonColor: {
      type: String,
      default: 'primary',
    },
    submitButtonClass: {
      type: String,
      default: '',
    },
    submitButtonVariant: {
      type: String,
      default: 'elevated',
    },

    // Boutons d'annulation
    showCancelButton: {
      type: Boolean,
      default: true,
    },
    cancelButtonText: {
      type: String,
      default: 'Annuler',
    },
    cancelButtonColor: {
      type: String,
      default: 'secondary',
    },
    cancelButtonClass: {
      type: String,
      default: 'mr-2',
    },
    cancelButtonVariant: {
      type: String,
      default: 'elevated',
    },
    customCancelAction: {
      type: Function,
      default: null,
    },

    // Bouton de réinitialisation
    showResetButton: {
      type: Boolean,
      default: false,
    },
    resetButtonText: {
      type: String,
      default: 'Réinitialiser',
    },
    resetButtonColor: {
      type: String,
      default: 'warning',
    },
    resetButtonClass: {
      type: String,
      default: 'mr-2',
    },
    resetButtonVariant: {
      type: String,
      default: 'elevated',
    },

    // Layout responsive
    cols: {
      type: [String, Number],
      default: 12,
    },
    md: {
      type: [String, Number],
      default: 12,
    },
    lg: {
      type: [String, Number],
      default: 12,
    },
    xl: {
      type: [String, Number],
      default: 12,
    },
    justify: {
      type: String,
      default: 'start',
    },
    fluid: {
      type: Boolean,
      default: false,
    },

    // Styles
    elevation: {
      type: [String, Number],
      default: 2,
    },
    containerClass: {
      type: String,
      default: '',
    },
    cardClass: {
      type: String,
      default: '',
    },
    titleClass: {
      type: String,
      default: '',
    },
    subtitleClass: {
      type: String,
      default: '',
    },
    contentClass: {
      type: String,
      default: '',
    },
    actionsContainerClass: {
      type: String,
      default: 'mt-4',
    },
    actionsSpacer: {
      type: Boolean,
      default: false,
    },

    // Validation
    validationSchema: {
      type: Object,
      default: () => ({}),
    },
    customValidation: {
      type: Function,
      default: () => true,
    },
    customDisabled: {
      type: Boolean,
      default: false,
    },

    // Handling de la soumission
    handleSubmit: {
      type: Function,
      default: null,
    },

    // Affichage des actions
    showActions: {
      type: Boolean,
      default: true,
    },
  })

  const emit = defineEmits([
    'update:modelValue',
    'submit',
    'cancel',
    'reset',
    'clear-error',
    'clear-success',
  ])

  const formRef = ref(null)
  const formValid = ref(false)
  const validationErrors = ref([])
  const internalErrorMessage = ref('')
  const internalSuccessMessage = ref('')

  const formData = computed({
    get: () => props.modelValue,
    set: (value) => emit('update:modelValue', value),
  })

  // Fusionner les messages internes et externes
  const displayErrorMessage = computed(() => {
    return internalErrorMessage.value || props.errorMessage
  })

  const displaySuccessMessage = computed(() => {
    return internalSuccessMessage.value || props.successMessage
  })

  // Initialiser la validation si un schéma est fourni
  const validation =
    props.validationSchema && Object.keys(props.validationSchema).length > 0
      ? useFormValidation(props.validationSchema)
      : null

  // Extraire les erreurs de validation pour affichage
  const extractValidationErrors = () => {
    const errors = []
    if (validation && validation.errors.value) {
      Object.entries(validation.errors.value).forEach(([field, fieldErrors]) => {
        if (Array.isArray(fieldErrors) && fieldErrors.length > 0) {
          fieldErrors.forEach((error) => {
            errors.push(`${field}: ${error}`)
          })
        }
      })
    }
    return errors
  }

  const clearValidationErrors = () => {
    validationErrors.value = []
    if (validation) {
      validation.clearErrors()
    }
  }

  const clearError = () => {
    internalErrorMessage.value = ''
    validationErrors.value = []
    emit('clear-error')
  }

  const clearSuccess = () => {
    internalSuccessMessage.value = ''
    emit('clear-success')
  }

  const setError = (message) => {
    internalErrorMessage.value = message
    internalSuccessMessage.value = ''
  }

  const setSuccess = (message) => {
    internalSuccessMessage.value = message
    internalErrorMessage.value = ''
    clearValidationErrors()
  }

  // Fournir validation et isFieldRequired aux composants enfants
  import { provide } from 'vue'
  if (validation) {
    provide('validation', validation)
    provide('isFieldRequired', validation.isFieldRequired)
  }

  const handleSubmit = async () => {
    // Réinitialiser les messages
    clearError()
    clearSuccess()
    clearValidationErrors()

    // Valider avec le schéma si disponible
    if (validation && !validation.validateAll(formData.value)) {
      validationErrors.value = extractValidationErrors()
      setError('Veuillez corriger les erreurs de saisie.')
      return
    }

    // Si une fonction personnalisée est fournie, l'utiliser
    if (props.handleSubmit && typeof props.handleSubmit === 'function') {
      try {
        await props.handleSubmit(formData.value)
      } catch (error) {
        setError(error.message || 'Une erreur est survenue lors de la soumission.')
        console.error('Erreur lors de la soumission:', error)
      }
      return
    }

    // Sinon, utiliser le comportement par défaut
    if (formRef.value) {
      formRef.value.validate()
    }

    if (formValid.value && props.customValidation()) {
      emit('submit', formData.value)
    } else {
      setError('Veuillez remplir correctement tous les champs requis.')
    }
  }

  const handleCancel = () => {
    if (props.customCancelAction && typeof props.customCancelAction === 'function') {
      props.customCancelAction()
    } else {
      emit('cancel')
    }
  }

  const handleReset = () => {
    resetForm()
    emit('reset')
  }

  const resetForm = () => {
    clearValidationErrors()
    clearError()
    clearSuccess()
    if (formRef.value) {
      formRef.value.reset()
    }
    if (validation) {
      validation.clearErrors()
    }
  }

  const resetValidation = () => {
    clearValidationErrors()
    if (formRef.value) {
      formRef.value.resetValidation()
    }
    if (validation) {
      validation.clearErrors()
    }
  }

  defineExpose({
    resetForm,
    resetValidation,
    formRef,
    formValid,
    validation,
    setError,
    setSuccess,
    clearError,
    clearSuccess,
  })
</script>

<style scoped>
  /* Style global pour les labels de champs */
  :deep(.field-label) {
    display: block;
    margin-bottom: 4px;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-color);
  }
</style>
