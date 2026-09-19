<template>
  <v-app>
    <v-main>
      <v-container>
        <BaseForm
          v-model="formData"
          :title="`Modifier l'Équipement #${equipmentId}`"
          :loading="loading"
          :error-message="errorMessage"
          :success-message="successMessage"
          :loading-message="loadingData ? 'Chargement des données...' : ''"
          :custom-validation="validateForm"
          submit-button-text="Enregistrer les modifications"
          :handle-submit="handleSubmit"
        >
          <template #default>
            <EquipmentFormFields
              v-model="formData"
              v-bind="sharedEquipmentFieldProps"
              :show-counters="false"
              :lien-image-equipement="formData.lienImageEquipement"
              v-on="equipmentFieldEvents"
            />
          </template>
        </BaseForm>
      </v-container>
    </v-main>

    <v-dialog v-model="showLieuDialog" max-width="600" scrollable>
      <v-card>
        <v-card-text class="pa-6">
          <LieuForm
            :parent-id="selectedParentLieuId"
            :locations="locations"
            @created="handleLieuCreated"
            @close="showLieuDialog = false"
          />
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showFabricantDialog" max-width="80%">
      <FabricantForm @created="handleFabricantCreated" @close="showFabricantDialog = false" />
    </v-dialog>

    <v-dialog v-model="showFournisseurDialog" max-width="80%">
      <FournisseurForm @created="handleFournisseurCreated" @close="showFournisseurDialog = false" />
    </v-dialog>

    <v-dialog v-model="showModeleDialog" max-width="80%">
      <ModeleEquipementForm
        :fabricants="fabricants"
        @created="handleModeleCreated"
        @close="showModeleDialog = false"
        @fabricant-created="handleFabricantCreated"
      />
    </v-dialog>

    <v-dialog v-model="showFamilleDialog" max-width="50%">
      <FamilleEquipementForm
        :families="familles"
        @created="handleFamilleCreated"
        @close="showFamilleDialog = false"
      />
    </v-dialog>
  </v-app>
</template>

<script setup>
  import { ref, computed, onMounted } from 'vue'
  import { useRoute } from 'vue-router'
  import { BaseForm } from '@/components/common'
  import { useEquipmentForm } from '@/composables/useEquipmentForm'
  import EquipmentFormFields from '@/components/Forms/EquipmentFormFields.vue'
  import FabricantForm from '@/components/Forms/FabricantForm.vue'
  import FournisseurForm from '@/components/Forms/FournisseurForm.vue'
  import ModeleEquipementForm from '@/components/Forms/ModeleEquipementForm.vue'
  import FamilleEquipementForm from '@/components/Forms/FamilleEquipementForm.vue'
  import LieuForm from '@/components/Forms/LieuForm.vue'

  const route = useRoute()

  const {
    formData,
    loading,
    loadingData,
    errorMessage,
    successMessage,
    locations,
    equipmentModels,
    fournisseurs,
    fabricants,
    consumables,
    familles,
    equipmentStatuses,
    equipmentModelsLoading,
    fournisseursLoading,
    fabricantsLoading,
    consumablesLoading,
    showFabricantDialog,
    showFournisseurDialog,
    showModeleDialog,
    showFamilleDialog,
    validateForm,
    handleFileUpload,
    fetchData,
    fetchEquipment,
    detectChanges,
    handleFabricantCreated,
    handleFournisseurCreated,
    handleModeleCreated,
    handleFamilleCreated,
    handleLocationCreated,
    searchSectionOptions,
    api,
    router,
  } = useEquipmentForm(true)

  const equipmentId = computed(() => route.params.id || null)

  const showLieuDialog = ref(false)
  const selectedParentLieuId = ref(null)

  const sharedEquipmentFieldProps = computed(() => ({
    equipmentModels: equipmentModels.value,
    fournisseurs: fournisseurs.value,
    fabricants: fabricants.value,
    familles: familles.value,
    locations: locations.value,
    consumables: consumables.value,
    equipmentStatuses: equipmentStatuses.value,
    equipmentModelsLoading: equipmentModelsLoading.value,
    fournisseursLoading: fournisseursLoading.value,
    fabricantsLoading: fabricantsLoading.value,
    consumablesLoading: consumablesLoading.value,
  }))

  const equipmentFieldEvents = {
    'file-upload': handleFileUpload,
    'location-created': handleLocationCreated,
    'search-equipment-models': (search) => searchSectionOptions('equipmentModels', search),
    'search-fournisseurs': (search) => searchSectionOptions('fournisseurs', search),
    'search-fabricants': (search) => searchSectionOptions('fabricants', search),
    'search-consumables': (search) => searchSectionOptions('consumables', search),
    'open-lieu-dialog': (parentId) => handleOpenLieuDialog(parentId),
  }

  const handleOpenLieuDialog = (parentId) => {
    selectedParentLieuId.value = parentId
    showLieuDialog.value = true
  }

  const handleLieuCreated = async (newLieu) => {
    try {
      // Rafraîchir la liste des lieux et sélectionner le nouveau si possible
      await fetchData()
      if (newLieu?.id) {
        formData.value.lieu = newLieu.id
      }
    } finally {
      showLieuDialog.value = false
    }
  }

  const handleSubmit = async () => {
    if (!validateForm()) return

    // Détecter les changements
    const { hasChanges, changes } = detectChanges()

    if (!hasChanges) {
      errorMessage.value = 'Aucune modification détectée'
      return
    }

    loading.value = true
    errorMessage.value = ''
    try {
      const fd = new FormData()

      if (formData.value.lienImageEquipement instanceof File) {
        fd.append('lienImageEquipement', formData.value.lienImageEquipement)
        delete changes.lienImageEquipement
      }

      fd.append('changes', JSON.stringify(changes))

      await api.put(`equipements/${equipmentId.value}/`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      successMessage.value = 'Équipement modifié avec succès'
      setTimeout(() => router.back(), 1500)
    } catch (e) {
      console.error('Erreur lors de la modification:', e)
      errorMessage.value = "Erreur lors de la modification de l'équipement"

      if (e.response?.data) {
        const errors = Object.entries(e.response.data)
          .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(', ') : msgs}`)
          .join('\n')
        errorMessage.value += `\n${errors}`
      }
    } finally {
      loading.value = false
    }
  }

  onMounted(async () => {
    try {
      await fetchData()
      await fetchEquipment(equipmentId.value)
      // Pas besoin de fetchDocs car pas de compteurs en mode édition
    } catch (error) {
      console.error('Erreur dans onMounted:', error)
      errorMessage.value = error.message || 'Erreur lors du chargement'
    }
  })
</script>
