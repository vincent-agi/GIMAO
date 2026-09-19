<template>
  <BaseForm
    v-model="formData"
    :title="title"
    :validation-schema="validationSchema"
    :handle-submit="save"
    :error-message="errorMessage"
    :success-message="successMessage"
    :loading="loading"
    :submit-button-text="submitButtonText"
    :custom-cancel-action="true"
    elevation="0"
    @cancel="close"
  >
    <template #default>
      <!-- Infos fabricant -->
      <v-card-subtitle class="text-h6 font-weight-bold px-0 pb-2">
        Informations du fabricant
      </v-card-subtitle>

      <v-row dense>
        <v-col cols="12" md="6">
          <FormField
            v-model="formData.nom"
            field-name="nom"
            label="Nom du fabricant"
            placeholder="Ex: Siemens, Schneider Electric..."
          />
        </v-col>

        <v-col cols="12" md="6">
          <FormField
            v-model="formData.email"
            field-name="email"
            label="Email"
            type="email"
            placeholder="contact@fabricant.com"
          />
        </v-col>

        <v-col cols="12" md="6">
          <FormField
            v-model="formData.numTelephone"
            field-name="numTelephone"
            label="Téléphone"
            placeholder="01 23 45 67 89"
          />
        </v-col>

        <v-col cols="12" md="6">
          <FormCheckbox
            v-model="formData.serviceApresVente"
            field-name="serviceApresVente"
            label="Service après-vente"
          />
        </v-col>
      </v-row>

      <v-divider class="my-6"></v-divider>

      <!-- Adresse -->
      <v-card-subtitle class="text-h6 font-weight-bold px-0 pb-2"> Adresse </v-card-subtitle>

      <v-row dense>
        <v-col cols="12" md="4">
          <FormField
            v-model="formData.adresse.numero"
            field-name="adresse.numero"
            label="N°"
            placeholder="12"
          />
        </v-col>

        <v-col cols="12" md="8">
          <FormField
            v-model="formData.adresse.rue"
            field-name="adresse.rue"
            label="Rue"
            placeholder="Avenue des Champs-Élysées"
          />
        </v-col>

        <v-col cols="12" md="6">
          <FormField
            v-model="formData.adresse.ville"
            field-name="adresse.ville"
            label="Ville"
            placeholder="Lyon"
          />
        </v-col>

        <v-col cols="12" md="6">
          <FormField
            v-model="formData.adresse.code_postal"
            field-name="adresse.code_postal"
            label="Code postal"
            placeholder="69000"
          />
        </v-col>

        <v-col cols="12" md="6">
          <FormField
            v-model="formData.adresse.pays"
            field-name="adresse.pays"
            label="Pays"
            placeholder="France"
          />
        </v-col>

        <v-col cols="12" md="6">
          <FormField
            v-model="formData.adresse.complement"
            field-name="adresse.complement"
            label="Complément"
            placeholder="Bâtiment B, Porte 201"
          />
        </v-col>
      </v-row>
    </template>
  </BaseForm>
</template>

<script setup>
  import { ref, watch } from 'vue'
  import { BaseForm, FormField, FormCheckbox } from '@/components/common'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'

  const props = defineProps({
    title: {
      type: String,
      default: 'Ajouter un fabricant',
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
    connectedUserId: {
      type: Number,
      default: null,
    },
  })

  const emit = defineEmits(['close', 'created', 'updated'])

  const formData = ref({
    nom: '',
    email: '',
    numTelephone: '',
    serviceApresVente: false,
    adresse: {
      numero: '',
      rue: '',
      ville: '',
      code_postal: '',
      pays: '',
      complement: '',
    },
  })

  const originalData = ref(null)

  const validationSchema = {
    nom: ['required', { name: 'minLength', params: [2] }],
    email: ['email'],
    numTelephone: ['phone'],
    'adresse.numero': [{ name: 'minLength', params: [1] }],
    'adresse.rue': [{ name: 'minLength', params: [2] }],
    'adresse.ville': [{ name: 'minLength', params: [2] }],
    'adresse.code_postal': [
      { name: 'pattern', params: [/^[0-9]{4,6}$/], message: 'Code postal invalide (4-6 chiffres)' },
    ],
    'adresse.pays': [{ name: 'minLength', params: [2] }],
  }

  const loading = ref(false)
  const errorMessage = ref('')
  const successMessage = ref('')

  // Initialiser les données
  watch(
    () => props.initialData,
    (newData) => {
      if (newData && Object.keys(newData).length > 0) {
        formData.value = {
          nom: newData.nom || '',
          email: newData.email || '',
          numTelephone: newData.numTelephone || '',
          serviceApresVente: newData.serviceApresVente || false,
          adresse: {
            numero: newData.adresse?.numero || '',
            rue: newData.adresse?.rue || '',
            ville: newData.adresse?.ville || '',
            code_postal: newData.adresse?.code_postal || '',
            pays: newData.adresse?.pays || '',
            complement: newData.adresse?.complement || '',
          },
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
    changes.adresse = {}

    // Champs simples
    const simpleFields = ['nom', 'email', 'numTelephone', 'serviceApresVente']
    simpleFields.forEach((field) => {
      if (formData.value[field] !== originalData.value[field]) {
        changes[field] = {
          ancienne: originalData.value[field],
          nouvelle: formData.value[field],
        }
      }
    })

    // Adresse
    const addressFields = ['numero', 'rue', 'ville', 'code_postal', 'pays', 'complement']
    addressFields.forEach((field) => {
      if (formData.value.adresse[field] !== originalData.value.adresse[field]) {
        changes.adresse[field] = {
          ancienne: originalData.value.adresse[field],
          nouvelle: formData.value.adresse[field],
        }
      }
    })

    // Supprimer adresse si vide
    if (Object.keys(changes.adresse).length === 0) {
      delete changes.adresse
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

        const response = await api.put(`fabricants/${props.initialData.id}/`, changes)
        console.log('Fabricant modifié avec succès:', response)

        successMessage.value = 'Fabricant modifié avec succès'
        emit('updated', response)
      } else {
        // Mode création
        const response = await api.post('fabricants/', formData.value)

        const newFabricant = {
          id: response.id,
          nom: response.nom,
        }

        successMessage.value = 'Fabricant créé avec succès'
        emit('created', newFabricant)
      }

      setTimeout(() => {
        emit('close')
      }, 1500)
    } catch (error) {
      console.error("Erreur lors de l'enregistrement du fabricant:", error)
      errorMessage.value = "Erreur lors de l'enregistrement du fabricant"
    } finally {
      loading.value = false
    }
  }
</script>
