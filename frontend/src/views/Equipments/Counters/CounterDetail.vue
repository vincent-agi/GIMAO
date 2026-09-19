<template>
  <v-card>
    <!-- Titre -->
    <v-card-title class="d-flex align-center">
      <v-icon left>mdi-counter</v-icon>
      <span>Détails du compteur</span>
    </v-card-title>

    <v-card-text v-if="!loading && counter">
      <!-- Informations générales du compteur -->
      <v-sheet class="pa-4 mb-4" elevation="2" rounded>
        <h3 class="mb-3 text-blue-darken-3">Informations du compteur</h3>

        <v-row dense>
          <v-col cols="12" md="4">
            <strong>Nom :</strong>
            <div class="text-h6">{{ counter.nomCompteur }}</div>
          </v-col>

          <v-col cols="12" md="4">
            <strong>Valeur actuelle :</strong>
            <div class="text-h6">
              {{
                counter.type === 'Calendaire'
                  ? formatCalendarDate(counter.valeurCourante)
                  : counter.valeurCourante
              }}
            </div>
          </v-col>
          <v-col v-if="counter.type !== 'Calendaire'" cols="12" md="4">
            <strong>Unité :</strong>
            <div class="text-h6">{{ counter.unite }}</div>
          </v-col>
        </v-row>

        <v-row dense class="mt-2">
          <v-col cols="12" md="4">
            <strong>Statut :</strong>
            <v-chip
              :color="counter.estPrincipal ? 'primary' : 'grey'"
              label
              class="ml-2"
              size="small"
            >
              {{ counter.estPrincipal ? 'Principal' : 'Secondaire' }}
            </v-chip>
          </v-col>

          <v-col cols="12" md="4">
            <strong>Équipement :</strong>
            <div>{{ counter.equipement_info?.designation || '—' }}</div>
          </v-col>

          <v-col cols="12" md="4">
            <strong>Lieu :</strong>
            <div>{{ counter.equipement_info?.lieu?.nomLieu || '—' }}</div>
          </v-col>
        </v-row>
      </v-sheet>

      <!-- Liste des seuils avec plans de maintenance -->
      <div v-if="counter.seuils && counter.seuils.length > 0">
        <h3 class="mb-3">Maintenances préventives associées</h3>

        <v-expansion-panels v-model="openedPanels" multiple>
          <v-expansion-panel v-for="(seuil, index) in counter.seuils" :key="seuil.id">
            <v-expansion-panel-title expand-icon="mdi-menu-down">
              <template #default>
                <v-row no-gutters align="center">
                  <v-col cols="4" class="text-left">
                    <div class="d-flex align-center">
                      <v-icon left>mdi-calendar-clock</v-icon>
                      <strong class="ml-2"
                        >{{ counter.type === 'Calendaire' ? 'Périodicité' : 'Seuil' }}
                        {{ index + 1 }}</strong
                      >
                    </div>
                  </v-col>
                  <v-col cols="6" class="text-left">
                    <div v-if="seuil.planMaintenance" class="text-truncate">
                      {{ seuil.planMaintenance.nom }}
                    </div>
                    <div v-else class="text-grey">Aucun plan de maintenance associé</div>
                  </v-col>
                  <v-col cols="2" class="text-right">
                    <v-chip :color="getProgressionColor(seuil)" size="small" label>
                      {{ getProgressionText(seuil) }}
                    </v-chip>
                  </v-col>
                </v-row>
              </template>
            </v-expansion-panel-title>

            <v-expansion-panel-text>
              <!-- Détails du seuil -->
              <v-sheet class="pa-3 mb-3" elevation="1" rounded>
                <h4 class="mb-2">Détails du seuil</h4>
                <v-row dense>
                  <v-col cols="12" md="3">
                    <strong>Dernière intervention :</strong>
                    <div>{{ formatLastIntervention(seuil.derniereIntervention) }}</div>
                  </v-col>
                  <v-col cols="12" md="3">
                    <strong>Prochaine maintenance :</strong>
                    <div>{{ formatNextMaintenance(seuil.prochaineMaintenance) }}</div>
                  </v-col>
                  <v-col cols="12" md="3">
                    <strong>Intervalle :</strong>
                    <div>{{ formatIntervalle(seuil.ecartInterventions) }}</div>
                  </v-col>
                  <v-col cols="12" md="3">
                    <strong class="mr-2">Type de seuil :</strong>
                    <v-chip :color="seuil.estGlissant ? 'green' : 'orange'" size="small" label>
                      {{ seuil.estGlissant ? 'Glissant' : 'Fixe' }}
                    </v-chip>
                  </v-col>
                  <v-col v-if="seuil.anticipationJours" cols="12" md="3">
                    <strong>Déclenchement effectif :</strong>
                    <div>
                      {{
                        formatNextMaintenance(seuil.prochaineMaintenance - seuil.anticipationJours)
                      }}
                    </div>
                    <div class="text-caption text-grey">
                      {{ seuil.anticipationJours }} jours avant l'échéance
                    </div>
                  </v-col>
                </v-row>
              </v-sheet>

              <!-- Plan de maintenance -->
              <div v-if="seuil.planMaintenance">
                <v-sheet class="pa-3 mb-3" elevation="1" rounded>
                  <h4 class="mb-2">Opération de maintenance</h4>

                  <!-- Informations du PM -->
                  <v-row dense class="mb-3">
                    <v-col cols="12" md="6">
                      <strong>Nom :</strong>
                      <div>{{ seuil.planMaintenance.nom }}</div>
                    </v-col>
                    <v-col cols="12" md="6">
                      <strong>Type :</strong>
                      <div>{{ seuil.planMaintenance.type }}</div>
                    </v-col>
                  </v-row>

                  <v-row dense class="mb-3">
                    <v-col cols="12">
                      <strong>Commentaire :</strong>
                      <div>
                        {{ seuil.planMaintenance.commentaire || 'Aucun commentaire' }}
                      </div>
                    </v-col>
                  </v-row>

                  <v-row
                    v-if="
                      seuil.planMaintenance.necessiteHabilitationElectrique ||
                      seuil.planMaintenance.necessitePermisFeu
                    "
                    dense
                    class="mb-3"
                  >
                    <v-col cols="12">
                      <strong>Requis :</strong>
                      <div class="d-flex gap-3 mt-1">
                        <v-chip
                          v-if="seuil.planMaintenance.necessiteHabilitationElectrique"
                          color="orange"
                          size="small"
                          label
                        >
                          <v-icon left small>mdi-flash</v-icon>
                          Habilitation électrique
                        </v-chip>
                        <v-chip
                          v-if="seuil.planMaintenance.necessitePermisFeu"
                          color="red"
                          size="small"
                          label
                        >
                          <v-icon left small>mdi-fire</v-icon>
                          Permis feu
                        </v-chip>
                      </div>
                    </v-col>
                  </v-row>

                  <!-- Consommables -->
                  <v-sheet class="pa-3 mb-3" elevation="0" rounded border>
                    <h5 class="mb-2">Consommables nécessaires</h5>

                    <div v-if="!seuil.planMaintenance.consommables?.length" class="text-grey">
                      Aucun consommable requis
                    </div>

                    <v-row
                      v-for="consommable in seuil.planMaintenance.consommables"
                      :key="consommable.id"
                      dense
                      class="mb-1"
                    >
                      <v-col cols="8">
                        <v-icon left small>mdi-package-variant</v-icon>
                        {{ consommable.designation }}
                      </v-col>
                      <v-col cols="4">
                        Quantité :
                        {{ consommable.quantite_necessaire || consommable.quantite }}
                      </v-col>
                    </v-row>
                  </v-sheet>

                  <!-- Documents -->
                  <v-sheet class="pa-3" elevation="0" rounded border>
                    <h5 class="mb-2">Documents associés</h5>

                    <div v-if="!seuil.planMaintenance.documents?.length" class="text-grey">
                      Aucun document
                    </div>

                    <v-row
                      v-for="doc in seuil.planMaintenance.documents"
                      :key="doc.id"
                      dense
                      class="mb-2 align-center"
                    >
                      <v-col cols="3">
                        <strong>{{ doc.nom || doc.titre || 'Sans titre' }}</strong>
                      </v-col>
                      <v-col cols="5">
                        <v-icon left small>mdi-file</v-icon>
                        {{ getFileName(doc.chemin || doc.path) || '—' }}
                      </v-col>
                      <v-col cols="3">
                        <v-chip size="small" label>
                          {{ doc.type }}
                        </v-chip>
                      </v-col>
                      <v-col cols="1" class="text-right">
                        <v-btn
                          :href="BASE_URL + MEDIA_BASE_URL + doc.chemin"
                          target="_blank"
                          icon
                          small
                        >
                          <v-icon>mdi-open-in-new</v-icon>
                        </v-btn>
                      </v-col>
                    </v-row>
                  </v-sheet>
                </v-sheet>
              </div>

              <div v-else class="pa-4 text-center text-grey">
                <v-icon large class="mb-2">mdi-alert-circle-outline</v-icon>
                <div>Aucun plan de maintenance associé à ce seuil</div>
              </div>

              <!-- Boutons d'action pour ce seuil -->
              <div class="d-flex justify-end mt-3">
                <v-btn
                  v-if="store.getters.hasPermission('mp:edit')"
                  color="primary"
                  size="small"
                  @click="editSeuil(seuil)"
                >
                  <v-icon left small>mdi-pencil</v-icon>
                  Modifier ce seuil
                </v-btn>
              </div>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </div>

      <!-- Message si aucun seuil -->
      <div v-else class="pa-4 text-center text-grey">
        <v-icon large class="mb-2">mdi-information-outline</v-icon>
        <div>Aucun seuil défini pour ce compteur</div>
      </div>
    </v-card-text>

    <!-- Chargement -->
    <v-card-text v-if="loading" class="text-center">
      <v-progress-circular indeterminate></v-progress-circular>
      <div class="mt-2">Chargement des données...</div>
    </v-card-text>

    <!-- Erreur -->
    <v-card-text v-if="errorMessage" class="text-center text-red">
      <v-icon color="red">mdi-alert-circle</v-icon>
      {{ errorMessage }}
    </v-card-text>

    <!-- Actions -->
    <v-card-actions>
      <v-btn color="grey" @click="router.back()">
        <v-icon left>mdi-arrow-left</v-icon>
        Retour
      </v-btn>
      <v-spacer />
      <v-btn
        v-if="store.getters.hasPermission('cp:edit')"
        color="primary"
        @click="showEditCounterDialog(true)"
      >
        <v-icon left>mdi-pencil</v-icon>
        Modifier le compteur
      </v-btn>
      <v-btn v-if="store.getters.hasPermission('mp:create')" color="success" @click="addNewSeuil">
        <v-icon left>mdi-plus</v-icon>
        Ajouter un seuil
      </v-btn>
    </v-card-actions>
  </v-card>

  <v-dialog v-model="showCounterDialog" max-width="1000px">
    <v-card>
      <v-card-title>Modifier le compteur</v-card-title>
      <v-divider></v-divider>
      <v-card-text>
        <CounterInlineForm
          v-if="counter"
          :model-value="counter"
          :is-edit-mode="true"
          @save="saveCounter"
          @cancel="closeCounterDialog"
        />
      </v-card-text>
    </v-card>
  </v-dialog>

  <v-dialog v-model="showSeuilDialog" max-width="1200px" scrollable>
    <v-card v-if="currentSeuil">
      <v-card-title class="text-h5 pa-4">
        {{ currentSeuil.id ? 'Modifier le seuil' : 'Ajouter un nouveau seuil' }}
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text class="pa-4">
        <MaintenancePlanInlineForm
          v-model="currentPlan"
          :counters="countersForSelect"
          :types-p-m="pmTypes"
          :consumables="consumables"
          :existing-p-ms="existingPMs"
          :types-documents="typesDocuments"
          :show-pm-selection="true"
          :is-edit-mode="!!currentSeuil.id"
          :show-actions="true"
          @cancel="closeSeuilDialog"
          @save="handleFormSave"
        />
      </v-card-text>
      <v-divider></v-divider>
    </v-card>
  </v-dialog>
</template>

<script setup>
  import { ref, onMounted, computed } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import { useStore } from 'vuex'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL, MEDIA_BASE_URL, BASE_URL } from '@/utils/constants'
  import { formatCalendarDate } from '@/utils/helpers'
  import CounterInlineForm from '@/components/Forms/CounterInlineForm.vue'
  import MaintenancePlanInlineForm from '@/components/Forms/MaintenancePlanInlineForm.vue'
  import { fetchAllPages } from '@/utils/paginatedApi'

  const route = useRoute()
  const router = useRouter()
  const store = useStore()
  const counterId = Number(route.params.id)

  const counter = ref(null)
  const originalCounter = ref(null)
  const openedPanels = ref([]) // Premier panel ouvert par défaut
  const currentSeuil = ref(null)
  const currentPlan = ref(null)

  const consumables = ref([])
  const typesPM = ref([])
  const typesDocuments = ref([])
  const existingPMs = ref([])

  const loading = ref(true)
  const saving = ref(false)
  const errorMessage = ref('')
  const successMessage = ref('')

  const showCounterDialog = ref(false)
  const showSeuilDialog = ref(false)

  const initialPlanSnapshot = ref(null)
  const initialSeuilSnapshot = ref(null)

  const isCounterEdit = ref(true)
  const isEditSeuil = ref(false)

  const api = useApi(API_BASE_URL)

  // Computed properties
  const countersForSelect = computed(() => {
    if (!counter.value) return []

    return [
      {
        id: counterId,
        nomCompteur: counter.value.nomCompteur || 'Compteur actuel',
        unite: counter.value.unite || 'heures',
        valeurCourante: counter.value.valeurCourante || 0,
        estPrincipal: counter.value.estPrincipal || false,
        type: counter.value.type || (counter.value.unite === 'date' ? 'Calendaire' : 'Numérique'),
      },
    ]
  })

  const pmTypes = computed(() =>
    typesPM.value
      .filter(
        (item) =>
          item.libelle === 'Préventive conditionnelle' || item.libelle === 'Préventive systématique'
      )
      .map((item) => ({ id: item.id, libelle: item.libelle }))
  )

  const progressionData = computed(() => {
    if (!counter.value || !counter.value.seuils) return {}

    const data = {}
    const actuelle = Number(counter.value.valeurCourante)

    counter.value.seuils.forEach((seuil) => {
      const prochaine = Number(seuil.prochaineMaintenance)
      const derniere = Number(seuil.derniereIntervention)
      const anticipation = seuil.anticipationJours ? Number(seuil.anticipationJours) : 0

      if (isNaN(prochaine) || isNaN(actuelle) || isNaN(derniere)) return

      // Avec anticipation : le déclenchement effectif est (prochaine - anticipation) jours
      // Le 100% est atteint à cette date effective, pas à prochaineMaintenance
      const declenchementEffectif = prochaine - anticipation

      if (declenchementEffectif === derniere) {
        data[seuil.id] = actuelle >= declenchementEffectif ? 100 : 0
        return
      }
      const progression = ((actuelle - derniere) / (declenchementEffectif - derniere)) * 100
      data[seuil.id] = Math.min(Math.max(progression, 0), 100)
    })
    return data
  })

  const getProgressionColor = (seuil) => {
    const progression = progressionData.value[seuil.id]
    if (progression == null || isNaN(progression)) return 'grey'

    if (progression >= 100) return 'red'
    if (progression >= 80) return 'orange'
    if (progression >= 50) return 'blue'
    return 'green'
  }

  const getProgressionText = (seuil) => {
    const progression = progressionData.value[seuil.id]
    if (progression == null || isNaN(progression)) return 'N/A'

    if (progression >= 100) return 'Dépassé'
    return `${Math.round(progression)}%`
  }

  // Méthodes utilitaires
  const getFileName = (path) => path?.split('/').pop() || '—'

  const formatLastIntervention = (days) => {
    if (days === null || days === undefined) return '—'

    if (counter.value.type === 'Calendaire') {
      console.log('Formatage date calendaire pour', days)
      return formatCalendarDate(days)
    } else {
      return `${days} ${counter.value.unite}`
    }
  }

  const formatNextMaintenance = (days) => {
    if (days === null || days === undefined) return '—'

    if (counter.value.type === 'Calendaire') {
      return formatCalendarDate(days)
    } else {
      return `${days} ${counter.value.unite}`
    }
  }

  const formatIntervalle = (intervalle) => {
    if (intervalle === null || intervalle === undefined) return '—'

    if (counter.value.type === 'Calendaire') {
      const days = Math.round(intervalle / 1000 / 24 / 60 / 60) - 1 // convertir ms en jours
      if (days === 0) return '0 jour'

      const years = Math.floor(days / 365)
      const remainingAfterYears = days % 365

      const months = Math.floor(remainingAfterYears / 30)
      const remDays = remainingAfterYears % 30

      const parts = []
      if (years) parts.push(`${years} ${years > 1 ? 'ans' : 'an'}`)
      if (months) parts.push(`${months} mois`)
      if (remDays) parts.push(`${remDays} ${remDays > 1 ? 'jours' : 'jour'}`)

      return parts.join(' ')
    } else {
      console.log('Compteur non calendaire - formatIntervalle')
    }

    return `${intervalle} ${counter.value.unite}`
  }

  // Méthodes de chargement
  const fetchCounter = async () => {
    counter.value = await api.get(`compteurs/${counterId}`)
    originalCounter.value = JSON.parse(JSON.stringify(counter.value))
  }

  const fetchReferentials = async () => {
    const [cons, pmTypes, docTypes, pms] = await Promise.all([
      fetchAllPages(api, 'consommables/'),
      api.get('types-plan-maintenance/'),
      api.get('types-documents/'),
      api.get(
        'plans-maintenance/par_equipement/?equipement_id=' + counter.value.equipement_info?.id
      ),
    ])

    consumables.value = cons
    typesPM.value = pmTypes
    typesDocuments.value = docTypes
    existingPMs.value = pms
  }

  const loadPage = async () => {
    loading.value = true
    errorMessage.value = ''

    try {
      if (!counterId) {
        throw new Error('Identifiant compteur invalide')
      }

      await fetchCounter()
      await fetchReferentials()
    } catch (e) {
      console.error(e)
      errorMessage.value = e.message || 'Erreur lors du chargement'
    } finally {
      loading.value = false
    }
  }

  // Méthodes pour les actions
  const showEditCounterDialog = (isEdit) => {
    isCounterEdit.value = isEdit
    showCounterDialog.value = true
  }

  const closeCounterDialog = () => {
    showCounterDialog.value = false
  }

  const addNewSeuil = () => {
    currentSeuil.value = {
      id: null,
      derniereIntervention: null,
      prochaineMaintenance: null,
      ecartInterventions: 0,
      estGlissant: false,
      planMaintenance: null,
    }

    currentPlan.value = {
      id: null,
      nom: '',
      type_id: null,
      description: '',
      compteurIndex: 0,
      consommables: [],
      documents: [],
      seuil: {
        derniereIntervention: null,
        ecartInterventions: 0,
        prochaineMaintenance: null,
        estGlissant: false,
      },
      necessiteHabilitationElectrique: false,
      necessitePermisFeu: false,
    }

    showSeuilDialog.value = true
  }

  const editSeuil = (seuil) => {
    currentSeuil.value = { ...seuil }

    const pm = seuil.planMaintenance
    currentPlan.value = {
      id: pm?.id || null,
      nom: pm?.nom || '',
      type_id: pm?.type_id || null,
      description: pm?.commentaire || '',
      compteurIndex: 0,
      consommables:
        pm?.consommables?.map((c) => ({
          consommable_id: c.consommable_id || c.id,
          quantite_necessaire: c.quantite || 1,
        })) || [],
      documents:
        pm?.documents?.map((d) => ({
          nom: d.nomDocument || d.nom,
          type_id: d.typeDocument?.id || d.type_id,
          file: null,
        })) || [],
      seuil: {
        derniereIntervention: seuil.derniereIntervention || 0,
        ecartInterventions: seuil.ecartInterventions || 0,
        prochaineMaintenance: seuil.prochaineMaintenance || 0,
        estGlissant: seuil.estGlissant || false,
      },
      necessiteHabilitationElectrique: pm?.necessiteHabilitationElectrique || false,
      necessitePermisFeu: pm?.necessitePermisFeu || false,
    }

    initialSeuilSnapshot.value = JSON.parse(JSON.stringify(currentPlan.value.seuil))
    initialPlanSnapshot.value = JSON.parse(
      JSON.stringify({
        nom: currentPlan.value.nom,
        type_id: currentPlan.value.type_id,
        description: currentPlan.value.description,
        necessiteHabilitationElectrique: currentPlan.value.necessiteHabilitationElectrique,
        necessitePermisFeu: currentPlan.value.necessitePermisFeu,
        consommables: currentPlan.value.consommables,
        documents: currentPlan.value.documents,
      })
    )

    isEditSeuil.value = true

    showSeuilDialog.value = true
  }

  const closeSeuilDialog = () => {
    currentSeuil.value = null
    currentPlan.value = null
    showSeuilDialog.value = false
    isEditSeuil.value = false
  }

  const saveCounter = async (updatedCounter) => {
    if (!updatedCounter) {
      successMessage.value = 'Aucune modification détectée.'
      return
    }

    // Mode édition
    const changes = detectCounterChanges(updatedCounter)

    console.log('Modifications détectées du compteur :', changes)

    // Ajouter l'ID utilisateur
    if (Object.keys(changes).length > 0) {
      changes.user = store.getters.currentUser?.id

      await api.put(`compteurs/${counterId}/`, changes)
      await fetchCounter()
      // Mettre à jour l'original pour que les prochains diffs soient corrects
      originalCounter.value = JSON.parse(JSON.stringify(counter.value))
      successMessage.value = 'Compteur mis à jour avec succès.'
    } else {
      successMessage.value = 'Aucune modification détectée.'
    }
  }

  const detectCounterChanges = (updatedCounter) => {
    const changes = {}

    if (originalCounter.value.nomCompteur !== updatedCounter.nomCompteur) {
      changes.nomCompteur = {
        ancien: originalCounter.value.nomCompteur,
        nouveau: updatedCounter.nomCompteur,
      }
    }
    if (originalCounter.value.valeurCourante !== updatedCounter.valeurCourante) {
      changes.valeurCourante = {
        ancien: originalCounter.value.valeurCourante,
        nouveau: updatedCounter.valeurCourante,
      }
    }
    if (
      originalCounter.value.unite !== updatedCounter.unite &&
      updatedCounter.type !== 'Calendaire'
    ) {
      changes.unite = {
        ancien: originalCounter.value.unite,
        nouveau: updatedCounter.unite,
      }
    }
    if (originalCounter.value.estPrincipal !== updatedCounter.estPrincipal) {
      changes.estPrincipal = {
        ancien: originalCounter.value.estPrincipal,
        nouveau: updatedCounter.estPrincipal,
      }
    }
    if (originalCounter.value.type !== updatedCounter.type) {
      changes.type = {
        ancien: originalCounter.value.type,
        nouveau: updatedCounter.type,
      }
    }

    return changes
  }

  const handleFormSave = (data) => {
    currentPlan.value.pmMode = data.pmMode

    // Si un PM existant est sélectionné
    if (data.pmMode === 'existing' && data.selectedExistingPMId) {
      currentPlan.value.id = data.selectedExistingPMId
      console.log('PM existant sélectionné, ID:', data.selectedExistingPMId)
    }

    saveSeuil()
  }

  const diffObjects = (oldObj, newObj) => {
    const diff = {}

    Object.keys(newObj).forEach((key) => {
      const oldVal = oldObj?.[key]
      const newVal = newObj[key]

      // comparaison simple
      if (JSON.stringify(oldVal) !== JSON.stringify(newVal)) {
        diff[key] = {
          ancien: oldVal ?? null,
          nouveau: newVal ?? null,
        }
      }
    })

    return diff
  }

  const saveSeuil = async () => {
    try {
      saving.value = true
      const formData = new FormData()

      if (isEditSeuil.value) {
        const seuilDiff = diffObjects(initialSeuilSnapshot.value, currentPlan.value.seuil)

        const planDiff = diffObjects(initialPlanSnapshot.value, {
          id: currentPlan.value.id,
          nom: currentPlan.value.nom,
          type_id: currentPlan.value.type_id,
          description: currentPlan.value.description,
          necessiteHabilitationElectrique: currentPlan.value.necessiteHabilitationElectrique,
          necessitePermisFeu: currentPlan.value.necessitePermisFeu,
          consommables: currentPlan.value.consommables,
          documents: currentPlan.value.documents,
        })

        formData.append('seuil_diff', JSON.stringify(seuilDiff))
        formData.append('planMaintenance_diff', JSON.stringify(planDiff))
        formData.append('seuil_id', currentSeuil.value.id)

        /* fichiers uniquement si modifiés */
        const docsAvecFichier = currentPlan.value.documents.filter((d) => d.file instanceof File)
        console.log('Changements détectés pour le seuil :', seuilDiff)

        docsAvecFichier.forEach((doc, index) => {
          formData.append(`document_${index}`, doc.file)
        })

        await api.patch(`declenchements/${currentSeuil.value.id}/`, formData)
      } else {
        /* ===== SEUIL ===== */
        formData.append(
          'seuil',
          JSON.stringify({
            derniereIntervention: currentPlan.value.seuil.derniereIntervention ?? 0,
            ecartInterventions: currentPlan.value.seuil.ecartInterventions ?? 0,
            prochaineMaintenance: currentPlan.value.seuil.prochaineMaintenance ?? null,
            estGlissant: !!currentPlan.value.seuil.estGlissant,
          })
        )

        console.log('Saving new seuil for counter', counterId)
        console.log('Seuil data:', {
          derniereIntervention: currentPlan.value.seuil.derniereIntervention ?? 0,
          ecartInterventions: currentPlan.value.seuil.ecartInterventions ?? 0,
          prochaineMaintenance: currentPlan.value.seuil.prochaineMaintenance ?? null,
          estGlissant: !!currentPlan.value.seuil.estGlissant,
        })

        /* ===== COMPTEUR ===== */
        formData.append('compteur', counterId)

        /* ===== PLAN DE MAINTENANCE ===== */
        const docsAvecFichier = (currentPlan.value.documents || []).filter(
          (d) => d.file instanceof File
        )

        const planMaintenance = {
          id: currentPlan.value.id,
          nom: currentPlan.value.nom,
          type_id: currentPlan.value.type_id,
          commentaire: currentPlan.value.description,
          necessiteHabilitationElectrique: !!currentPlan.value.necessiteHabilitationElectrique,
          necessitePermisFeu: !!currentPlan.value.necessitePermisFeu,

          consommables: (currentPlan.value.consommables || []).map((c) => ({
            consommable_id: c.consommable_id,
            quantite_necessaire: c.quantite_necessaire ?? 1,
          })),

          documents: docsAvecFichier.map((doc) => ({
            titre: doc.nom,
            type: doc.type_id,
          })),
        }

        formData.append('planMaintenance', JSON.stringify(planMaintenance))

        /* ===== FILES ===== */
        docsAvecFichier.forEach((doc, index) => {
          formData.append(`document_${index}`, doc.file)
        })

        /* ===== API ===== */
        await api.post('declenchements/', formData)
      }

      await fetchCounter()
      closeSeuilDialog()
    } catch (e) {
      console.error(e)
      errorMessage.value = 'Erreur lors de la sauvegarde du seuil'
    } finally {
      saving.value = false
    }
  }

  onMounted(() => {
    loadPage()
  })
</script>

<style scoped>
  .gap-3 {
    gap: 12px;
  }

  .text-truncate {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
</style>
