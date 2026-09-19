<template>
  <BaseForm
    v-model="formData"
    :title="isEditMode ? 'Modifier le magasin' : 'Ajouter un magasin'"
    :validation-schema="validationSchema"
    :loading="loading"
    :error-message="errorMessage"
    :success-message="successMessage"
    :handle-submit="save"
    :custom-cancel-action="close"
    elevation="0"
  >
    <v-row dense>
      <!-- Nom : sélection depuis les lieux ou saisie libre -->
      <v-col cols="12">
        <v-select
          v-model="nomSelection"
          :items="lieuOptions"
          item-title="label"
          item-value="value"
          label="Nom du magasin"
          placeholder="Choisir un lieu ou saisir un nom"
          variant="outlined"
          density="comfortable"
          :loading="lieuxLoading"
        />
      </v-col>

      <!-- Champ libre si "Autre" est sélectionné -->
      <v-col v-if="nomSelection === '__autre__'" cols="12">
        <FormField
          v-model="formData.nom"
          field-name="nom"
          label="Nom personnalisé"
          placeholder="Saisir le nom du magasin"
        />
      </v-col>

      <v-col cols="12">
        <FormCheckbox v-model="formData.estMobile" field-name="estMobile" label="Magasin mobile" />
      </v-col>

      <v-divider class="my-4"></v-divider>

      <v-col cols="12">
        <v-card-subtitle class="text-h6 font-weight-bold px-0 pb-2">
          Adresse (optionnelle)
        </v-card-subtitle>
      </v-col>

      <v-col cols="4">
        <FormField
          v-model="formData.adresse.numero"
          field-name="adresse.numero"
          label="N°"
          placeholder="123"
        />
      </v-col>
      <v-col cols="8">
        <FormField
          v-model="formData.adresse.rue"
          field-name="adresse.rue"
          label="Rue"
          placeholder="Rue de la République"
        />
      </v-col>

      <v-col cols="6">
        <FormField
          v-model="formData.adresse.ville"
          field-name="adresse.ville"
          label="Ville"
          placeholder="Paris"
        />
      </v-col>
      <v-col cols="6">
        <FormField
          v-model="formData.adresse.code_postal"
          field-name="adresse.code_postal"
          label="Code postal"
          placeholder="75000"
        />
      </v-col>

      <v-col cols="12">
        <FormField
          v-model="formData.adresse.pays"
          field-name="adresse.pays"
          label="Pays"
          placeholder="France"
        />
      </v-col>

      <v-col cols="12">
        <FormField
          v-model="formData.adresse.complement"
          field-name="adresse.complement"
          label="Complément"
          placeholder="Bâtiment A, Etage 3"
        />
      </v-col>
    </v-row>
  </BaseForm>
</template>

<script setup>
  import { ref, computed, watch, onMounted } from 'vue'
  import { BaseForm, FormField, FormCheckbox } from '@/components/common'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'

  const emit = defineEmits(['created', 'updated', 'close'])

  const props = defineProps({
    magasin: {
      type: Object,
      default: null,
    },
  })

  const api = useApi(API_BASE_URL)
  const isEditMode = computed(() => !!props.magasin)

  // ── Lieux ──────────────────────────────────────────────────────────────────
  const lieux = ref([])
  const lieuxLoading = ref(false)

  const lieuOptions = computed(() => [
    ...lieux.value.map((l) => ({ label: l.nomLieu, value: l.nomLieu })),
    { label: 'Autre (saisir un nom)', value: '__autre__' },
  ])

  onMounted(async () => {
    lieuxLoading.value = true
    try {
      const res = await api.get('lieux/')
      lieux.value = Array.isArray(res) ? res : res.results || []
    } catch {
      /* silencieux */
    } finally {
      lieuxLoading.value = false
    }
  })

  // ── Sélection nom ──────────────────────────────────────────────────────────
  const nomSelection = ref('')

  watch(nomSelection, (val) => {
    if (val && val !== '__autre__') {
      formData.value.nom = val
    } else if (val !== '__autre__') {
      formData.value.nom = ''
    }
  })

  // ── Formulaire ─────────────────────────────────────────────────────────────
  const formData = ref({
    nom: '',
    estMobile: false,
    adresse: {
      numero: '',
      rue: '',
      ville: '',
      code_postal: '',
      pays: '',
      complement: null,
    },
  })

  const validationSchema = {
    nom: ['required', { name: 'minLength', params: [2] }, { name: 'maxLength', params: [100] }],
    estMobile: [],
    'adresse.numero': [{ name: 'minLength', params: [1] }],
    'adresse.rue': [{ name: 'minLength', params: [2] }],
    'adresse.ville': [{ name: 'minLength', params: [2] }],
    'adresse.code_postal': [
      {
        name: 'pattern',
        params: [/^[0-9]{4,6}$/],
        message: 'Le code postal doit contenir entre 4 et 6 chiffres',
      },
    ],
    'adresse.pays': [{ name: 'minLength', params: [2] }],
  }

  const loading = ref(false)
  const errorMessage = ref('')
  const successMessage = ref('')

  const close = () => emit('close')

  // Initialiser en mode édition
  watch(
    () => props.magasin,
    (newMagasin) => {
      if (newMagasin) {
        formData.value = {
          nom: newMagasin.nom || '',
          estMobile: newMagasin.estMobile || false,
          adresse: {
            numero: newMagasin.adresse?.numero || '',
            rue: newMagasin.adresse?.rue || '',
            ville: newMagasin.adresse?.ville || '',
            code_postal: newMagasin.adresse?.code_postal || '',
            pays: newMagasin.adresse?.pays || '',
            complement: newMagasin.adresse?.complement || null,
          },
        }
        // Pré-sélectionner si le nom correspond à un lieu existant
        nomSelection.value = newMagasin.nom || '__autre__'
      }
    },
    { immediate: true, deep: true }
  )

  const save = async () => {
    loading.value = true
    errorMessage.value = ''
    successMessage.value = ''

    try {
      let response
      if (isEditMode.value) {
        response = await api.patch(`magasins/${props.magasin.id}/`, formData.value)
        successMessage.value = 'Magasin modifié avec succès'
        emit('updated', response)
      } else {
        response = await api.post('magasins/', formData.value)
        successMessage.value = 'Magasin créé avec succès'
        emit('created', { id: response.id, nom: response.nom, estMobile: response.estMobile })
      }
      setTimeout(() => emit('close'), 500)
    } catch (error) {
      errorMessage.value = error.message || 'Une erreur est survenue'
    } finally {
      loading.value = false
    }
  }
</script>
