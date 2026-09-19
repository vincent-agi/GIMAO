<template>
  <BaseForm
    v-model="formData"
    :title="title"
    :validation-schema="validationSchema"
    :loading="loading"
    :error-message="errorMessage"
    :success-message="successMessage"
    :handleSubmit="save"
    :submit-button-text="submitButtonText"
    :custom-cancel-action="true"
    @cancel="close"
    elevation="0"
  >
    <v-card-subtitle class="text-h6 font-weight-bold px-0 pb-2">
      Identification
    </v-card-subtitle>

    <v-row dense>
      <v-col cols="12" md="6">
        <FormField v-model="formData.designation" field-name="designation" label="Désignation"
          placeholder="Ex: Fourgon atelier n°3" />
      </v-col>
      <v-col cols="12" md="6">
        <FormField v-model="formData.reference" field-name="reference" label="Référence interne" />
      </v-col>
    </v-row>

    <v-row dense>
      <v-col cols="12" md="6">
        <FormField v-model="formData.vin" field-name="vin" label="VIN"
          placeholder="17 caractères, ex: VF1BB000000000001" />
      </v-col>
      <v-col cols="12" md="6">
        <FormField v-model="formData.immatriculation" field-name="immatriculation" label="Immatriculation"
          placeholder="AB-123-CD" />
      </v-col>
    </v-row>

    <v-row dense>
      <v-col cols="12" md="6">
        <FormSelect v-model="formData.genre" field-name="genre" label="Genre" :items="GENRE_OPTIONS"
          item-title="title" item-value="value" />
      </v-col>
      <v-col cols="12" md="6">
        <FormSelect v-model="formData.energie" field-name="energie" label="Énergie" :items="ENERGIE_OPTIONS"
          item-title="title" item-value="value" />
      </v-col>
    </v-row>

    <v-row dense>
      <v-col cols="12" md="4">
        <FormField v-model="formData.co2" field-name="co2" label="CO2 (g/km)" type="number" />
      </v-col>
      <v-col cols="12" md="4">
        <FormField v-model="formData.puissanceFiscale" field-name="puissanceFiscale" label="Puissance fiscale (CV)"
          type="number" />
      </v-col>
      <v-col cols="12" md="4">
        <FormField v-model="formData.ptac" field-name="ptac" label="PTAC (kg)" type="number" />
      </v-col>
    </v-row>

    <v-divider class="my-6"></v-divider>

    <v-card-subtitle class="text-h6 font-weight-bold px-0 pb-2">
      Classification et localisation
    </v-card-subtitle>

    <v-row dense>
      <v-col cols="12" md="6">
        <FormSelect v-model="formData.lieu" field-name="lieu" label="Lieu" :items="lieux" item-title="nomLieu"
          item-value="id" />
      </v-col>
      <v-col cols="12" md="6">
        <FormSelect v-model="formData.famille" field-name="famille" label="Famille" :items="familles"
          item-title="nom" item-value="id" />
      </v-col>
    </v-row>

    <v-row dense>
      <v-col cols="12" md="6">
        <FormSelect v-model="formData.fabricant" field-name="fabricant" label="Fabricant" :items="fabricants"
          item-title="nom" item-value="id" />
      </v-col>
      <v-col cols="12" md="6">
        <FormSelect v-model="formData.fournisseur" field-name="fournisseur" label="Fournisseur" :items="fournisseurs"
          item-title="nom" item-value="id" />
      </v-col>
    </v-row>

    <v-row dense>
      <v-col cols="12" md="6">
        <FormSelect v-model="formData.modeleEquipement" field-name="modeleEquipement" label="Modèle (optionnel)"
          :items="modeles" item-title="nom" item-value="id" clearable />
      </v-col>
    </v-row>
  </BaseForm>
</template>

<script setup>
/**
 * Formulaire de création/édition d'un véhicule (US-002, US-003).
 *
 * Même pattern que FournisseurForm.vue/ModeleEquipementForm.vue : un seul
 * composant pour la création et l'édition, piloté par la prop `isEdit`.
 * En édition, seuls les champs modifiés sont envoyés au format
 * `{ champ: { nouvelle: valeur } }` attendu par
 * `equipement.services.update_vehicule` (backend).
 */
import { ref, watch } from 'vue'
import { BaseForm, FormField } from '@/components/common'
import FormSelect from '@/components/Forms/inputType/FormSelect.vue'
import { useApi } from '@/composables/useApi'
import { useStore } from 'vuex'
import { API_BASE_URL } from '@/utils/constants'

const GENRE_OPTIONS = [
  { value: 'VL', title: 'Véhicule léger' },
  { value: 'PL', title: 'Poids lourd' },
  { value: 'UTILITAIRE', title: 'Utilitaire' },
  { value: 'REMORQUE', title: 'Remorque' },
]

const ENERGIE_OPTIONS = [
  { value: 'ESSENCE', title: 'Essence' },
  { value: 'DIESEL', title: 'Diesel' },
  { value: 'ELECTRIQUE', title: 'Électrique' },
  { value: 'HYBRIDE', title: 'Hybride' },
  { value: 'GPL', title: 'GPL' },
  { value: 'AUTRE', title: 'Autre' },
]

const props = defineProps({
  title: { type: String, default: 'Ajouter un véhicule' },
  submitButtonText: { type: String, default: 'Créer' },
  isEdit: { type: Boolean, default: false },
  initialData: { type: Object, default: () => ({}) },
  lieux: { type: Array, default: () => [] },
  familles: { type: Array, default: () => [] },
  fabricants: { type: Array, default: () => [] },
  fournisseurs: { type: Array, default: () => [] },
  modeles: { type: Array, default: () => [] },
})

const emit = defineEmits(['created', 'updated', 'close'])

const store = useStore()

/** @returns {number|null} L'id de l'utilisateur connecté (session store, ou repli localStorage). */
const getCurrentUserId = () => {
  const currentUser = store.getters.currentUser
  if (currentUser?.id) return currentUser.id

  const userFromStorage = localStorage.getItem('user')
  if (userFromStorage) {
    try {
      return JSON.parse(userFromStorage)?.id ?? null
    } catch {
      return null
    }
  }
  return null
}

const emptyFormData = () => ({
  designation: '',
  reference: '',
  lieu: null,
  famille: null,
  fabricant: null,
  fournisseur: null,
  modeleEquipement: null,
  vin: '',
  immatriculation: '',
  genre: null,
  energie: null,
  co2: null,
  puissanceFiscale: null,
  ptac: null,
})

const formData = ref(emptyFormData())
const originalData = ref(null)

const validationSchema = {
  designation: ['required', { name: 'minLength', params: [2] }],
  lieu: ['required'],
  famille: ['required'],
  fabricant: ['required'],
  fournisseur: ['required'],
  vin: ['required', { name: 'pattern', params: [/^[A-HJ-NPR-Z0-9]{17}$/], message: 'Le VIN doit comporter 17 caractères (hors I, O, Q)' }],
  immatriculation: ['required', { name: 'pattern', params: [/^[A-Z]{2}-\d{3}-[A-Z]{2}$/], message: 'Format attendu : AB-123-CD' }],
  genre: ['required'],
  energie: ['required'],
  co2: [{ name: 'min', params: [0] }],
  puissanceFiscale: [{ name: 'min', params: [0] }],
  ptac: [{ name: 'min', params: [0] }],
}

watch(
  () => props.initialData,
  (data) => {
    if (!data || Object.keys(data).length === 0) return

    const profile = data.vehicule_profile || {}
    formData.value = {
      designation: data.designation || '',
      reference: data.reference || '',
      lieu: data.lieu?.id ?? data.lieu ?? null,
      famille: data.famille?.id ?? data.famille ?? null,
      fabricant: data.fabricant?.id ?? data.fabricant ?? null,
      fournisseur: data.fournisseur?.id ?? data.fournisseur ?? null,
      modeleEquipement: data.modele?.id ?? data.modeleEquipement ?? null,
      vin: profile.vin || '',
      immatriculation: profile.immatriculation || '',
      genre: profile.genre || null,
      energie: profile.energie || null,
      co2: profile.co2 ?? null,
      puissanceFiscale: profile.puissanceFiscale ?? null,
      ptac: profile.ptac ?? null,
    }

    if (props.isEdit) {
      originalData.value = JSON.parse(JSON.stringify(formData.value))
    }
  },
  { immediate: true, deep: true },
)

const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const close = () => emit('close')

/** @returns {object} Diff `{ champ: { nouvelle } }` des champs modifiés depuis le chargement initial. */
const detectChanges = () => {
  if (!props.isEdit || !originalData.value) return {}

  const changes = {}
  for (const field of Object.keys(formData.value)) {
    if (formData.value[field] !== originalData.value[field]) {
      changes[field] = { nouvelle: formData.value[field] }
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
      const changes = detectChanges()

      if (Object.keys(changes).length === 0) {
        errorMessage.value = 'Aucun changement détecté'
        return
      }

      const response = await api.put(`vehicules/${props.initialData.id}/`, {
        changes: JSON.stringify(changes),
      })

      successMessage.value = 'Véhicule modifié avec succès'
      emit('updated', response)
    } else {
      const payload = {
        ...formData.value,
        createurEquipement: getCurrentUserId(),
      }

      const response = await api.post('vehicules/', payload)

      successMessage.value = 'Véhicule créé avec succès'
      emit('created', response)
    }

    setTimeout(() => emit('close'), 1000)
  } catch (error) {
    errorMessage.value = error?.response?.data?.error || "Erreur lors de l'enregistrement du véhicule"
  } finally {
    loading.value = false
  }
}
</script>
