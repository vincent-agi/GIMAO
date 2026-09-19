<template>
  <BaseDetailView
    :title="equipement.designation || 'Détail de l\'équipement'"
    :data="equipement"
    :loading="isLoading"
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
        <!-- Section gauche : Détails de l'équipement -->
        <v-col cols="12" md="4">
          <h3 class="text-h6 mb-4 text-primary">Description de l'équipement</h3>

          <div v-for="(value, key) in equipmentDetails" :key="key" class="detail-field">
            <label v-if="key !== 'id'" class="detail-label">{{ formatLabel(key) }}</label>
            <div v-if="key !== 'id'" class="detail-value">
              <v-chip v-if="key === 'statut'" :color="getStatusColor(value)" dark size="small">
                {{ getStatusLabel(value) || 'Inconnu' }}
              </v-chip>
              <span v-else>{{ formatValue(value) }}</span>
            </div>
          </div>

          <!-- Section documentation -->
          <v-card elevation="2" class="mt-4">
            <v-card-title class="text-h6">Documentation</v-card-title>
            <v-divider></v-divider>

            <!-- Documents techniques -->
            <v-card-text>
              <h4 class="mb-2">Documents des plans de maintenance</h4>
              <DocumentList
                v-if="technicalDocuments.length > 0"
                :documents="technicalDocuments"
                :show-type="true"
                :show-delete="false"
                @download-success="handleDownloadSuccess"
                @download-error="handleDownloadError"
                @delete-success="handleDeleteSuccess"
                @delete-error="handleDeleteError"
              />
              <p v-else class="text-caption text-grey">Aucun document technique disponible</p>
            </v-card-text>

            <!-- Documents de l'équipement -->
            <v-card-text>
              <div class="d-flex align-center justify-space-between mb-2">
                <h4>Documents de l'équipement</h4>
                <v-btn
                  v-if="store.getters.hasPermission('eq:document.add')"
                  size="small"
                  color="primary"
                  variant="outlined"
                  prepend-icon="mdi-plus"
                  @click="handleModalOpening"
                >
                  Ajouter
                </v-btn>
              </div>
              <DocumentList
                v-if="equipmentDocuments.length > 0"
                :documents="equipmentDocuments"
                :show-type="true"
                :show-delete="store.getters.hasPermission('eq:document.delete')"
                @download-success="handleDownloadSuccess"
                @download-error="handleDownloadError"
                @delete-success="handleDeleteSuccess"
                @delete-error="handleDeleteError"
              />
              <p v-else class="text-caption text-grey">Aucun document associé à l'équipement</p>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Section droite : Image, consommables, interventions et actions -->
        <v-col cols="12" md="8">
          <!-- Section image -->
          <v-card elevation="2" class="mb-4">
            <v-img
              v-if="data.lienImage"
              :src="`${BASE_URL}/media/${data.lienImage}`"
              aspect-ratio="4/3"
              class="rounded-lg"
              style="max-height: 30vh; object-fit: cover"
              alt="Image de l'équipement"
            >
              <template #placeholder>
                <v-row class="fill-height ma-0" align="center" justify="center">
                  <v-icon size="64" color="grey-lighten-2">mdi-image-off</v-icon>
                </v-row>
              </template>
            </v-img>
            <div v-else class="d-flex align-center justify-center pa-8">
              <v-icon size="64" color="grey-lighten-2">mdi-image-off</v-icon>
            </div>
          </v-card>

          <!-- Boutons d'action -->
          <v-card elevation="2" class="mb-4">
            <v-card-actions class="justify-center pa-4">
              <v-btn
                v-if="store.getters.hasPermission('di:create')"
                color="warning"
                prepend-icon="mdi-alert-circle"
                @click="signalFailure"
              >
                Créer une demande d'intervention (DI)
              </v-btn>
              <v-btn
                v-if="store.getters.hasPermission('eq:maintenance.calendar')"
                color="primary"
                prepend-icon="mdi-calendar-clock"
                @click="openMaintenanceCalendar"
              >
                Voir le calendrier maintenance
              </v-btn>
            </v-card-actions>
          </v-card>

          <!-- Historique des états -->
          <EquipmentStatusTimeline
            v-if="store.getters.hasPermission('eq:historique.view')"
            :equipement-id="route.params.id"
            class="mb-4"
          />

          <!-- KPI de maintenance corrective -->
          <KPIEquipementComponent
            v-if="store.getters.hasPermission('eq:kpi.view')"
            :equipement-id="route.params.id"
            class="mb-4"
          />

          <!-- Section compteurs -->
          <div>
            <v-card v-if="store.getters.hasPermission('cp:viewList')" elevation="2" class="mb-4">
              <v-card-title class="text-h6">Maintenances préventives</v-card-title>
              <v-divider></v-divider>
              <v-card-text>
                <v-data-table
                  v-if="filteredCounters"
                  :items="filteredCounters"
                  :headers="TABLE_HEADERS.COUNTER"
                  class="elevation-1"
                  hide-default-footer
                >
                  <template #[`item.valeurCourante`]="{ item }">
                    {{
                      item.type === 'Calendaire'
                        ? formatCalendarDate(item.valeurCourante)
                        : item.valeurCourante
                    }}
                  </template>

                  <template #[`item.type`]="{ item }">
                    {{ item.type === 'Calendaire' ? 'Calendrier' : item.type }}
                  </template>

                  <template #[`item.action`]="{ item }">
                    <v-btn icon size="small" @click="viewCounter(item)">
                      <v-icon>mdi-eye</v-icon>
                    </v-btn>
                  </template>
                </v-data-table>
                <p v-else class="text-caption text-grey">
                  Aucune maintenance préventive disponible
                </p>
              </v-card-text>
              <div class="justify-end d-flex">
                <v-btn
                  v-if="store.getters.hasPermission('cp:create')"
                  text
                  color="primary align-self-end"
                  class="my-2 mx-2"
                  @click="openAddCounterDialog"
                >
                  Ajouter une maintenance préventive
                </v-btn>
              </div>
            </v-card>
          </div>

          <!-- Historique des interventions -->
          <div>
            <v-card elevation="2" class="mb-4">
              <v-card-title class="text-h6">Interventions</v-card-title>
              <v-divider></v-divider>
              <v-card-text>
                <v-data-table
                  v-if="data.bons_travail && data.bons_travail.length > 0"
                  :items="data.bons_travail"
                  :headers="TABLE_HEADERS.INTERVENTIONS_EQUIPMENT"
                  class="elevation-1"
                  hide-default-footer
                >
                  <template #[`item.date_assignation`]="{ item }">
                    {{ formatDate(item.date_assignation) }}
                  </template>
                  <template #[`item.statut`]="{ item }">
                    <v-chip :color="getStatusColor(item.statut)" dark size="small">
                      {{ INTERVENTION_STATUS[item.statut] || item.statut }}
                    </v-chip>
                  </template>
                  <template #[`item.action`]="{ item }">
                    <v-btn icon size="small" @click="viewIntervention(item)">
                      <v-icon>mdi-eye</v-icon>
                    </v-btn>
                  </template>
                </v-data-table>
                <p v-else class="text-caption text-grey">Aucune intervention enregistrée</p>
              </v-card-text>
            </v-card>
          </div>

          <!-- Section consommables -->
          <v-card elevation="2" class="mb-4">
            <v-card-title class="text-h6">Consommables</v-card-title>
            <v-divider></v-divider>
            <v-card-text>
              <v-data-table
                v-if="data.consommables && data.consommables.length > 0"
                :items="data.consommables"
                :headers="TABLE_HEADERS.CONSUMABLES"
                class="elevation-1"
                hide-default-footer
              >
                <template #[`item.reference`]="{ item }">
                  {{ item.reference || 'Non spécifié' }}
                </template>
                <template #[`item.fabricant`]="{ item }">
                  {{ item.fabricant || 'Non spécifié' }}
                </template>
                <template #[`item.designation`]="{ item }">
                  {{ item.designation || 'Sans nom' }}
                </template>
              </v-data-table>
              <p v-else class="text-caption text-grey">Aucun consommable associé</p>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </template>
  </BaseDetailView>

  <!-- Bouton flottant en bas à droite -->
  <div class="floating-buttons">
    <v-btn
      v-if="!equipement.archive && store.getters.hasPermission('eq:archive')"
      color="warning"
      size="large"
      icon
      elevation="4"
      class="mb-3 d-block"
      @click="showArchiveDialog = true"
    >
      <v-icon size="large">mdi-archive-arrow-down</v-icon>
      <v-tooltip activator="parent" location="left"> Archiver l'équipement </v-tooltip>
    </v-btn>

    <v-btn
      v-if="showEditButton"
      color="primary"
      size="large"
      icon
      elevation="4"
      class="d-block"
      @click="editCurrentEquip()"
    >
      <v-icon size="large">mdi-pencil</v-icon>
      <v-tooltip activator="parent" location="left">
        {{ editButtonText }}
      </v-tooltip>
    </v-btn>
  </div>

  <ConfirmationModal
    v-model="showArchiveDialog"
    title="Confirmer l'archivage"
    message="Êtes-vous sûr de vouloir archiver cet équipement ?
          Il ne sera plus visible dans la liste des équipements."
    confirm-text="Archiver"
    @confirm="archiveEquipment"
    @cancel="showArchiveDialog = false"
  />

  <!-- Dialog pour ajouter un document -->
  <v-dialog v-model="showAddDocumentDialog" max-width="900px" @click:outside="closeDocumentDialog">
    <v-card>
      <v-card-title>Ajouter un document</v-card-title>
      <v-divider />
      <v-card-text>
        <DocumentForm v-model="newDocuments" :type-documents="typesDocuments" />
      </v-card-text>
      <v-card-actions class="justify-end pa-4">
        <v-btn variant="text" @click="closeDocumentDialog">Annuler</v-btn>
        <v-btn color="primary" :loading="addingDocument" @click="submitDocument">Ajouter</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- Dialog pour ajouter une maintenance préventive -->
  <v-dialog v-model="showCounterDialog" max-width="600px" @click:outside="closeCounterDialog">
    <v-card>
      <v-card-title>Ajouter une maintenance préventive</v-card-title>
      <v-divider></v-divider>
      <v-card-text>
        <CounterInlineForm
          v-if="currentCounter"
          v-model="currentCounter"
          :is-edit-mode="false"
          @save="saveCounter"
          @cancel="closeCounterDialog"
        />
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
  import { ref, computed, onMounted } from 'vue'
  import { useStore } from 'vuex'
  import { useRouter, useRoute } from 'vue-router'
  import BaseDetailView from '@/components/common/BaseDetailView.vue'
  import CounterInlineForm from '@/components/Forms/CounterInlineForm.vue'
  import DocumentForm from '@/components/Forms/DocumentForm.vue'
  import DocumentList from '@/components/DocumentList.vue'
  import ConfirmationModal from '@/components/common/ConfirmationModal.vue'
  import KPIEquipementComponent from '@/components/KPIEquipementComponent.vue'
  import EquipmentStatusTimeline from '@/components/EquipmentStatusTimeline.vue'
  import { useApi } from '@/composables/useApi'
  import { getStatusColor, getStatusLabel, formatCalendarDate } from '@/utils/helpers'
  import { API_BASE_URL, BASE_URL, INTERVENTION_STATUS, TABLE_HEADERS } from '@/utils/constants'

  const router = useRouter()
  const route = useRoute()
  const api = useApi(API_BASE_URL)
  const store = useStore()

  const equipement = computed(() => api.data.value || {})
  const isLoading = computed(() => api.loading.value)
  const errorMessage = ref('')
  const successMessage = ref('')
  const showEditButton = ref(store.getters.hasPermission('eq:edit'))
  const editButtonText = ref("Modifier l'équipement")

  // Archive
  const showArchiveDialog = ref(false)
  const archiving = ref(false)

  const archiveEquipment = async () => {
    archiving.value = true
    try {
      await api.patch(`equipements/${route.params.id}/set-archive/`, { archive: true })
      successMessage.value = 'Équipement archivé avec succès'
      showArchiveDialog.value = false
      setTimeout(() => {
        router.push({ name: 'EquipmentList' })
      }, 1000)
    } catch (error) {
      console.error("Erreur lors de l'archivage:", error)
      errorMessage.value = "Erreur lors de l'archivage de l'équipement"
      showArchiveDialog.value = false
    } finally {
      archiving.value = false
    }
  }

  // Document
  const EMPTY_DOC = { nomDocument: '', typeDocument_id: null, file: null }
  const typesDocuments = ref([])
  const showAddDocumentDialog = ref(false)
  const addingDocument = ref(false)
  const newDocuments = ref([{ ...EMPTY_DOC }])

  const fetchTypesDocuments = async () => {
    if (typesDocuments.value.length > 0) return
    try {
      const docApi = useApi(API_BASE_URL)
      typesDocuments.value = (await docApi.get('types-documents/')) ?? []
    } catch (e) {
      console.error('Erreur chargement types documents:', e)
    }
  }

  const openModal = () => {
    showAddDocumentDialog.value = true
  }

  const handleModalOpening = async () => {
    await fetchTypesDocuments()
    openModal()
  }

  const closeDocumentDialog = () => {
    showAddDocumentDialog.value = false
    newDocuments.value = [{ ...EMPTY_DOC }]
  }

  const submitDocument = async () => {
    const doc = newDocuments.value[0]
    if (!doc?.file || !doc?.typeDocument_id) return

    addingDocument.value = true
    try {
      const fd = new FormData()
      fd.append('file', doc.file)
      fd.append('typeDocument_id', doc.typeDocument_id)
      if (doc.nomDocument) fd.append('nomDocument', doc.nomDocument)

      const docApi = useApi(API_BASE_URL)
      await docApi.post(`equipements/${route.params.id}/add_document/`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      successMessage.value = 'Document ajouté avec succès'
      closeDocumentDialog()
      await fetchEquipmentData()
      setTimeout(() => (successMessage.value = ''), 3000)
    } catch (error) {
      console.error('Erreur ajout document:', error)
      errorMessage.value = "Erreur lors de l'ajout du document"
    } finally {
      addingDocument.value = false
    }
  }

  // Dialog compteur
  const showCounterDialog = ref(false)
  const currentCounter = ref(null)

  const filteredCounters = computed(() => {
    if (!equipement.value.compteurs) return []
    // return equipement.value.compteurs.filter(counter => counter.type !== 'Calendaire');
    return equipement.value.compteurs
  })

  const getEmptyCounter = () => ({
    nomCompteur: '',
    unite: 'heures',
    valeurCourante: 0,
    estPrincipal: false,
    type: 'Numérique',
  })

  // Documents des plans de maintenance (techniques)
  const technicalDocuments = computed(() => {
    const docs = equipement.value.documents || []
    return docs.map((doc) => ({
      id: doc.id,
      titre: doc.titre,
      path: doc.path,
      type_nom: doc.type_nom || '-',
    }))
  })

  // Documents directement associés à l'équipement
  const equipmentDocuments = computed(() => {
    const docs = equipement.value.documents_equipement || []
    return docs.map((doc) => ({
      id: doc.id,
      titre: doc.titre,
      path: doc.path,
      type_nom: doc.type_nom || '-',
    }))
  })

  const equipmentDetails = computed(() => {
    if (!equipement.value) return {}
    const { id, reference, designation, dateMiseEnService, prixAchat } = equipement.value

    const type = equipement.value.type_display || ''
    const lieu = equipement.value.lieu?.nomLieu || ''
    const modele = equipement.value.modele?.nom || ''
    const fournisseur = equipement.value.fournisseur?.nom || ''
    const fabricant = equipement.value.fabricant?.nom || ''
    const statut = equipement.value.dernier_statut?.statut || ''

    return {
      id,
      reference,
      designation,
      type,
      dateMiseEnService,
      prixAchat,
      lieu,
      modele,
      fournisseur,
      fabricant,
      statut,
    }
  })

  const fetchEquipmentData = async () => {
    errorMessage.value = ''
    try {
      await api.get(`equipement/${route.params.id}/affichage/?seuils_lite=true`)
    } catch (error) {
      console.error("Erreur lors de la récupération des données de l'équipement:", error)
      errorMessage.value = "Erreur lors du chargement de l'équipement"
    }
  }

  const formatLabel = (key) => {
    const labels = {
      reference: 'Code GMAO',
      designation: 'Désignation',
      type: "Type d'équipement",
      dateMiseEnService: 'Date de mise en service',
      prixAchat: "Prix d'achat",
      lieu: 'Lieu',
      modele: 'Modèle',
      fournisseur: 'Fournisseur',
      fabricant: 'Fabricant',
      statut: 'Statut',
    }
    return labels[key] || key
  }

  const isoDateTimeRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?$/

  const formatDate = (isoString) => {
    const d = new Date(isoString)
    if (isNaN(d.getTime())) return isoString

    return d
      .toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      })
      .replace(' ', ' à ')
  }

  const formatValue = (value) => {
    if (value === null || value === undefined) return '-'

    if (typeof value === 'boolean') {
      return value ? 'Oui' : 'Non'
    }

    if (typeof value === 'number') {
      return value.toLocaleString('fr-FR')
    }

    if (typeof value === 'string') {
      const trimmed = value.trim()

      if (isoDateTimeRegex.test(trimmed)) {
        const ts = Date.parse(trimmed)
        if (!isNaN(ts)) {
          return formatDate(trimmed)
        }
        return trimmed
      }

      const isoDateOnly = /^\d{4}-\d{2}-\d{2}$/
      if (isoDateOnly.test(trimmed)) {
        const ts = Date.parse(trimmed)
        if (!isNaN(ts)) {
          return new Intl.DateTimeFormat('fr-FR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
          }).format(new Date(ts))
        }
        return trimmed
      }

      return trimmed === '' ? '-' : trimmed
    }

    return String(value) || '-'
  }

  const viewIntervention = (intervention) => {
    if (intervention && intervention.id) {
      if (route.query.from === 'dashboard') {
        router.push({
          name: 'InterventionDetail',
          params: { id: intervention.id },
          query: { from: route.query.from },
        })
        return
      }

      router.push({
        name: 'InterventionDetail',
        params: { id: intervention.id },
        query: { from: 'equipment', equipmentId: equipement.value.id },
      })
    }
  }

  const signalFailure = () => {
    if (equipement.value.reference) {
      router.push({
        name: 'CreateFailure',
        params: { equipementId: equipement.value.id },
      })
    }
  }

  const openMaintenanceCalendar = () => {
    const equipmentId = equipmentDetails.value?.id
    if (!equipmentId) return

    router.push({
      name: 'Calendar',
      query: {
        from: 'equipment',
        mode: 'maintenance',
        equipmentId: equipmentId,
      },
    })
  }

  const viewCounter = (counter) => {
    router.push({
      name: 'CounterDetail',
      params: { id: counter.id },
      query: { from: 'equipment', equipmentId: equipmentDetails.value.id },
    })
  }

  const openAddCounterDialog = () => {
    currentCounter.value = getEmptyCounter()
    showCounterDialog.value = true
  }

  const closeCounterDialog = () => {
    showCounterDialog.value = false
    currentCounter.value = null
  }

  const saveCounter = async () => {
    try {
      const fd = new FormData()

      const counterData = {
        nom: currentCounter.value.nomCompteur,
        unite: currentCounter.value.unite,
        valeurCourante: currentCounter.value.valeurCourante ?? 0,
        estPrincipal: currentCounter.value.estPrincipal,
        equipement: route.params.id,
        type: currentCounter.value.type,
      }

      fd.append('compteur', JSON.stringify(counterData))

      const counterApi = useApi(API_BASE_URL)
      await counterApi.post('compteurs/', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      successMessage.value = 'Compteur créé avec succès'
      closeCounterDialog()
      await fetchEquipmentData()

      setTimeout(() => (successMessage.value = ''), 3000)
    } catch (error) {
      console.error('Erreur lors de la création du compteur:', error)
      errorMessage.value = 'Erreur lors de la création du compteur'
    }
  }

  const handleDownloadSuccess = (message) => {
    successMessage.value = message
    setTimeout(() => (successMessage.value = ''), 3000)
  }

  const handleDownloadError = (message) => {
    errorMessage.value = message
    setTimeout(() => (errorMessage.value = ''), 3000)
  }

  const handleDeleteSuccess = async () => {
    successMessage.value = 'Document supprimé avec succès'
    await fetchEquipmentData()
    setTimeout(() => (successMessage.value = ''), 3000)
  }

  const handleDeleteError = (message) => {
    errorMessage.value = message
    setTimeout(() => (errorMessage.value = ''), 3000)
  }

  onMounted(() => {
    fetchEquipmentData()
  })

  const editCurrentEquip = () => {
    router.push({
      name: 'EditEquipment',
      params: { id: equipmentDetails.value.id },
      query: { from: 'equipment', equipmentId: equipmentDetails.value.id },
    })
  }
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
