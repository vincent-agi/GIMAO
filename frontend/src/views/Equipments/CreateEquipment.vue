<template>
  <v-app>
    <v-main>
      <v-container>
        <BaseForm
          v-model="formData"
          title="Créer un Équipement"
          :loading="loading"
          :error-message="errorMessage"
          :success-message="successMessage"
          :loading-message="loadingData ? 'Chargement des données...' : ''"
          :validation-schema="validationSchema"
          submit-button-text="Créer un Équipement"
          :handle-submit="handleSubmit"
          actions-container-class="d-flex justify-end gap-2 mt-3"
          submit-button-class="mt-3"
          cancel-button-class="mt-3 mr-3"
          :show-actions="showFormActions"
        >
          <template #default="{ validation }">
            <v-stepper
              v-model="step"
              :steps="EQUIPMENT_CREATE_STEPS.length"
              justify="center"
              alt-labels
            >
              <v-stepper-header class="justify-center">
                <v-stepper-item
                  v-for="(label, index) in EQUIPMENT_CREATE_STEPS"
                  :key="index"
                  :value="index + 1"
                  :complete="isStepComplete(index + 1)"
                  :editable="isStepEditable(index + 1)"
                  :color="isStepEditable(index + 1) ? 'primary' : undefined"
                  @click="goToStep(index + 1)"
                >
                  <template #title>
                    <span class="step-label">{{ label }}</span>
                  </template>
                </v-stepper-item>
              </v-stepper-header>

              <v-stepper-window v-model="step" :steps="EQUIPMENT_CREATE_STEPS.length" class="mb-8">
                <!-- Étape 1: Informations générales  & Statut -->
                <v-stepper-window-item :value="1">
                  <EquipmentFormFields
                    v-model="formData"
                    v-bind="sharedEquipmentFieldProps"
                    :step="1"
                    :show-location="false"
                    :show-status="true"
                    :show-consommables="false"
                    :show-counters="false"
                    :show-general="true"
                    :show-model-info="false"
                    v-on="equipmentFieldEvents"
                  />
                </v-stepper-window-item>

                <!-- Étape 2: Fournisseur et Fabricant -->
                <v-stepper-window-item :value="2">
                  <EquipmentFormFields
                    v-model="formData"
                    v-bind="sharedEquipmentFieldProps"
                    :step="2"
                    :show-location="false"
                    :show-status="false"
                    :show-consommables="false"
                    :show-counters="false"
                    :show-general="false"
                    :show-model-info="true"
                    v-on="equipmentFieldEvents"
                  />
                </v-stepper-window-item>

                <!-- Étape 3: Localisation -->
                <v-stepper-window-item :value="3">
                  <EquipmentFormFields
                    v-model="formData"
                    v-bind="sharedEquipmentFieldProps"
                    :step="3"
                    :show-status="false"
                    :show-consommables="false"
                    :show-counters="false"
                    :show-general="false"
                    :show-model-info="false"
                    v-on="equipmentFieldEvents"
                  />
                </v-stepper-window-item>

                <!-- Navigation -->
                <v-row justify="space-between" class="mt-6 mb-2 px-4">
                  <v-btn type="button" variant="text" :disabled="step === 1" @click="prevStep">
                    Précédent
                  </v-btn>

                  <v-btn
                    v-if="step < EQUIPMENT_CREATE_STEPS.length"
                    type="button"
                    variant="text"
                    color="primary"
                    :disabled="!canGoToNextStep(validation)"
                    @click="nextStep"
                  >
                    Suivant
                  </v-btn>
                </v-row>
              </v-stepper-window>
            </v-stepper>
          </template>
        </BaseForm>
      </v-container>
    </v-main>

    <v-dialog v-model="showFabricantDialog" max-width="600" scrollable>
      <v-card>
        <v-card-text class="pa-6">
          <FabricantForm @created="handleFabricantCreated" @close="showFabricantDialog = false" />
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showFournisseurDialog" max-width="600" scrollable>
      <v-card>
        <v-card-text class="pa-6">
          <FournisseurForm
            @created="handleFournisseurCreated"
            @close="showFournisseurDialog = false"
          />
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showModeleDialog" max-width="600" scrollable>
      <v-card>
        <v-card-text class="pa-6">
          <ModeleEquipementForm
            :fabricants="fabricants"
            @created="handleModeleCreated"
            @close="showModeleDialog = false"
            @fabricant-created="handleFabricantCreated"
          />
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showFamilleDialog" max-width="500" scrollable>
      <v-card>
        <v-card-text class="pa-6">
          <FamilleEquipementForm
            :families="familles"
            @created="handleFamilleCreated"
            @close="showFamilleDialog = false"
          />
        </v-card-text>
      </v-card>
    </v-dialog>

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

    <v-dialog v-model="showConsommableDialog" max-width="600" scrollable>
      <v-card>
        <v-card-text class="pa-6">
          <ConsommableForm
            :magasins="magasins"
            @created="handleConsommableCreated"
            @close="showConsommableDialog = false"
            @magasin-created="handleMagasinCreated"
          />
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<script setup>
  import { ref, onMounted, computed } from 'vue'
  import { BaseForm } from '@/components/common'
  import { EQUIPMENT_CREATE_STEPS } from '@/utils/constants'
  import { useEquipmentForm } from '@/composables/useEquipmentForm'
  import EquipmentFormFields from '@/components/Forms/EquipmentFormFields.vue'
  import FabricantForm from '@/components/Forms/FabricantForm.vue'
  import FournisseurForm from '@/components/Forms/FournisseurForm.vue'
  import ModeleEquipementForm from '@/components/Forms/ModeleEquipementForm.vue'
  import FamilleEquipementForm from '@/components/Forms/FamilleEquipementForm.vue'
  import LieuForm from '@/components/Forms/LieuForm.vue'
  import ConsommableForm from '@/components/Forms/ConsommableForm.vue'

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
    handleFileUpload,
    fetchData,
    handleFabricantCreated,
    handleFournisseurCreated,
    handleModeleCreated,
    handleFamilleCreated,
    handleLocationCreated,
    searchSectionOptions,
    api,
    router,
  } = useEquipmentForm()

  const step = ref(1)
  const visitedSteps = ref([1])
  const showLieuDialog = ref(false)
  const selectedParentLieuId = ref(null)
  const showConsommableDialog = ref(false)
  const magasins = ref([])

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
    'open-modele-dialog': () => {
      showModeleDialog.value = true
    },
    'open-fournisseur-dialog': () => {
      showFournisseurDialog.value = true
    },
    'open-fabricant-dialog': () => {
      showFabricantDialog.value = true
    },
    'open-famille-dialog': () => {
      showFamilleDialog.value = true
    },
    'open-lieu-dialog': (parentId) => handleOpenLieuDialog(parentId),
    'open-consommable-dialog': () => {
      showConsommableDialog.value = true
    },
  }

  const showFormActions = computed(() => step.value === EQUIPMENT_CREATE_STEPS.length)

  //Règles de validation par étape
  const validationSchema = {
    step1: {
      numSerie: [
        { name: 'minLength', params: [1] },
        { name: 'maxLength', params: [100] },
      ],
      designation: ['required', { name: 'maxLength', params: [100] }],
      reference: ['required', { name: 'maxLength', params: [100] }],
      dateMiseEnService: ['required'],
      prixAchat: ['numeric', 'positive'],
      statut: ['required'],
    },
    step2: {
      fournisseur: ['required'],
      fabricant: ['required'],
      famille: ['required'],
    },
    step3: {
      lieu: ['required'],
    },
    step4: {
      // compteurs: ['required', { name: 'minItems', params: [1] }],
    },
    step5: {},
    step6: {},
  }

  const handleSubmit = async () => {
    // Validation basique : au moins un compteur requis
    // if (formData.value.compteurs.length === 0) {
    //   errorMessage.value = 'Au moins un compteur est requis';
    //   step.value = 6;  // Rediriger vers l'étape des compteurs
    //   return;
    // }

    // Validation des compteurs
    const invalidCounters = (formData.value.compteurs || []).filter(
      (c) => !c?.isDefaultCalendar && (!c.nomCompteur || !c.unite)
    )

    if (invalidCounters.length > 0) {
      errorMessage.value = 'Tous les compteurs doivent avoir un nom et une unité'
      step.value = 4
      return
    }

    // Validation que le statut est défini
    if (!formData.value.statut) {
      errorMessage.value = "Le statut de l'équipement est requis"
      step.value = 1
      return
    }

    loading.value = true
    errorMessage.value = ''

    try {
      const fd = new FormData()

      // Ajouter les champs simples
      for (const key in formData.value) {
        if (key === 'lieu') {
          fd.append('lieu', formData.value.lieu?.id ?? '')
        } else if (key === 'consommables') {
          fd.append(key, JSON.stringify(formData.value[key]))
        } else if (key === 'compteurs') {
          // Envoyer uniquement les données de base du compteur
          const compteursData = formData.value.compteurs.map((c) => ({
            id: c.id,
            nom: c.nomCompteur,
            valeurCourante: c.valeurCourante ?? 0,
            unite: c.unite,
            estPrincipal: c.estPrincipal,
            type: c.type,
          }))
          fd.append(key, JSON.stringify(compteursData))
        } else if (key === 'plansMaintenance') {
          // Envoyer les plans de maintenance séparément
          const plansData = formData.value.plansMaintenance.map((p, planIndex) => {
            const docsAvecFichier = (p.documents || []).filter((d) => d?.file instanceof File)

            docsAvecFichier.forEach((doc, docIndex) => {
              fd.append(`pm_${planIndex}_document_${docIndex}`, doc.file)
            })

            return {
              id: p.id,
              nom: p.nom,
              type_id: p.type_id,
              description: p.description,
              compteurIndex: p.compteurIndex,
              consommables: p.consommables,
              necessiteHabilitationElectrique: p.necessiteHabilitationElectrique,
              necessitePermisFeu: p.necessitePermisFeu,
              documents: docsAvecFichier.map((doc) => ({
                titre: doc.nom || doc.nomDocument || doc.titre || '',
                type: doc.type_id ?? doc.typeDocument_id ?? doc.type ?? null,
              })),
              seuil: {
                estGlissant: p.seuil.estGlissant,
                derniereIntervention: p.seuil.derniereIntervention ?? 0,
                ecartInterventions: p.seuil.ecartInterventions ?? 0,
                prochaineMaintenance: p.seuil.prochaineMaintenance ?? 0,
              },
            }
          })
          fd.append(key, JSON.stringify(plansData))
        } else if (key === 'lienImageEquipement') {
          if (formData.value[key] instanceof File) {
            fd.append('lienImageEquipement', formData.value[key])
          }
        } else if (formData.value[key] !== null && formData.value[key] !== undefined) {
          fd.append(key, formData.value[key])
        }
      }

      await api.post('equipements/', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      successMessage.value = 'Équipement créé avec succès'

      setTimeout(() => router.back(), 1500)
    } catch (e) {
      console.error('Erreur lors de la création:', e)
      const detail = e?.response?.data ? JSON.stringify(e.response.data) : e?.message || ''
      errorMessage.value = `Erreur : ${detail || 'Veuillez vérifier les informations saisies.'}`
    } finally {
      loading.value = false
    }
  }

  const nextStep = () => {
    if (step.value < EQUIPMENT_CREATE_STEPS.length) {
      step.value++
      if (!visitedSteps.value.includes(step.value)) {
        visitedSteps.value.push(step.value)
      }
    }
  }

  const prevStep = () => {
    if (step.value > 1) step.value--
  }

  const goToStep = (targetStep) => {
    if (isStepEditable(targetStep)) {
      step.value = targetStep
    }
  }

  const isStepComplete = (stepNumber) => {
    return visitedSteps.value.includes(stepNumber) && step.value > stepNumber
  }

  const isStepEditable = (stepNumber) => {
    return visitedSteps.value.includes(stepNumber)
  }

  const canGoToNextStep = (validation) => {
    if (!validation) return true
    return validation.isStepValid(step.value, formData.value)
  }

  const handleOpenLieuDialog = (parentId) => {
    selectedParentLieuId.value = parentId
    showLieuDialog.value = true
  }

  const handleLieuCreated = async (newLieu) => {
    console.log('Nouveau lieu créé:', newLieu)
    // Rafraîchir la liste des lieux
    await fetchData()
    // Fermer la dialog
    showLieuDialog.value = false
  }

  const handleConsommableCreated = async (newConsommable) => {
    console.log('Nouveau consommable créé:', newConsommable)
    // Rafraîchir la liste des consommables
    await fetchData()
    // Ajouter le consommable à la sélection
    if (!formData.value.consommables.includes(newConsommable.id)) {
      formData.value.consommables.push(newConsommable.id)
    }
    // Fermer la dialog
    showConsommableDialog.value = false
  }

  const handleMagasinCreated = async (newMagasin) => {
    console.log('Nouveau magasin créé:', newMagasin)
    // Rafraîchir la liste des magasins
    await fetchMagasins()
  }

  const fetchMagasins = async () => {
    try {
      const data = await api.get('magasins/')
      magasins.value = data
    } catch (error) {
      console.error('Erreur lors du chargement des magasins:', error)
    }
  }

  onMounted(async () => {
    await fetchData()
    await fetchMagasins()
  })
</script>

<style scoped>
  .step-label {
    font-size: 0.875rem;
    font-weight: 500;
  }

  :deep(.v-stepper-item--editable) {
    cursor: pointer;
  }

  :deep(.v-stepper-item--editable .v-stepper-item__avatar) {
    background-color: rgb(var(--v-theme-primary)) !important;
    color: white !important;
  }

  :deep(.v-stepper-item--complete .v-stepper-item__avatar) {
    background-color: rgb(var(--v-theme-primary)) !important;
  }

  :deep(.v-stepper-item--editable .step-label) {
    color: rgb(var(--v-theme-primary));
    font-weight: 600;
  }
</style>
