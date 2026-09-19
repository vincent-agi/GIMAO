<template>
  <BaseForm
    v-model="formData"
    :title="isEdit ? 'Modifier le consommable' : 'Ajouter un consommable'"
    :validation-schema="validationSchema"
    :loading="loading"
    :error-message="errorMessage"
    :success-message="successMessage"
    :handle-submit="save"
    :custom-cancel-action="close"
    elevation="0"
  >
    <v-row dense>
      <v-col cols="12">
        <FormField
          v-model="formData.designation"
          field-name="designation"
          label="Désignation"
          placeholder="Saisir la désignation du consommable"
        />
      </v-col>

      <v-col cols="12">
        <FormField
          v-model="formData.seuilStockFaible"
          field-name="seuilStockFaible"
          label="Seuil de stock faible (optionnel)"
          placeholder="0"
          type="number"
        />
      </v-col>

      <v-col cols="12">
        <FormFileInput
          label="Image du consommable (optionnel)"
          placeholder="Sélectionner une image"
          accept="image/*"
          prepend-inner-icon="mdi-camera"
          @update:model-value="handleFileUpload"
        />
      </v-col>
    </v-row>
  </BaseForm>
</template>

<script setup>
  import { ref, watch, computed, onMounted } from 'vue'
  import { BaseForm, FormField, FormFileInput } from '@/components/common'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'

  const props = defineProps({
    initialData: {
      type: Object,
      default: null,
    },
  })

  const emit = defineEmits(['created', 'updated', 'close'])

  const formData = ref({
    designation: '',
    seuilStockFaible: null,
    lienImageConsommable: null,
  })

  const isEdit = computed(() => !!props.initialData)

  const validationSchema = {
    designation: [
      'required',
      { name: 'minLength', params: [2] },
      { name: 'maxLength', params: [50] },
    ],
    seuilStockFaible: ['numeric', 'positive'],
  }

  const loading = ref(false)
  const errorMessage = ref('')
  const successMessage = ref('')

  const close = () => {
    emit('close')
  }

  const handleFileUpload = (file) => {
    formData.value.lienImageConsommable = file
  }

  const initForm = () => {
    if (props.initialData) {
      formData.value = {
        designation: props.initialData.designation,
        seuilStockFaible: props.initialData.seuilStockFaible,
        lienImageConsommable: null, // On ne charge pas l'image existante dans l'input file
      }
    }
  }

  watch(
    () => props.initialData,
    () => {
      initForm()
    },
    { deep: true }
  )

  onMounted(() => {
    initForm()
  })

  const save = async () => {
    loading.value = true
    errorMessage.value = ''
    successMessage.value = ''

    const api = useApi(API_BASE_URL)

    const formDataToSend = new FormData()
    formDataToSend.append('designation', formData.value.designation)

    if (formData.value.seuilStockFaible !== null && formData.value.seuilStockFaible !== '') {
      formDataToSend.append('seuilStockFaible', formData.value.seuilStockFaible)
    }

    if (formData.value.lienImageConsommable instanceof File) {
      formDataToSend.append('lienImageConsommable', formData.value.lienImageConsommable)
    }

    try {
      let response
      if (isEdit.value) {
        response = await api.patch(`consommables/${props.initialData.id}/`, formDataToSend, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        successMessage.value = 'Consommable modifié avec succès'
        emit('updated', response)
      } else {
        // Pour déboguer FormData, il faut itérer dessus
        for (let [key, value] of formDataToSend.entries()) {
          console.log(`${key}:`, value)
        }

        // Ne PAS définir manuellement 'multipart/form-data', axios le fait automatiquement avec le bon boundary
        response = await api.post('consommables/', formDataToSend)
        successMessage.value = 'Consommable créé avec succès'
        emit('created', response)
      }

      setTimeout(() => {
        emit('close')
      }, 500)
    } catch (error) {
      console.error('Erreur lors de la sauvegarde du consommable:', error)
      errorMessage.value =
        error.message || 'Une erreur est survenue lors de la sauvegarde du consommable'
    } finally {
      loading.value = false
    }
  }
</script>
