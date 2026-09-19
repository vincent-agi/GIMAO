<template>
  <BaseForm
    v-model="formData"
    :title="title"
    :validation-schema="validationSchema"
    :loading="loading"
    :error-message="errorMessage"
    :success-message="successMessage"
    :handle-submit="save"
    :custom-cancel-action="close"
    :submit-button-text="submitButtonText"
    elevation="0"
  >
    <v-row dense>
      <!-- Nom -->
      <v-col cols="12">
        <FormField
          v-model="formData.nom"
          field-name="nom"
          label="Nom du modèle"
          placeholder="Ex: S7-1200, TeSys D, iC60N..."
        />
      </v-col>

      <!-- Fabricant -->
      <v-col cols="12">
        <FormSelect
          v-model="formData.fabricant"
          field-name="fabricant"
          label="Fabricant"
          :items="fabricants"
          item-title="nom"
          item-value="id"
          return-object
          clearable
        >
          <template #append-item>
            <v-divider />
            <v-list-item class="text-primary" @click="showFabricantModal = true">
              <v-list-item-title>
                <v-icon left size="18">mdi-plus</v-icon>
                Ajouter un fabricant
              </v-list-item-title>
            </v-list-item>
          </template>
        </FormSelect>
      </v-col>
    </v-row>
  </BaseForm>

  <!-- Modale fabricant -->
  <v-dialog v-model="showFabricantModal" max-width="600" scrollable>
    <v-card>
      <v-card-text class="pa-6">
        <FabricantForm @created="onFabricantCreated" @close="showFabricantModal = false" />
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
  import { ref, watch } from 'vue'
  import { BaseForm, FormField, FormSelect } from '@/components/common'
  import FabricantForm from '@/components/Forms/FabricantForm.vue'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'

  const props = defineProps({
    title: {
      type: String,
      default: "Ajouter un modèle d'\u00e9quipement",
    },
    submitButtonText: {
      type: String,
      default: 'Créer',
    },
    isEdit: {
      type: Boolean,
      default: false,
    },
    initialData: {
      type: Object,
      default: () => ({}),
    },
    fabricants: {
      type: Array,
      required: true,
    },
    connectedUserId: {
      type: Number,
      default: null,
    },
  })

  const emit = defineEmits(['created', 'updated', 'close', 'fabricant-created'])

  const formData = ref({
    nom: '',
    fabricant: null,
  })

  const originalData = ref(null)

  const validationSchema = {
    nom: ['required', { name: 'minLength', params: [2] }],
    fabricant: ['required'],
  }

  const loading = ref(false)
  const errorMessage = ref('')
  const successMessage = ref('')
  const showFabricantModal = ref(false)

  // Initialiser les données
  watch(
    () => props.initialData,
    (newData) => {
      if (newData && Object.keys(newData).length > 0) {
        formData.value = {
          nom: newData.nom || '',
          fabricant: newData.fabricant || null,
        }
        if (props.isEdit) {
          originalData.value = JSON.parse(JSON.stringify(formData.value))
        }
      }
    },
    { immediate: true, deep: true }
  )

  const close = () => {
    emit('close')
  }

  const detectChanges = () => {
    if (!props.isEdit || !originalData.value) return null

    const changes = {}

    // Vérifier le nom
    if (formData.value.nom !== originalData.value.nom) {
      changes.nom = {
        ancienne: originalData.value.nom,
        nouvelle: formData.value.nom,
      }
    }

    // Vérifier le fabricant
    const currentFabricantId = formData.value.fabricant?.id || formData.value.fabricant
    const originalFabricantId = originalData.value.fabricant?.id || originalData.value.fabricant

    if (currentFabricantId !== originalFabricantId) {
      changes.fabricant = {
        ancienne: originalFabricantId,
        nouvelle: currentFabricantId,
      }
    }

    return changes
  }

  const save = async () => {
    loading.value = true
    errorMessage.value = ''
    successMessage.value = ''

    const api = useApi(API_BASE_URL)

    try {
      if (props.isEdit) {
        // Mode édition
        const changes = detectChanges()

        if (!changes || Object.keys(changes).length === 0) {
          errorMessage.value = 'Aucun changement détecté'
          loading.value = false
          return
        }

        if (props.connectedUserId) {
          changes.user = props.connectedUserId
        }

        const response = await api.put(`modele-equipements/${props.initialData.id}/`, changes)
        console.log('Modèle modifié avec succès:', response)

        successMessage.value = "Modèle d'\u00e9quipement modifié avec succès"
        emit('updated', response)
      } else {
        // Mode création
        const payload = {
          nom: formData.value.nom,
          fabricant: formData.value.fabricant?.id || formData.value.fabricant,
        }

        console.log('payload : ', payload)

        const response = await api.post('modele-equipements/', payload)
        const modeleCreated = {
          id: response.id,
          nom: formData.value.nom,
          fabricant: formData.value.fabricant?.id || formData.value.fabricant,
        }
        console.log('Modele transmis : ', modeleCreated)
        successMessage.value = 'Modèle créé avec succès'
        emit('created', modeleCreated)
      }

      setTimeout(() => {
        emit('close')
      }, 1500)
    } catch (error) {
      console.error(error)
      errorMessage.value =
        error.message || "Une erreur est survenue lors de l'enregistrement du modèle"
    } finally {
      loading.value = false
    }
  }

  const onFabricantCreated = (newFab) => {
    emit('fabricant-created', newFab)
    formData.value.fabricant = newFab
  }
</script>
