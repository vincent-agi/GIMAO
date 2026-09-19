<template>
  <BaseDetailView
    :data="defaillance"
    :loading="loading"
    :error-message="errorMessage"
    :title="'Détail de la demande d\'intervention'"
    :success-message="successMessage"
    :auto-display="false"
    :show-edit-button="false"
    @delete="handleDelete"
    @clear-error="errorMessage = ''"
    @clear-success="successMessage = ''"
  >
    <!-- Contenu personnalisé -->
    <template #default="{ data }">
      <v-row v-if="data">
        <!-- Colonne gauche: Demande d'intervention -->
        <v-col cols="12" md="6">
          <h3 class="text-h6 mb-4 text-primary">{{ data.nom }}</h3>

          <div class="detail-field">
            <label class="detail-label">Commentaire</label>
            <div class="detail-value">{{ data.commentaire }}</div>
          </div>

          <div class="detail-field">
            <label class="detail-label">Statut</label>
            <div class="detail-value">
              <v-chip :color="data.statut ? FAILURE_STATUS_COLORS[data.statut] : 'grey'" dark>
                {{ FAILURE_STATUS[data.statut] }}
              </v-chip>
            </div>
          </div>

          <div class="detail-field">
            <label class="detail-label">Statut supposé de l'équipement</label>
            <div class="detail-value">
              <v-chip
                v-if="data.statut_suppose"
                :color="data.statut_suppose ? EQUIPMENT_STATUS_COLORS[data.statut_suppose] : 'grey'"
                dark
              >
                {{ EQUIPMENT_STATUS[data.statut_suppose] }}
              </v-chip>
              <span v-else>Non spécifié</span>
            </div>
          </div>

          <div class="detail-field">
            <label class="detail-label">Créateur</label>
            <div class="detail-value">
              {{ data.utilisateur.prenom ?? '' }} {{ data.utilisateur.nomFamille ?? '' }}
            </div>
          </div>

          <div class="detail-field">
            <label class="detail-label">Date de création</label>
            <div class="detail-value">{{ formatDate(data.date_creation) }}</div>
          </div>

          <div class="detail-field">
            <label class="detail-label">Date de changement de statut</label>
            <div class="detail-value">{{ formatDate(data.date_changementStatut) }}</div>
          </div>

          <v-row>
            <v-col v-if="store.getters.hasPermission('di:transform')" cols="12">
              <v-btn
                color="primary"
                block
                :disabled="!canCreateIntervention"
                @click="openCreateInterventionModal"
              >
                <v-icon class="mx-2" left>mdi-wrench</v-icon>
                Transformer en bon de travail
              </v-btn>
            </v-col>
            <v-col v-if="store.getters.hasPermission('di:accept')" cols="6">
              <v-btn color="success" block :disabled="!canAccept" @click="openAcceptModal">
                Accepter la demande
              </v-btn>
            </v-col>
            <v-col v-if="store.getters.hasPermission('di:refuse')" cols="6">
              <v-btn color="error" block :disabled="!canClose" @click="openRejectModal">
                Refuser la demande
              </v-btn>
            </v-col>
          </v-row>
        </v-col>

        <!-- Colonne droite: Équipement et Documents -->
        <v-col cols="12" md="6">
          <!-- Section Équipement -->
          <v-card elevation="2" class="mb-4">
            <v-card-title
              class="d-flex align-center"
              @click="showEquipmentDetails = !showEquipmentDetails"
            >
              <span>Équipement</span>
              <v-spacer></v-spacer>
              <v-btn
                color="primary"
                class="mr-2"
                size="small"
                :disabled="!data.equipement"
                @click="openEquipment"
              >
                Détails
              </v-btn>
              <v-icon>
                {{ showEquipmentDetails ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
              </v-icon>
            </v-card-title>

            <v-expand-transition>
              <v-card-text v-show="showEquipmentDetails" v-if="data.equipement">
                <div
                  v-for="(value, key) in formattedEquipmentLabel"
                  :key="key"
                  class="detail-field"
                >
                  <label class="detail-label">{{ key }}</label>
                  <div v-if="key !== 'Statut'" class="detail-value">{{ value }}</div>
                  <v-chip v-else :color="getStatusColor(value)" variant="tonal">{{
                    getStatusLabel(value)
                  }}</v-chip>
                </div>
              </v-card-text>
            </v-expand-transition>
          </v-card>

          <!-- Section Documents -->
          <v-card elevation="2">
            <v-card-title
              class="d-flex align-center"
              @click="showDocumentsDetails = !showDocumentsDetails"
            >
              <span>Documents</span>
              <v-spacer></v-spacer>
              <v-btn
                v-if="canEditFailure"
                color="primary"
                class="mr-2"
                size="small"
                @click="handleAddDocument"
              >
                <v-icon left>mdi-plus</v-icon>
                Ajouter
              </v-btn>
              <v-icon>
                {{ showDocumentsDetails ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
              </v-icon>
            </v-card-title>

            <v-expand-transition>
              <v-card-text v-show="showDocumentsDetails">
                <DocumentList
                  v-if="(data.documentsDI || []).length > 0"
                  :documents="data.documentsDI || []"
                  :show-type="true"
                  :show-delete="canEditFailure"
                  @delete-success="handleDeleteSuccess"
                  @delete-error="handleDeleteError"
                  @download-error="handleDownloadError"
                  @download-success="handleDownloadSuccess"
                />
                <p v-else class="text-caption text-grey">Aucun document associé</p>
              </v-card-text>
            </v-expand-transition>
          </v-card>
        </v-col>
      </v-row>
    </template>
  </BaseDetailView>

  <!-- Modale de confirmation pour accepter la demande -->
  <ConfirmationModal
    v-model="showAcceptModal"
    type="success"
    title="Accepter la demande"
    message="Êtes-vous sûr de vouloir accepter cette demande d'intervention ? \n\nCette action changera le statut de la demande."
    confirm-text="Accepter"
    cancel-text="Annuler"
    confirm-icon="mdi-check"
    :loading="acceptLoading"
    @confirm="handleChangeStatusFailure('ACCEPTEE')"
    @cancel="showAcceptModal = false"
  />

  <!-- Modale de confirmation pour rejeter la demande -->
  <ConfirmationModal
    v-model="showRejectModal"
    type="error"
    title="Rejeter la demande"
    message="Êtes-vous sûr de vouloir rejeter cette demande d'intervention ? \n\nCette action changera le statut de la demande."
    confirm-text="Rejeter"
    cancel-text="Annuler"
    confirm-icon="mdi-check"
    :loading="rejectLoading"
    @confirm="handleChangeStatusFailure('REFUSEE')"
    @cancel="showRejectModal = false"
  />

  <!-- Modale de confirmation pour transformer la demande -->
  <v-dialog v-model="showCreateInterventionModal" max-width="500">
    <v-card>
      <v-card-title class="text-h5 bg-primary text-white pb-3">
        Transformer la demande
      </v-card-title>

      <v-card-text class="pt-4">
        <p class="mb-4">
          Êtes-vous sûr de vouloir transformer cette demande d'intervention en bon de travail ?<br /><br />Cette
          action changera le statut de la demande.
        </p>

        <FormTextarea
          v-model="transformFormData.diagnostic"
          field-name="diagnostic"
          label="Diagnostic"
          placeholder="Saisir un diagnostic"
          rows="3"
          class="mb-4"
        />

        <FormSelect
          v-model="transformFormData.statut_equipement"
          field-name="statut_equipement"
          label="Nouveau statut de l'équipement"
          :items="statutOptions"
          item-title="title"
          item-value="value"
          placeholder="Valider ou modifier le statut de l'équipement"
        />
      </v-card-text>

      <v-card-actions class="pa-4">
        <v-spacer></v-spacer>
        <v-btn color="grey" variant="text" @click="showCreateInterventionModal = false">
          Annuler
        </v-btn>
        <v-btn
          color="primary"
          :loading="createInterventionLoading"
          :disabled="!canSubmitCreateIntervention"
          @click="handleCreateIntervention()"
        >
          <v-icon left class="mr-1">mdi-check</v-icon>
          Transformer
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- Modale d'archivage -->
  <ConfirmationModal
    v-model="showArchiveDialog"
    title="Confirmer l'archivage"
    message="Êtes-vous sûr de vouloir archiver cette demande d'intervention ?
          Elle ne sera plus visible dans la liste principale."
    confirm-text="Archiver"
    @confirm="archiveFailure"
    @cancel="showArchiveDialog = false"
  />

  <!-- Boutons flottants -->
  <div class="floating-buttons">
    <v-btn
      v-if="!defaillance?.archive && store.getters.hasPermission('di:archive')"
      color="warning"
      size="large"
      icon
      elevation="4"
      class="mb-3 d-block"
      @click="showArchiveDialog = true"
    >
      <v-icon size="large">mdi-archive-arrow-down</v-icon>
      <v-tooltip activator="parent" location="left"> Archiver la demande </v-tooltip>
    </v-btn>

    <v-btn
      v-if="canEditFailure"
      color="primary"
      size="large"
      icon
      elevation="4"
      class="d-block"
      @click="editCurrentFailure()"
    >
      <v-icon size="large">mdi-pencil</v-icon>
      <v-tooltip activator="parent" location="left"> Modifier la demande </v-tooltip>
    </v-btn>
  </div>
</template>

<script setup>
  import { ref, computed, onMounted } from 'vue'
  import { useRouter, useRoute } from 'vue-router'
  import BaseDetailView from '@/components/common/BaseDetailView.vue'
  import { FormSelect, FormTextarea } from '@/components/common'
  import ConfirmationModal from '@/components/common/ConfirmationModal.vue'
  import DocumentList from '@/components/DocumentList.vue'
  import { useApi } from '@/composables/useApi'
  import {
    API_BASE_URL,
    FAILURE_STATUS,
    FAILURE_STATUS_COLORS,
    EQUIPMENT_STATUS,
    EQUIPMENT_STATUS_COLORS,
  } from '@/utils/constants'
  import { useStore } from 'vuex'
  import { getStatusColor, getStatusLabel } from '@/utils/helpers'

  const store = useStore()
  const router = useRouter()
  const route = useRoute()
  const failureApi = useApi(API_BASE_URL)
  const equipmentApi = useApi(API_BASE_URL)
  const patchApi = useApi(API_BASE_URL)

  // Récupération de l'utilisateur connecté
  const currentUser = computed(() => store.getters.currentUser)

  const defaillance = ref(null)
  const loading = ref(false)
  const errorMessage = ref('')
  const successMessage = ref('')
  const showEquipmentDetails = ref(false)
  const showDocumentsDetails = ref(false)
  const showAcceptModal = ref(false)
  const acceptLoading = ref(false)
  const showRejectModal = ref(false)
  const rejectLoading = ref(false)
  const showCreateInterventionModal = ref(false)
  const createInterventionLoading = ref(false)

  const transformFormData = ref({
    diagnostic: '',
    statut_equipement: null,
  })

  const showArchiveDialog = ref(false)
  const archiving = ref(false)

  const statutOptions = Object.entries(EQUIPMENT_STATUS).map(([key, value]) => ({
    title: value,
    value: key,
  }))

  const canSubmitCreateIntervention = computed(() => {
    const diagnostic = (transformFormData.value.diagnostic || '').trim()
    const statut = transformFormData.value.statut_equipement
    return diagnostic.length >= 2 && diagnostic.length <= 2000 && !!statut
  })

  const formatDate = (dateString) => {
    if (!dateString) return 'Non spécifié'
    return new Date(dateString).toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const canClose = computed(
    () =>
      FAILURE_STATUS[defaillance.value?.statut] === FAILURE_STATUS.EN_ATTENTE ||
      FAILURE_STATUS[defaillance.value?.statut] === FAILURE_STATUS.ACCEPTEE
  )
  const canCreateIntervention = computed(
    () =>
      FAILURE_STATUS[defaillance.value?.statut] === FAILURE_STATUS.EN_ATTENTE ||
      FAILURE_STATUS[defaillance.value?.statut] === FAILURE_STATUS.ACCEPTEE
  )
  const canAccept = computed(
    () => FAILURE_STATUS[defaillance.value?.statut] === FAILURE_STATUS.EN_ATTENTE
  )

  // Permission de modification: Perm d'édition + créateur de la défaillance ou perm d'édition de toutes les défaillances
  const canEditFailure = computed(() => {
    if (!currentUser.value || !defaillance.value) return false
    const canEdit = store.getters.hasPermission('di:editCreated')
    const isCreator = defaillance.value.utilisateur.id === currentUser.value.id
    const canEditAllDis = store.getters.hasPermission('di:editAll')
    return (canEdit && isCreator) || canEditAllDis
  })

  const formattedEquipmentLabel = computed(() => {
    if (!defaillance.value?.equipement) return {}
    const eq = defaillance.value.equipement
    return {
      'Code GMAO': eq.reference || 'Non spécifié',
      Désignation: eq.designation || 'Non spécifié',
      Lieu: eq.lieu || 'Non spécifié',
      Statut: eq.dernier_statut?.statut || 'Non spécifié',
    }
  })

  const fetchData = async () => {
    loading.value = true
    errorMessage.value = ''

    try {
      const response = await failureApi.get(`demandes-intervention/${route.params.id}/`)
      const defaillanceData = response

      if (defaillanceData.equipement && typeof defaillanceData.equipement === 'object') {
        defaillanceData.equipement.dernier_statut = defaillanceData.equipement.dernier_statut || {}
      } else if (typeof defaillanceData.equipement === 'string') {
        const equipementResponse = await equipmentApi.get(
          `equipement/${defaillanceData.equipement}/affichage/`
        )
        defaillanceData.equipement = equipementResponse
        defaillanceData.equipement.dernier_statut = defaillanceData.equipement.dernier_statut || {}
      } else {
        defaillanceData.equipement = { dernier_statut: {} }
      }

      defaillance.value = defaillanceData
    } catch (error) {
      console.error('Erreur lors de la récupération des données:', error)
      errorMessage.value = 'Erreur lors du chargement des données'
    } finally {
      loading.value = false
    }
  }

  const archiveFailure = async () => {
    archiving.value = true
    try {
      await patchApi.patch(`demandes-intervention/${route.params.id}/set-archive/`, {
        archive: true,
      })
      successMessage.value = 'Demande archivée avec succès'
      showArchiveDialog.value = false
      setTimeout(() => {
        router.push({ name: 'FailureList' })
      }, 1000)
    } catch (error) {
      console.error("Erreur lors de l'archivage:", error)
      errorMessage.value = "Erreur lors de l'archivage de la demande"
      showArchiveDialog.value = false
    } finally {
      archiving.value = false
    }
  }

  const handleDelete = async () => {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette défaillance ?')) {
      try {
        await patchApi.delete(`demandes-intervention/${route.params.id}/`)
        successMessage.value = 'Défaillance supprimée avec succès'
        setTimeout(() => router.push({ name: 'FailureList' }), 1500)
      } catch {
        errorMessage.value = 'Erreur lors de la suppression'
      }
    }
  }

  const handleChangeStatusFailure = async (newStatus) => {
    rejectLoading.value = true
    acceptLoading.value = true
    try {
      await patchApi.patch(`demandes-intervention/${route.params.id}/updateStatus/`, {
        statut: newStatus,
      })
      successMessage.value = "Demande d'intervention " + FAILURE_STATUS[newStatus] + ' avec succès'
      showRejectModal.value = false
      showAcceptModal.value = false
      await fetchData()
    } catch {
      switch (newStatus) {
        case 'ACCEPTEE':
          errorMessage.value = "Erreur lors de l'acceptation de la demande"
          break
        case 'REFUSEE':
          errorMessage.value = 'Erreur lors du rejet de la demande'
          break
        default:
          errorMessage.value = 'Erreur lors du changement du statut de la demande'
      }
    } finally {
      rejectLoading.value = false
      acceptLoading.value = false
    }
  }

  const handleCreateIntervention = async () => {
    createInterventionLoading.value = true
    try {
      const response = await patchApi.post(
        `demandes-intervention/${route.params.id}/transform_to_bon_travail/`,
        {
          responsable: store.getters.currentUser.id,
          statut_equipement: transformFormData.value.statut_equipement,
          diagnostic: transformFormData.value.diagnostic,
        }
      )
      successMessage.value = "Demande d'intervention transformée avec succès"
      showCreateInterventionModal.value = false

      setTimeout(() => {
        router.push({ name: 'InterventionDetail', params: { id: response.id } })
      }, 1500)
    } catch {
      errorMessage.value = 'Erreur lors de la transformation de la demande'
    } finally {
      createInterventionLoading.value = false
    }
  }

  // Fonctions pour les modales
  const openAcceptModal = () => {
    showAcceptModal.value = true
  }
  const openRejectModal = () => {
    showRejectModal.value = true
  }
  const openCreateInterventionModal = () => {
    transformFormData.value = {
      diagnostic: '',
      statut_equipement:
        defaillance.value?.statut_suppose ||
        defaillance.value?.equipement?.dernier_statut?.statut ||
        null,
    }
    showCreateInterventionModal.value = true
  }

  const openEquipment = () => {
    if (defaillance.value?.equipement?.id) {
      if (route.query?.from) {
        router.push({
          name: 'EquipmentDetail',
          params: { id: defaillance.value.equipement.id },
          query: { from: 'failure-' + route.query.from, failureID: defaillance.value.id },
        })
        return
      }

      router.push({
        name: 'EquipmentDetail',
        params: { id: defaillance.value.equipement.id },
        query: { from: 'failure', failureID: defaillance.value.id },
      })
    }
  }

  const handleAddDocument = () => {
    if (route.query?.from) {
      router.push({
        name: 'AddDocumentFailure',
        params: { id: route.params.id },
        query: { from: route.query.from },
      })
      return
    }
    router.push({
      name: 'AddDocumentFailure',
      params: { id: route.params.id },
    })
  }

  const handleDownloadError = (message) => {
    errorMessage.value = message || 'Erreur lors du téléchargement'
  }

  const handleDownloadSuccess = () => {
    successMessage.value = 'Document téléchargé'
  }

  const handleDeleteSuccess = async () => {
    successMessage.value = 'Document supprimé'
    await fetchData()
  }

  const handleDeleteError = (message) => {
    errorMessage.value = message || 'Erreur lors de la suppression du document'
  }

  const editCurrentFailure = () => {
    router.push({
      name: 'EditFailure',
      params: { id: route.params.id },
    })
  }

  onMounted(() => {
    fetchData()
  })
</script>

<style scoped>
  .detail-field {
    margin-bottom: 16px;
  }

  .detail-label {
    display: block;
    font-weight: 600;
    font-size: 0.875rem;
    color: var(--text-color);
    opacity: 0.7;
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .detail-value {
    font-size: 1rem;
    color: var(--text-color);
    padding: 8px 0;
    border-bottom: 1px solid rgba(128, 128, 128, 0.25);
  }

  /*****************
  Bouton flottant
*****************/
  .floating-buttons {
    position: fixed !important;
    bottom: 24px;
    right: 24px;
    z-index: 100;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
</style>
