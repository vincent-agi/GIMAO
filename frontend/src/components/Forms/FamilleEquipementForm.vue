<template>
  <BaseForm
    v-model="formData"
    title="Ajouter une famille d'équipement"
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
          v-model="formData.nom"
          field-name="nom"
          label="Nom de la famille"
          placeholder="Saisir le nom de la famille"
        />
      </v-col>

      <v-col cols="12">
        <FormSelect
          v-model="formData.parent"
          field-name="parent"
          label="Famille parente (optionnel)"
          :items="families"
          item-title="nom"
          item-value="id"
          clearable
        />
      </v-col>
    </v-row>
  </BaseForm>
</template>

<script setup>
  import { ref } from 'vue'
  import { BaseForm, FormField, FormSelect } from '@/components/common'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'

  defineProps({
    families: {
      type: Array,
      default: () => [],
    },
  })

  const emit = defineEmits(['created', 'close'])

  const formData = ref({
    nom: '',
    parent: null,
  })

  const validationSchema = {
    nom: ['required', { name: 'minLength', params: [2] }, { name: 'maxLength', params: [100] }],
    parent: [],
  }

  const loading = ref(false)
  const errorMessage = ref('')
  const successMessage = ref('')

  const save = async () => {
    loading.value = true
    errorMessage.value = ''
    successMessage.value = ''

    const api = useApi(API_BASE_URL)

    try {
      const response = await api.post('famille-equipements/', formData.value)
      const newFamily = {
        id: response.id,
        nom: formData.value.nom,
        parent: formData.value.parent,
      }
      successMessage.value = 'Famille créée avec succès'
      emit('created', newFamily)
      setTimeout(() => {
        emit('close')
      }, 500)
    } catch (error) {
      console.error('Erreur lors de la création de la famille:', error)
      errorMessage.value =
        error.message || 'Une erreur est survenue lors de la création de la famille'
    } finally {
      loading.value = false
    }
  }

  const close = () => {
    emit('close')
  }
</script>
