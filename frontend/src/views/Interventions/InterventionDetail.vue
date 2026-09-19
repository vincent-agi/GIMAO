<template>
  <BaseDetailView
    :title="'Détail du bon de travail'"
    :data="intervention"
    :loading="loading"
    :error-message="errorMessage"
    :success-message="successMessage"
    :auto-display="false"
    :show-edit-button="false"
    :show-delete-button="false"
    @clear-error="errorMessage = ''"
    @clear-success="successMessage = ''"
  >
    <template #default="{ data }">
      <v-row v-if="data">
        <!-- Colonne gauche : champs du BT -->
        <v-col cols="12" md="6" class="detail-column">
          <h3 class="text-h6 mb-4 text-primary detail-title">
            {{ data.nom }}
            <span v-if="equipement" class="text-medium-emphasis font-weight-regular">
              - {{ equipement.designation }}
            </span>
          </h3>
          <div class="detail-field">
            <label class="detail-label">ID</label>
            <div class="detail-value">{{ data.id || 'Non spécifié' }}</div>
          </div>

          <div class="detail-field">
            <label class="detail-label">Type</label>
            <div class="detail-value">
              {{ INTERVENTION_TYPE[data.type] || data.type || 'Non spécifié' }}
            </div>
          </div>

          <div class="detail-field">
            <label class="detail-label">Statut</label>
            <div class="detail-value">
              <v-chip :color="getInterventionStatusColor(data.statut)">
                {{ INTERVENTION_STATUS[data.statut] || data.statut || 'Non spécifié' }}
              </v-chip>
            </div>
          </div>

          <div class="detail-field">
            <label class="detail-label">Diagnostic</label>
            <div class="detail-value text-pre">
              {{ data.diagnostic || 'Non spécifié' }}
            </div>
          </div>

          <div class="detail-field">
            <label class="detail-label">Date d'assignation</label>
            <div class="detail-value">{{ formatDateTime(data.date_assignation) }}</div>
          </div>

          <div class="detail-field">
            <label class="detail-label">Date de début prévue</label>
            <div class="detail-value">{{ formatDateTime(data.date_prevue) }}</div>
          </div>

          <div class="detail-field">
            <label class="detail-label">Durée prévue</label>
            <div class="detail-value">{{ formatDuration(data.duree_previsionnelle) }}</div>
          </div>

          <div class="detail-field">
            <label class="detail-label">Date de début</label>
            <div class="detail-value">{{ formatDateTime(data.date_debut) }}</div>
          </div>

          <div class="detail-field">
            <label class="detail-label">Date de fin</label>
            <div class="detail-value">{{ formatDateTime(data.date_fin) }}</div>
          </div>

          <div class="detail-field">
            <label class="detail-label">Date de clôture</label>
            <div class="detail-value">{{ formatDateTime(data.date_cloture) }}</div>
          </div>

          <!-- Boutons d'action -->
          <v-row class="mt-6">
            <v-col cols="12" xl="6" class="py-1">
              <v-btn
                v-if="canStartIntervention"
                color="info"
                block
                :disabled="!canStart"
                @click="openStartModal"
                >Démarrer l'intervention</v-btn
              >
            </v-col>
            <v-col cols="12" xl="6" class="py-1">
              <v-btn
                v-if="canFinishIntervention"
                color="info"
                block
                :disabled="!canFinish"
                @click="openFinishModal"
                >Terminer l'intervention</v-btn
              >
            </v-col>
            <v-col
              v-if="store.getters.hasPermission('bt:acceptClosure')"
              cols="12"
              xl="6"
              class="py-1"
            >
              <v-btn
                v-if="store.getters.hasPermission('bt:acceptClosure')"
                color="success"
                class="text-white"
                block
                :disabled="!canClose"
                @click="openCloseModal"
                >Clôturer le BT</v-btn
              >
            </v-col>
            <v-col
              v-if="store.getters.hasPermission('bt:refuseClosure')"
              cols="12"
              xl="6"
              class="py-1"
            >
              <v-btn color="error" block :disabled="!canRefuseClose" @click="openRefuseCloseModal"
                >Refuser la clôture du BT</v-btn
              >
            </v-col>
          </v-row>
        </v-col>

        <!-- Colonne droite : commentaires + FK en sous-sections -->
        <v-col cols="12" md="6" class="detail-column">
          <!-- Spacer pour aligner avec le titre (nom) de la colonne gauche -->
          <h3 class="text-h6 mb-4">&nbsp;</h3>

          <div class="detail-field">
            <label class="detail-label">Commentaire</label>
            <div class="detail-value text-pre">
              {{ data.commentaire || 'Aucun commentaire' }}
            </div>
          </div>

          <div class="detail-field">
            <label class="detail-label">Commentaire de refus de clôture</label>
            <div class="detail-value text-pre">
              {{ data.commentaire_refus_cloture || 'Non spécifié' }}
            </div>
          </div>

          <!-- Section Affectation -->
          <v-card class="mt-4" elevation="2">
            <v-card-title
              class="text-h6 d-flex align-center cursor-pointer"
              @click="showAffectation = !showAffectation"
            >
              Affectation
              <v-spacer></v-spacer>
              <v-icon>
                {{ showAffectation ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
              </v-icon>
            </v-card-title>
            <v-expand-transition>
              <div v-show="showAffectation">
                <v-divider></v-divider>
                <v-card-text>
                  <div class="detail-field">
                    <label class="detail-label">Responsable</label>
                    <div class="detail-value">
                      <span v-if="data.responsable">{{
                        formatUserDisplay(data.responsable) || 'Non spécifié'
                      }}</span>
                      <span v-else>Non spécifié</span>
                    </div>
                  </div>
                  <div class="detail-field">
                    <label class="detail-label">Utilisateurs assignés</label>
                    <div class="detail-value">
                      <div
                        v-if="
                          Array.isArray(data.utilisateur_assigne) && data.utilisateur_assigne.length
                        "
                      >
                        <div v-for="u in data.utilisateur_assigne" :key="u.id">
                          - {{ formatUserDisplay(u) || 'Non spécifié' }}
                        </div>
                      </div>
                      <div v-else>Non spécifié</div>
                    </div>
                  </div>
                </v-card-text>
              </div>
            </v-expand-transition>
          </v-card>

          <!-- Section DI -->
          <v-card class="mt-4" elevation="2">
            <v-card-title
              class="text-h6 d-flex align-center cursor-pointer"
              @click="toggleDemandeDetails"
            >
              Demande d'intervention
              <v-spacer></v-spacer>
              <v-btn
                color="primary"
                size="small"
                class="mr-2"
                :disabled="!demandeId"
                @click.stop="openFailure"
              >
                Ouvrir
              </v-btn>
              <v-icon>
                {{ showDemandeDetails ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
              </v-icon>
            </v-card-title>
            <v-expand-transition>
              <div v-show="showDemandeDetails">
                <v-divider></v-divider>
                <v-card-text>
                  <div v-for="(value, key) in formattedDemande" :key="key" class="detail-field">
                    <label class="detail-label">{{ key }}</label>
                    <div class="detail-value">{{ value }}</div>
                  </div>
                </v-card-text>
              </div>
            </v-expand-transition>
          </v-card>

          <!-- Section Équipement (provient de la DI) -->
          <v-card class="mt-4" elevation="2">
            <v-card-title
              class="text-h6 d-flex align-center cursor-pointer"
              @click="toggleEquipementDetails"
            >
              {{ equipement ? equipement.designation : 'Équipement' }}
              <v-spacer></v-spacer>
              <v-btn
                color="primary"
                size="small"
                class="mr-2"
                :disabled="!equipementId"
                @click.stop="openEquipement"
              >
                Ouvrir
              </v-btn>
              <v-icon>
                {{ showEquipementDetails ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
              </v-icon>
            </v-card-title>
            <v-expand-transition>
              <div v-show="showEquipementDetails">
                <v-divider></v-divider>
                <v-card-text>
                  <div v-if="!equipement">Aucun équipement associé</div>
                  <div v-else>
                    <div
                      v-for="(value, key) in formattedEquipement"
                      :key="key"
                      class="detail-field"
                    >
                      <label class="detail-label">{{ key }}</label>
                      <div v-if="key !== 'Statut'" class="detail-value">{{ value }}</div>
                      <v-chip v-else :color="getStatusColor(value)" variant="tonal">{{
                        getStatusLabel(value)
                      }}</v-chip>
                    </div>
                  </div>
                </v-card-text>
              </div>
            </v-expand-transition>
          </v-card>

          <!-- Section Documents -->
          <v-card class="mt-4" elevation="2">
            <v-card-title
              class="text-h6 d-flex align-center cursor-pointer"
              @click="toggleDocumentsDetails"
            >
              Documents
              <v-spacer></v-spacer>
              <v-btn
                v-if="canUserEditBT"
                color="primary"
                size="small"
                class="mr-2"
                @click.stop="addDocument"
              >
                <v-icon left>mdi-plus</v-icon>
                Ajouter
              </v-btn>
              <v-icon>
                {{ showDocumentsDetails ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
              </v-icon>
            </v-card-title>
            <v-expand-transition>
              <div v-show="showDocumentsDetails">
                <v-divider></v-divider>
                <v-card-text>
                  <h4 class="text-subtitle-1 mb-2">Documents du BT</h4>
                  <DocumentList
                    v-if="(data.documentsBT || data.liste_documents_intervention || []).length > 0"
                    :documents="data.documentsBT || data.liste_documents_intervention || []"
                    :show-type="true"
                    :show-delete="canUserEditBT"
                    @delete-success="handleDeleteSuccess"
                    @delete-error="handleDeleteError"
                    @download-error="handleDownloadError"
                    @download-success="handleDownloadSuccess"
                  />
                  <p v-else class="text-caption text-grey">
                    Aucun document associé au Bon de Travail
                  </p>

                  <h4 class="text-subtitle-1 mt-6 mb-2">Documents de la DI</h4>
                  <DocumentList
                    v-if="(data.documentsDI || []).length > 0"
                    :documents="data.documentsDI || []"
                    :show-type="true"
                    :show-delete="canUserEditBT"
                    @delete-success="handleDeleteSuccess"
                    @delete-error="handleDeleteError"
                    @download-error="handleDownloadError"
                    @download-success="handleDownloadSuccess"
                  />
                  <p v-else class="text-caption text-grey">
                    Aucun document associé à la Demande d'Intervention
                  </p>
                </v-card-text>
              </div>
            </v-expand-transition>
          </v-card>

          <!-- Section Consommables (juste après Documents) -->
          <v-card class="mt-4" elevation="2">
            <v-card-title
              class="text-h6 d-flex align-center cursor-pointer"
              @click="toggleConsommablesDetails"
            >
              Consommables
              <v-spacer></v-spacer>
              <v-icon>
                {{ showConsommablesDetails ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
              </v-icon>
            </v-card-title>
            <v-expand-transition>
              <div v-show="showConsommablesDetails">
                <v-divider></v-divider>
                <v-card-text>
                  <v-data-table
                    v-if="Array.isArray(data.consommables) && data.consommables.length"
                    :headers="consommableHeaders"
                    :items="data.consommables"
                    class="elevation-1"
                    hide-default-footer
                    :items-per-page="-1"
                  >
                    <template #[`item.image`]="{ item }">
                      <div class="d-flex justify-center">
                        <v-img
                          v-if="item.image"
                          :src="`${BASE_URL}/media/${String(item.image).replace(/^\/+/, '')}`"
                          max-width="48"
                          max-height="48"
                          cover
                        />
                        <span v-else class="text-caption text-grey">-</span>
                      </div>
                    </template>
                    <template #[`item.designation`]="{ item }">
                      {{ item.designation || 'Non spécifié' }}
                    </template>
                    <template #[`item.quantite`]="{ item }">
                      {{ Number.isFinite(item.quantite) ? item.quantite : (item.quantite ?? 0) }}
                    </template>
                  </v-data-table>
                  <p v-else class="text-caption text-grey">Aucun consommable associé</p>
                </v-card-text>
              </div>
            </v-expand-transition>
          </v-card>
        </v-col>
      </v-row>
    </template>
  </BaseDetailView>

  <!-- Boutons flottants -->
  <div class="floating-buttons">
    <v-btn
      v-if="!intervention?.archive && store.getters.hasPermission('bt:archive')"
      color="warning"
      size="large"
      icon
      elevation="4"
      class="mb-3 d-block"
      @click="showArchiveDialog = true"
    >
      <v-icon size="large">mdi-archive-arrow-down</v-icon>
      <v-tooltip activator="parent" location="left"> Archiver le bon de travail </v-tooltip>
    </v-btn>

    <v-btn
      v-if="canUserEditBT"
      color="primary"
      size="large"
      icon
      elevation="4"
      class="d-block"
      @click="goToEditIntervention"
    >
      <v-icon size="large">mdi-pencil</v-icon>
      <v-tooltip activator="parent" location="left"> Modifier l'intervention </v-tooltip>
    </v-btn>
  </div>

  <!-- Modale d'archivage -->
  <ConfirmationModal
    v-model="showArchiveDialog"
    title="Confirmer l'archivage"
    message="Êtes-vous sûr de vouloir archiver ce bon de travail ?
            Il ne sera plus visible dans la liste principale."
    confirm-text="Archiver"
    @confirm="archiveIntervention"
    @cancel="showArchiveDialog = false"
  />

  <!-- Modales de confirmation (comme DI) -->
  <ConfirmationModal
    v-model="showStart"
    type="info"
    title="Démarrer l'intervention"
    message="Êtes-vous sûr de vouloir démarrer cette intervention ?"
    confirm-text="Démarrer"
    confirm-icon="mdi-play"
    :loading="actionLoading"
    @confirm="startIntervention"
    @cancel="showStart = false"
  />
  <ConfirmationModal
    v-model="showFinish"
    type="info"
    title="Terminer l'intervention"
    message="Êtes-vous sûr de vouloir terminer cette intervention ?"
    confirm-text="Terminer"
    confirm-icon="mdi-check"
    :loading="actionLoading"
    @confirm="finishIntervention"
    @cancel="showFinish = false"
  />
  <ConfirmationModal
    v-model="showClose"
    type="success"
    title="Clôturer le bon de travail"
    message="Êtes-vous sûr de vouloir clôturer ce bon de travail ?"
    confirm-text="Clôturer"
    confirm-icon="mdi-check-circle-outline"
    :loading="actionLoading"
    @confirm="closeBonTravail"
    @cancel="showClose = false"
  />

  <!-- Refuser la clôture : formulaire (commentaire obligatoire) -->
  <v-dialog v-model="showRefuseClose" max-width="600" scrollable>
    <v-card class="rounded-xl intervention-dialog-card">
      <v-card-text class="pa-6 refuse-close-dialog__body">
        <BaseForm
          v-model="refuseCloseFormData"
          title="Refuser la clôture"
          :validation-schema="refuseCloseValidationSchema"
          :loading="actionLoading"
          :error-message="errorMessage"
          :success-message="successMessage"
          submit-button-text="Refuser"
          submit-button-color="error"
          cancel-button-text="Annuler"
          :custom-cancel-action="() => (showRefuseClose = false)"
          :handle-submit="refuseCloseBonTravail"
          container-class="dialog-form-shell"
          card-class="dialog-form-card"
          title-class="dialog-form-title"
          content-class="dialog-form-content"
          elevation="0"
          @clear-error="errorMessage = ''"
          @clear-success="successMessage = ''"
        >
          <template #default>
            <v-row dense>
              <v-col cols="12">
                <FormTextarea
                  v-model="refuseCloseFormData.commentaire_refus_cloture"
                  field-name="commentaire_refus_cloture"
                  label="Commentaire de refus"
                  rows="4"
                />
              </v-col>
            </v-row>
          </template>
        </BaseForm>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
  import { ref, onMounted, computed } from 'vue'
  import { useRouter, useRoute } from 'vue-router'
  import { useStore } from 'vuex'
  import BaseDetailView from '@/components/common/BaseDetailView.vue'
  import ConfirmationModal from '@/components/common/ConfirmationModal.vue'
  import DocumentList from '@/components/DocumentList.vue'
  import { BaseForm, FormTextarea } from '@/components/common'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL, BASE_URL, INTERVENTION_STATUS, INTERVENTION_TYPE } from '@/utils/constants'
  import {
    formatDateTime,
    formatDuration,
    getInterventionStatusColor,
    getStatusColor,
    getStatusLabel,
  } from '@/utils/helpers'

  const router = useRouter()
  const route = useRoute()
  const store = useStore()

  const api = useApi(API_BASE_URL)

  const currentUser = computed(() => store.getters.currentUser)

  const intervention = ref(null)
  const loading = ref(false)
  const actionLoading = ref(false)
  const errorMessage = ref('')
  const successMessage = ref('')

  const MESSAGE_TIMEOUT_MS = 3000

  const showDemandeDetails = ref(false)
  const showDocumentsDetails = ref(false)
  const showConsommablesDetails = ref(false)
  const showAffectation = ref(false)
  const showEquipementDetails = ref(false)

  const showArchiveDialog = ref(false)
  const archiving = ref(false)

  const showStart = ref(false)
  const showFinish = ref(false)
  const showClose = ref(false)
  const showRefuseClose = ref(false)
  const refuseCloseFormData = ref({
    commentaire_refus_cloture: '',
  })

  const refuseCloseValidationSchema = {
    commentaire_refus_cloture: ['required', { name: 'maxLength', params: [500] }],
  }

  const consommableHeaders = [
    { title: 'Image', value: 'image', sortable: false, align: 'center' },
    { title: 'Désignation', value: 'designation' },
    { title: 'Quantité', value: 'quantite', align: 'center' },
  ]

  const demandeId = computed(() => intervention.value?.demande_intervention?.id)

  const equipement = computed(() => intervention.value?.demande_intervention?.equipement || null)
  const equipementId = computed(() => equipement.value?.id)

  const formattedDemande = computed(() => {
    const demande = intervention.value?.demande_intervention
    if (!demande) return {}
    return {
      'Nom de la demande': demande.nom || 'Non spécifié',
      Commentaire: demande.commentaire || 'Aucun commentaire',
      Demandeur: formatUserDisplay(demande.utilisateur) || 'Non spécifié',
      'Date de creation': formatDateTime(demande.date_creation) || 'Non spécifié',
    }
  })

  const formattedEquipement = computed(() => {
    const e = equipement.value
    if (!e) return {}
    return {
      'Code GMAO': e.reference || 'Non spécifié',
      Désignation: e.designation || 'Non spécifié',
      Lieu: e.lieu || 'Non spécifié',
      Statut: e.dernier_statut?.statut || 'Non spécifié',
    }
  })

  const canClose = computed(
    () =>
      !intervention.value?.date_cloture &&
      intervention.value?.statut !== 'CLOTURE' &&
      store.getters.hasPermission('bt:acceptClosure')
  )
  const canStart = computed(
    () =>
      ['EN_ATTENTE', 'EN_RETARD'].includes(intervention.value?.statut) &&
      store.getters.hasPermission('bt:start')
  )
  const canFinish = computed(
    () => intervention.value?.statut === 'EN_COURS' && store.getters.hasPermission('bt:end')
  )
  const canRefuseClose = computed(
    () =>
      intervention.value?.statut === 'TERMINE' && store.getters.hasPermission('bt:refuseClosure')
  )

  // Méthodes pour cacher les boutons si l'utilisateur n'a pas les droits
  const canStartIntervention = computed(() => {
    const isAssigned = isUserAssignedToIntervention.value
    const isCreator = intervention.value?.utilisateur_createur?.id === currentUser.value?.id
    const isResponsable = intervention.value?.responsable?.id === currentUser.value?.id
    return isAssigned || isCreator || isResponsable
  })

  const canFinishIntervention = computed(() => {
    const isAssigned = isUserAssignedToIntervention.value
    const isCreator = intervention.value?.utilisateur_createur?.id === currentUser.value.id
    const isResponsable = intervention.value?.responsable?.id === currentUser.value?.id
    return isAssigned || isCreator || isResponsable
  })

  const canUserEditBT = computed(() => {
    const isAssigned = isUserAssignedToIntervention.value
    const isCreator = intervention.value?.utilisateur_createur?.id === currentUser.value.id
    const canEditAssignedBT = store.getters.hasPermission('bt:editAssigned')
    const canEditAllBT = store.getters.hasPermission('bt:editAll')
    return (isAssigned && canEditAssignedBT) || canEditAllBT || isCreator
  })

  const isUserAssignedToIntervention = computed(() => {
    if (!intervention.value || !currentUser.value) return false
    return intervention.value.utilisateur_assigne.map((u) => u.id).includes(currentUser.value.id)
  })

  const openStartModal = () => {
    showStart.value = true
  }

  const openFinishModal = () => {
    showFinish.value = true
  }

  const openCloseModal = () => {
    showClose.value = true
  }

  const openRefuseCloseModal = () => {
    refuseCloseFormData.value = { commentaire_refus_cloture: '' }
    showRefuseClose.value = true
  }

  const goToEditIntervention = () => {
    const id = intervention.value?.id ?? route.params.id
    if (!id) return

    if (route.query.from) {
      router.push({
        name: 'EditIntervention',
        params: { id },
        query: { from: route.query.from, interventionId: route.params.id },
      })
      return
    }

    router.push({ name: 'EditIntervention', params: { id } })
  }

  const archiveIntervention = async () => {
    archiving.value = true
    try {
      await api.patch(`bons-travail/${route.params.id}/set-archive/`, { archive: true })
      successMessage.value = 'Bon de travail archivé avec succès'
      showArchiveDialog.value = false
      setTimeout(() => {
        router.push({ name: 'InterventionList' })
      }, 1000)
    } catch (error) {
      console.error("Erreur lors de l'archivage:", error)
      errorMessage.value = "Erreur lors de l'archivage du bon de travail"
      showArchiveDialog.value = false
    } finally {
      archiving.value = false
    }
  }

  const fetchData = async () => {
    loading.value = true
    errorMessage.value = ''
    try {
      intervention.value = await api.get(`bons-travail/${route.params.id}`)
    } catch {
      errorMessage.value = 'Erreur lors du chargement des données'
      setTimeout(() => (errorMessage.value = ''), MESSAGE_TIMEOUT_MS)
    } finally {
      loading.value = false
    }
  }

  const toggleDemandeDetails = () => {
    showDemandeDetails.value = !showDemandeDetails.value
  }

  const toggleDocumentsDetails = () => {
    showDocumentsDetails.value = !showDocumentsDetails.value
  }

  const toggleConsommablesDetails = () => {
    showConsommablesDetails.value = !showConsommablesDetails.value
  }

  const toggleEquipementDetails = () => {
    showEquipementDetails.value = !showEquipementDetails.value
  }

  const formatUserDisplay = (user) => {
    if (!user) return ''
    const prenom = String(user.prenom || '').trim()
    const nomFamille = String(user.nomFamille || '').trim()
    if (prenom || nomFamille) return `${prenom} ${nomFamille}`.trim()
    const nomUtilisateur = String(user.nomUtilisateur || '').trim()
    return nomUtilisateur || ''
  }

  const openFailure = () => {
    if (demandeId.value) {
      router.push({
        name: 'FailureDetail',
        params: { id: demandeId.value },
        query: { from: 'intervention', interventionId: route.params.id },
      })
    }
  }

  const openEquipement = () => {
    if (!equipementId.value) return

    if (route.query.from) {
      router.push({
        name: 'EquipmentDetail',
        params: { id: equipementId.value },
        query: { from: 'intervention-' + route.query.from, interventionId: route.params.id },
      })
      return
    }

    router.push({
      name: 'EquipmentDetail',
      params: { id: equipementId.value },
      query: { from: 'intervention', interventionId: route.params.id },
    })
  }

  const addDocument = () => {
    if (!intervention.value?.id) return
    if (route.query.from) {
      router.push({
        name: 'AddDocumentIntervention',
        params: { id: intervention.value.id },
        query: { from: route.query.from, interventionId: route.params.id },
      })
      return
    }

    router.push({ name: 'AddDocumentIntervention', params: { id: intervention.value.id } })
  }

  const closeBonTravail = async () => {
    if (!intervention.value?.id) return
    actionLoading.value = true
    try {
      await api.patch(`bons-travail/${intervention.value.id}/updateStatus/`, {
        statut: 'CLOTURE',
        user: currentUser.value?.id,
      })
      successMessage.value = 'Bon de travail clôturé'
      setTimeout(() => (successMessage.value = ''), MESSAGE_TIMEOUT_MS)
      showClose.value = false
      await fetchData()
    } catch {
      errorMessage.value = 'Erreur lors de la clôture du bon de travail'
      setTimeout(() => (errorMessage.value = ''), MESSAGE_TIMEOUT_MS)
    } finally {
      actionLoading.value = false
    }
  }

  const refuseCloseBonTravail = async () => {
    if (!intervention.value?.id) return
    actionLoading.value = true
    try {
      await api.patch(`bons-travail/${intervention.value.id}/updateStatus/`, {
        statut: 'EN_ATTENTE',
        commentaire_refus_cloture: refuseCloseFormData.value.commentaire_refus_cloture,
        user: currentUser.value?.id,
      })
      successMessage.value = 'Clôture refusée'
      setTimeout(() => (successMessage.value = ''), MESSAGE_TIMEOUT_MS)
      showRefuseClose.value = false
      await fetchData()
    } catch {
      errorMessage.value = 'Erreur lors du refus de clôture'
      setTimeout(() => (errorMessage.value = ''), MESSAGE_TIMEOUT_MS)
    } finally {
      actionLoading.value = false
    }
  }

  const startIntervention = async () => {
    if (!intervention.value?.id) return
    actionLoading.value = true
    try {
      await api.patch(`bons-travail/${intervention.value.id}/updateStatus/`, {
        statut: 'EN_COURS',
        user: currentUser.value?.id,
      })
      successMessage.value = 'Intervention démarrée'
      setTimeout(() => (successMessage.value = ''), MESSAGE_TIMEOUT_MS)
      showStart.value = false
      await fetchData()
    } catch {
      errorMessage.value = "Erreur lors du démarrage de l'intervention"
      setTimeout(() => (errorMessage.value = ''), MESSAGE_TIMEOUT_MS)
    } finally {
      actionLoading.value = false
    }
  }

  const finishIntervention = async () => {
    if (!intervention.value?.id) return
    actionLoading.value = true
    try {
      await api.patch(`bons-travail/${intervention.value.id}/updateStatus/`, {
        statut: 'TERMINE',
        user: currentUser.value?.id,
      })
      successMessage.value = 'Intervention terminée'
      setTimeout(() => (successMessage.value = ''), MESSAGE_TIMEOUT_MS)
      showFinish.value = false
      await fetchData()
    } catch {
      errorMessage.value = "Erreur lors de la fin de l'intervention"
      setTimeout(() => (errorMessage.value = ''), MESSAGE_TIMEOUT_MS)
    } finally {
      actionLoading.value = false
    }
  }

  const handleDownloadError = (message) => {
    errorMessage.value = message || 'Erreur lors du téléchargement du fichier'
    setTimeout(() => (errorMessage.value = ''), MESSAGE_TIMEOUT_MS)
  }

  const handleDownloadSuccess = () => {
    successMessage.value = 'Document téléchargé'
    setTimeout(() => (successMessage.value = ''), MESSAGE_TIMEOUT_MS)
  }

  const handleDeleteSuccess = async () => {
    successMessage.value = 'Document supprimé'
    setTimeout(() => (successMessage.value = ''), MESSAGE_TIMEOUT_MS)
    await fetchData()
  }

  const handleDeleteError = (message) => {
    errorMessage.value = message || 'Erreur lors de la suppression du document'
    setTimeout(() => (errorMessage.value = ''), MESSAGE_TIMEOUT_MS)
  }

  onMounted(fetchData)
</script>

<style scoped>
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

<style scoped>
  .doc-truncate {
    display: block;
    max-width: 100%;
    white-space: normal;
    overflow-wrap: anywhere;
    word-break: break-word;
  }

  .doc-actions {
    display: inline-flex;
    flex-wrap: nowrap;
    align-items: center;
    white-space: nowrap;
  }

  .detail-column {
    min-width: 0;
  }

  .detail-field {
    margin-bottom: 16px;
    min-width: 0;
  }

  .detail-title {
    display: block;
    width: 100%;
    max-width: 100%;
    min-width: 0;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
    word-break: break-word !important;
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
    display: block;
    width: 100%;
    max-width: 100%;
    min-width: 0;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
    word-break: break-word !important;
  }

  .cursor-pointer {
    cursor: pointer;
  }

  .intervention-dialog-card {
    border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
    box-shadow: 0 22px 50px rgba(10, 15, 30, 0.18);
  }

  .refuse-close-dialog__body {
    background: transparent;
  }

  .refuse-close-dialog__body :deep(.dialog-form-shell) {
    padding: 0;
  }

  .refuse-close-dialog__body :deep(.dialog-form-card) {
    background: rgba(var(--v-theme-on-surface), 0.02);
    border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
    border-radius: 20px;
    overflow: hidden;
  }

  .refuse-close-dialog__body :deep(.dialog-form-title) {
    color: rgba(var(--v-theme-on-surface), 0.96);
    font-weight: 600;
    padding: 24px 24px 10px;
  }

  .refuse-close-dialog__body :deep(.dialog-form-content) {
    color: rgba(var(--v-theme-on-surface), 0.82);
    padding-top: 12px;
  }

  .text-pre {
    white-space: pre-wrap !important;
    overflow-wrap: anywhere !important;
    word-break: break-word !important;
    display: block;
    width: 100%;
  }

  .floating-create-button {
    position: fixed !important;
    bottom: 24px;
    right: 24px;
    z-index: 100;
  }
</style>
