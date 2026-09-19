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
      <v-col cols="12">
        <FormField
          v-model="formData.nomLieu"
          field-name="nomLieu"
          label="Nom du lieu"
          placeholder="Saisir le nom du lieu"
        />
      </v-col>

      <v-col cols="12">
        <FormSelect
          v-model="typeLieuSelection"
          field-name="typeLieu"
          label="Type de lieu"
          :items="TYPE_LIEU_OPTIONS"
          @update:model-value="onTypeLieuChange"
        />
      </v-col>

      <v-col v-if="typeLieuSelection === 'Autre'" cols="12">
        <FormField
          v-model="formData.typeLieu"
          field-name="typeLieuAutre"
          label="Préciser le type de lieu"
          placeholder="Saisir le type de lieu"
        />
      </v-col>

      <v-col v-if="showLienPlan" cols="12">
        <FormField
          v-model="formData.lienPlan"
          field-name="lienPlan"
          label="Lien vers le plan (optionnel)"
          placeholder="https://..."
        />
      </v-col>

      <v-col v-if="showParentSelection" cols="12">
        <!-- Mode TreeView -->
        <template v-if="useTreeView">
          <v-divider class="my-4"></v-divider>
          <v-card-subtitle class="text-h6 font-weight-bold px-0 pb-2">
            Lieu parent (optionnel)
          </v-card-subtitle>

          <v-card variant="outlined" class="pa-4">
            <p v-if="!locations || locations.length === 0" class="text-caption text-center">
              Aucun lieu disponible
            </p>
            <VTreeview
              v-else
              v-model:opened="openNodes"
              :items="locations"
              item-value="id"
              item-title="nomLieu"
              activatable
              hoverable
              rounded
              density="compact"
            >
              <template #prepend="{ item }">
                <v-checkbox
                  :model-value="isSelected(item)"
                  density="compact"
                  hide-details
                  @update:model-value="() => onSelect(item)"
                ></v-checkbox>
              </template>
            </VTreeview>

            <v-chip
              v-if="selectedParent"
              color="primary"
              class="mt-2"
              closable
              @click:close="clearSelectedParent"
            >
              <v-icon start>mdi-map-marker</v-icon>
              Lieu parent : {{ selectedParent.nomLieu }}
            </v-chip>

            <v-alert
              v-if="!selectedParent"
              type="info"
              variant="tonal"
              density="compact"
              class="mt-2"
            >
              <v-icon start>mdi-information</v-icon>
              Aucun lieu parent sélectionné - Ce lieu sera à la racine
            </v-alert>
          </v-card>
        </template>

        <!-- Mode Select simple -->
        <template v-else>
          <FormSelect
            v-model="formData.lieuParent"
            field-name="lieuParent"
            label="Lieu parent (optionnel)"
            :items="locations"
            item-title="nomLieu"
            item-value="id"
            clearable
            @change="console.log('Lieu parent sélectionné :', formData.lieuParent)"
          />
        </template>
      </v-col>
    </v-row>
  </BaseForm>
</template>

<script setup>
  import { ref, watch } from 'vue'
  import { VTreeview } from 'vuetify/labs/components'
  import { BaseForm, FormField, FormSelect } from '@/components/common'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'

  const TYPE_LIEU_OPTIONS = [
    'Bâtiment',
    'Étage',
    'RDC',
    'Salle',
    'Atelier',
    'Couloir',
    'Extérieur',
    'Autre',
  ]

  const props = defineProps({
    title: {
      type: String,
      default: 'Ajouter un lieu',
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
    parentId: {
      type: Number,
      default: null,
    },
    locations: {
      type: Array,
      default: () => [],
    },
    useTreeView: {
      type: Boolean,
      default: true,
    },
    showLienPlan: {
      type: Boolean,
      default: true,
    },
    showParentSelection: {
      type: Boolean,
      default: true,
    },
  })

  const emit = defineEmits(['created', 'updated', 'close'])

  const formData = ref({
    nomLieu: '',
    typeLieu: '',
    lienPlan: '',
    lieuParent: props.parentId,
  })

  const typeLieuSelection = ref('')

  const onTypeLieuChange = (val) => {
    if (val !== 'Autre') {
      formData.value.typeLieu = val
    } else {
      formData.value.typeLieu = ''
    }
  }

  const validationSchema = {
    nomLieu: ['required', { name: 'minLength', params: [2] }, { name: 'maxLength', params: [50] }],
    typeLieu: ['required', { name: 'minLength', params: [2] }, { name: 'maxLength', params: [50] }],
    lienPlan: [],
  }

  const loading = ref(false)
  const errorMessage = ref('')
  const successMessage = ref('')
  const selectedParent = ref(null)
  const openNodes = ref([])

  // Récupère le chemin d'ancêtres (liste d'ids) pour pouvoir ouvrir l'arborescence
  // jusqu'au lieu cible.
  const getPathToNode = (nodes, targetId, currentPath = []) => {
    if (!nodes) return null
    for (const node of nodes) {
      if (node.id == targetId) {
        return currentPath
      }
      if (node.children && node.children.length > 0) {
        const result = getPathToNode(node.children, targetId, [...currentPath, node.id])
        if (result) return result
      }
    }
    return null
  }

  // Initialiser les données
  watch(
    () => props.initialData,
    (newData) => {
      if (newData && Object.keys(newData).length > 0) {
        formData.value = {
          nomLieu: newData.nomLieu || '',
          typeLieu: newData.typeLieu || '',
          lienPlan: newData.lienPlan || '',
          lieuParent: newData.lieuParent || props.parentId,
        }
        const type = newData.typeLieu || ''
        typeLieuSelection.value = TYPE_LIEU_OPTIONS.includes(type) ? type : type ? 'Autre' : ''
      }
    },
    { immediate: true, deep: true }
  )

  // Trouver le lieu parent dans la hiérarchie
  const findLieuById = (locations, id) => {
    for (const lieu of locations) {
      if (lieu.id === id) return lieu
      if (lieu.children) {
        const found = findLieuById(lieu.children, id)
        if (found) return found
      }
    }
    return null
  }

  // Initialiser le parent si fourni
  watch(
    () => [props.parentId, props.locations],
    ([newParentId, newLocations]) => {
      if (newParentId && newLocations && newLocations.length > 0 && props.useTreeView) {
        selectedParent.value = findLieuById(newLocations, newParentId)
        formData.value.lieuParent = newParentId
      }
    },
    { immediate: true, deep: true }
  )

  // Ouvrir automatiquement l'arborescence jusqu'au parent sélectionné.
  watch(
    [() => formData.value.lieuParent, () => props.locations, () => props.useTreeView],
    ([lieuParentId, locations, useTreeView]) => {
      if (!useTreeView || !lieuParentId || !locations || locations.length === 0) return

      const path = getPathToNode(locations, lieuParentId)
      if (path) {
        openNodes.value = Array.from(new Set([...(openNodes.value || []), ...path]))
      }
    },
    { immediate: true, deep: true }
  )

  // Gestion de la sélection dans le TreeView
  const isSelected = (item) => {
    return selectedParent.value && selectedParent.value.id === item.id
  }

  const clearSelectedParent = () => {
    selectedParent.value = null
    formData.value.lieuParent = null
  }

  const onSelect = (item) => {
    if (isSelected(item)) {
      selectedParent.value = null
      formData.value.lieuParent = null
    } else {
      selectedParent.value = item
      formData.value.lieuParent = item.id
    }
  }

  // Synchroniser formData.lieuParent avec selectedParent
  watch(
    () => selectedParent.value,
    (newParent) => {
      if (props.useTreeView) {
        formData.value.lieuParent = newParent ? newParent.id : null
      }
    }
  )

  const close = () => {
    emit('close')
  }

  const save = async () => {
    loading.value = true
    errorMessage.value = ''
    successMessage.value = ''

    const api = useApi(API_BASE_URL)

    const payload = {
      nomLieu: formData.value.nomLieu,
      typeLieu: formData.value.typeLieu,
      lienPlan: formData.value.lienPlan || null,
      lieuParent: formData.value.lieuParent,
    }

    console.log(JSON.stringify(payload, null, 2))

    try {
      if (props.isEdit) {
        // Mode édition
        const response = await api.patch(`lieux/${props.initialData.id}/`, payload)
        console.log('Lieu modifié avec succès:', response)

        successMessage.value = 'Lieu modifié avec succès'
        emit('updated', response)
      } else {
        // Mode création
        const response = await api.post('lieux/', payload)
        console.log('Lieu créé avec succès:', response)

        const newLieu = {
          id: response.id,
          nomLieu: response.nomLieu,
          typeLieu: response.typeLieu,
          lienPlan: response.lienPlan,
          lieuParent: response.lieuParent,
        }

        successMessage.value = 'Lieu créé avec succès'
        emit('created', newLieu)
      }

      setTimeout(() => {
        emit('close')
      }, 1500)
    } catch (error) {
      console.error("Erreur lors de l'enregistrement du lieu:", error)
      errorMessage.value =
        error.message || "Une erreur est survenue lors de l'enregistrement du lieu"
    } finally {
      loading.value = false
    }
  }
</script>
