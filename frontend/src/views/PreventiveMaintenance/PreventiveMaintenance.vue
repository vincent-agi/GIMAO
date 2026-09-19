<template>
  <v-app>
    <v-main>
      <v-container fluid>
        <div class="d-flex align-center justify-space-between mb-4 flex-wrap" style="gap: 12px">
          <h1 class="text-h5 font-weight-bold">Maintenance préventive</h1>
          <div class="d-flex flex-wrap" style="gap: 8px">
            <v-btn
              color="secondary"
              variant="outlined"
              prepend-icon="mdi-calculator-variant"
              size="small"
              :loading="forcing"
              @click="forcerCalcul"
            >
              <span class="d-none d-sm-inline">Forcer le calcul des BT préventifs</span>
              <span class="d-inline d-sm-none">Forcer le calcul</span>
            </v-btn>
            <v-btn
              color="primary"
              prepend-icon="mdi-plus"
              size="small"
              @click="openCreateDialog(null)"
            >
              <span class="d-none d-sm-inline">Ajouter une maintenance préventive</span>
              <span class="d-inline d-sm-none">Ajouter une MP</span>
            </v-btn>
          </div>
        </div>

        <!-- Barre de recherche -->
        <v-text-field
          v-model="search"
          prepend-inner-icon="mdi-magnify"
          label="Rechercher un équipement..."
          variant="outlined"
          density="comfortable"
          clearable
          class="mb-4"
        />

        <v-progress-linear v-if="loadingData" indeterminate color="primary" class="mb-4" />

        <!-- Liste des équipements -->
        <v-row>
          <v-col
            v-for="equipment in filteredEquipments"
            :key="equipment.id"
            cols="12"
            md="6"
            lg="4"
          >
            <v-card
              variant="flat"
              border="sm"
              class="pa-4 h-100"
              style="border-color: rgba(0, 0, 0, 0.08) !important"
            >
              <!-- En-tête équipement -->
              <div class="d-flex align-center justify-space-between mb-3">
                <div>
                  <div class="text-subtitle-1 font-weight-bold">{{ equipment.designation }}</div>
                  <div class="text-caption text-grey">{{ equipment.reference }}</div>
                </div>
                <v-btn
                  size="small"
                  color="primary"
                  prepend-icon="mdi-plus"
                  variant="tonal"
                  @click="openCreateDialog(equipment)"
                >
                  Ajouter
                </v-btn>
              </div>

              <v-divider class="mb-3" />

              <!-- Plans de maintenance existants -->
              <div
                v-if="plansByEquipment[equipment.id]?.length > 0"
                class="d-flex flex-wrap"
                style="gap: 6px"
              >
                <v-chip
                  v-for="plan in plansByEquipment[equipment.id]"
                  :key="plan.id"
                  size="small"
                  color="primary"
                  variant="tonal"
                  label
                  append-icon="mdi-pencil"
                  style="cursor: pointer"
                  @click="openEditDialog(plan, equipment)"
                >
                  {{ plan.nom }}
                </v-chip>
              </div>
              <div
                v-else-if="!loadingPlans[equipment.id]"
                class="text-caption text-grey text-center py-2"
              >
                Aucun plan de maintenance défini
              </div>
              <v-progress-circular
                v-else
                indeterminate
                size="20"
                color="primary"
                class="d-flex mx-auto my-2"
              />
            </v-card>
          </v-col>
        </v-row>

        <div
          v-if="!loadingData && filteredEquipments.length === 0"
          class="text-center py-12 text-grey"
        >
          <v-icon size="64" class="mb-3">mdi-clipboard-list-outline</v-icon>
          <div class="text-h6">Aucun équipement trouvé</div>
        </div>
      </v-container>
    </v-main>

    <!-- Dialog édition → redirige vers CounterDetail -->
    <v-dialog v-model="showEditDialog" max-width="480">
      <v-card>
        <v-card-title class="text-h6 pa-4 pb-2">Modifier la maintenance préventive</v-card-title>
        <v-divider />
        <v-card-text class="pa-4">
          <p class="mb-4">
            Pour modifier <strong>{{ editPlan?.nom }}</strong
            >,
            <template v-if="editPlan?.compteur_id">
              accédez à la fiche du compteur associé.
            </template>
            <template v-else>
              accédez à la fiche de l'équipement pour gérer les compteurs et les seuils.
            </template>
          </p>
          <v-btn
            block
            color="primary"
            :prepend-icon="editPlan?.compteur_id ? 'mdi-counter' : 'mdi-tools'"
            @click="goToCounterDetail"
          >
            {{ editPlan?.compteur_id ? 'Ouvrir le compteur' : "Ouvrir l'équipement" }}
          </v-btn>
        </v-card-text>
        <v-card-actions class="px-4 pb-4">
          <v-spacer />
          <v-btn variant="text" @click="showEditDialog = false">Fermer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog création -->
    <v-dialog v-model="showDialog" max-width="800" scrollable persistent>
      <v-card>
        <v-card-title class="text-h6 pa-4 pb-2">
          Ajouter une maintenance préventive
          <span v-if="dialogEquipment"> : {{ dialogEquipment.designation }}</span>
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-4">
          <CreatePreventiveMaintenanceForm
            :equipments="equipments"
            :types-p-m="typesPM"
            :consumables="consumables"
            :initial-equipment-id="dialogEquipment?.id ?? null"
            @saved="onSaved"
            @cancel="showDialog = false"
          />
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar" :color="snackbarColor" timeout="4000">
      {{ snackbarMessage }}
    </v-snackbar>
  </v-app>
</template>

<script setup>
  import { ref, computed, onMounted } from 'vue'
  import { useApi } from '@/composables/useApi'
  import { useRouter } from 'vue-router'
  import { API_BASE_URL } from '@/utils/constants'
  import { fetchAllPages } from '@/utils/paginatedApi'
  import CreatePreventiveMaintenanceForm from './CreatePreventiveMaintenanceForm.vue'

  const api = useApi(API_BASE_URL)
  const router = useRouter()

  const equipments = ref([])
  const typesPM = ref([])
  const consumables = ref([])
  const plansByEquipment = ref({})
  const loadingData = ref(false)
  const loadingPlans = ref({})
  const search = ref('')
  const showDialog = ref(false)
  const dialogEquipment = ref(null)
  const showEditDialog = ref(false)
  const editPlan = ref(null)
  const editEquipment = ref(null)
  const snackbar = ref(false)
  const snackbarMessage = ref('')
  const snackbarColor = ref('success')
  const forcing = ref(false)

  const notify = (message, color = 'success') => {
    snackbarMessage.value = message
    snackbarColor.value = color
    snackbar.value = true
  }

  const forcerCalcul = async () => {
    if (forcing.value) return
    forcing.value = true
    try {
      const res = await api.post('plans-maintenance/forcer_calcul/')
      notify(res?.message || 'Calcul des maintenances préventives effectué.', 'success')
      // Rafraîchir les plans affichés
      await fetchData()
    } catch (e) {
      console.error(e)
      notify('Erreur lors du calcul des maintenances préventives.', 'error')
    } finally {
      // Cooldown anti double-clic : on garde le bouton désactivé quelques secondes
      setTimeout(() => {
        forcing.value = false
      }, 4000)
    }
  }

  const filteredEquipments = computed(() => {
    const q = search.value?.toLowerCase().trim()
    if (!q) return equipments.value
    return equipments.value.filter(
      (e) => e.designation?.toLowerCase().includes(q) || e.reference?.toLowerCase().includes(q)
    )
  })

  const openCreateDialog = (equipment) => {
    dialogEquipment.value = equipment
    showDialog.value = true
  }

  const openEditDialog = (plan, equipment) => {
    editPlan.value = plan
    editEquipment.value = equipment
    showEditDialog.value = true
  }

  const goToCounterDetail = () => {
    showEditDialog.value = false
    if (editPlan.value.compteur_id) {
      router.push({
        name: 'CounterDetail',
        params: { id: editPlan.value.compteur_id },
        query: { from: 'preventive', equipmentId: editEquipment.value?.id },
      })
    } else {
      router.push({
        name: 'EquipmentDetail',
        params: { id: editEquipment.value?.id },
      })
    }
  }

  const onSaved = async (equipementId) => {
    showDialog.value = false
    notify('Maintenance préventive enregistrée avec succès.', 'success')
    const id = equipementId || dialogEquipment.value?.id
    if (id) {
      await loadPlansForEquipment(id)
    }
  }

  const loadPlansForEquipment = async (equipmentId) => {
    loadingPlans.value[equipmentId] = true
    try {
      const data = await api.get(`plans-maintenance/par_equipement/?equipement_id=${equipmentId}`)
      plansByEquipment.value[equipmentId] = Array.isArray(data) ? data : (data.results ?? [])
    } catch (e) {
      console.error(e)
      plansByEquipment.value[equipmentId] = []
    } finally {
      loadingPlans.value[equipmentId] = false
    }
  }

  const fetchData = async () => {
    loadingData.value = true
    try {
      // Équipements : endpoint éprouvé utilisé dans tout le projet
      equipments.value = await fetchAllPages(api, 'equipements/')

      // Charger les plans en parallèle (lazy)
      equipments.value.forEach((eq) => loadPlansForEquipment(eq.id))
    } catch (e) {
      console.error('Erreur chargement équipements:', e)
    } finally {
      loadingData.value = false
    }

    // TypesPM et consommables via l'endpoint form-data (même source que useEquipmentForm)
    try {
      const formData = await api.get('equipements/form-data/', { minimal: true })
      typesPM.value = (formData.typesPM || []).filter(
        (t) => t.libelle === 'Préventive conditionnelle' || t.libelle === 'Préventive systématique'
      )
      consumables.value = formData.consumables || []
    } catch (e) {
      console.error('Erreur chargement form-data:', e)
    }
  }

  onMounted(fetchData)
</script>
