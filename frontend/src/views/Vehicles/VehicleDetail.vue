<template>
  <BaseDetailView
    :data="vehicleData"
    :loading="isLoading"
    :error-message="errorMessage"
    title="Détail du véhicule"
    :auto-display="false"
    :show-edit-button="false"
    @clear-error="errorMessage = ''"
  >
    <template #default="{ data }">
      <v-row v-if="data" dense>
        <v-col cols="12">
          <h3 class="text-h6 mb-3">Identification</h3>
        </v-col>

        <v-col cols="12" md="6">
          <strong>Désignation</strong>
          <div>{{ data.designation }}</div>
        </v-col>

        <v-col cols="12" md="6">
          <strong>Référence</strong>
          <div>{{ data.reference || '-' }}</div>
        </v-col>

        <v-col cols="12" md="6">
          <strong>VIN</strong>
          <div>{{ data.vehicule_profile?.vin || '-' }}</div>
        </v-col>

        <v-col cols="12" md="6">
          <strong>Immatriculation</strong>
          <div>{{ data.vehicule_profile?.immatriculation || '-' }}</div>
        </v-col>

        <v-col cols="12" md="6">
          <strong>Statut</strong>
          <div>
            <v-chip
              v-if="data.statut"
              variant="outlined"
              size="small"
              :color="getStatusColor(data.statut.statut)"
            >
              {{ getStatusLabel(data.statut.statut) }}
            </v-chip>
            <span v-else>-</span>
          </div>
        </v-col>

        <v-col cols="12" class="mt-4">
          <h3 class="text-h6 mb-3">Caractéristiques</h3>
        </v-col>

        <v-col cols="12" md="4">
          <strong>Genre</strong>
          <div>{{ genreLabel }}</div>
        </v-col>

        <v-col cols="12" md="4">
          <strong>Énergie</strong>
          <div>{{ energieLabel }}</div>
        </v-col>

        <v-col cols="12" md="4">
          <strong>CO2</strong>
          <div>
            {{ data.vehicule_profile?.co2 != null ? `${data.vehicule_profile.co2} g/km` : '-' }}
          </div>
        </v-col>

        <v-col cols="12" md="4">
          <strong>Puissance fiscale</strong>
          <div>
            {{
              data.vehicule_profile?.puissanceFiscale != null
                ? `${data.vehicule_profile.puissanceFiscale} CV`
                : '-'
            }}
          </div>
        </v-col>

        <v-col cols="12" md="4">
          <strong>PTAC</strong>
          <div>
            {{ data.vehicule_profile?.ptac != null ? `${data.vehicule_profile.ptac} kg` : '-' }}
          </div>
        </v-col>

        <v-col cols="12" class="mt-4">
          <h3 class="text-h6 mb-3">Classification et localisation</h3>
        </v-col>

        <v-col cols="12" md="6">
          <strong>Lieu</strong>
          <div>{{ data.lieu?.nomLieu || '-' }}</div>
        </v-col>

        <v-col cols="12" md="6">
          <strong>Modèle</strong>
          <div>{{ data.modele || '-' }}</div>
        </v-col>

        <!-- Carte grise (US-010) -->
        <v-col cols="12" class="mt-4">
          <div class="d-flex align-center justify-space-between mb-2">
            <h3 class="text-h6 mb-0">Carte grise</h3>
            <v-btn
              v-if="store.getters.hasPermission('veh:edit')"
              size="small"
              variant="outlined"
              @click="showCarteGriseForm = !showCarteGriseForm"
            >
              Ajouter une carte grise
            </v-btn>
          </div>

          <v-form
            v-if="showCarteGriseForm"
            ref="carteGriseFormRef"
            @submit.prevent="submitCarteGrise"
          >
            <v-row dense>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="carteGriseForm.immatriculation"
                  label="Immatriculation"
                  placeholder="AB-123-CD"
                  variant="outlined"
                  density="compact"
                  :rules="[requiredRule]"
                />
              </v-col>
              <v-col cols="12" md="8">
                <v-text-field
                  v-model="carteGriseForm.titulaire"
                  label="Titulaire"
                  variant="outlined"
                  density="compact"
                  :rules="[requiredRule]"
                />
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="carteGriseForm.date_premiere_mise_circulation"
                  label="Date de première mise en circulation"
                  type="date"
                  variant="outlined"
                  density="compact"
                  :rules="[requiredRule]"
                />
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="carteGriseForm.date_emission"
                  label="Date d'émission"
                  type="date"
                  variant="outlined"
                  density="compact"
                  :rules="[requiredRule]"
                />
              </v-col>
            </v-row>
            <v-alert v-if="carteGriseError" type="error" density="compact" class="mb-2">
              {{ carteGriseError }}
            </v-alert>
            <v-btn type="submit" color="primary" size="small" :loading="carteGriseSaving">
              Enregistrer
            </v-btn>
          </v-form>

          <v-table v-if="cartesGrises.length" density="compact" class="mt-2">
            <thead>
              <tr>
                <th>Immatriculation</th>
                <th>Titulaire</th>
                <th>Émission</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="carte in cartesGrises" :key="carte.id">
                <td>{{ carte.immatriculation }}</td>
                <td>{{ carte.titulaire }}</td>
                <td>{{ carte.date_emission }}</td>
              </tr>
            </tbody>
          </v-table>
          <p v-else class="text-caption text-grey">Aucune carte grise enregistrée.</p>
        </v-col>

        <!-- Contrôles techniques (US-011) -->
        <v-col cols="12" class="mt-4">
          <div class="d-flex align-center justify-space-between mb-2">
            <h3 class="text-h6 mb-0">Contrôles techniques</h3>
            <v-btn
              v-if="store.getters.hasPermission('veh:edit')"
              size="small"
              variant="outlined"
              @click="showControleTechniqueForm = !showControleTechniqueForm"
            >
              Ajouter un contrôle technique
            </v-btn>
          </div>

          <v-form
            v-if="showControleTechniqueForm"
            ref="controleTechniqueFormRef"
            @submit.prevent="submitControleTechnique"
          >
            <v-row dense>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="controleTechniqueForm.date_passage"
                  label="Date de passage"
                  type="date"
                  variant="outlined"
                  density="compact"
                  :rules="[requiredRule]"
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-select
                  v-model="controleTechniqueForm.resultat"
                  label="Résultat"
                  :items="RESULTAT_OPTIONS"
                  item-title="title"
                  item-value="value"
                  variant="outlined"
                  density="compact"
                  :rules="[requiredRule]"
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="controleTechniqueForm.date_echeance"
                  :label="
                    controleTechniqueForm.resultat === 'DEFAVORABLE'
                      ? 'Échéance de contre-visite'
                      : 'Échéance du prochain contrôle'
                  "
                  type="date"
                  variant="outlined"
                  density="compact"
                  :rules="[requiredRule]"
                />
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="controleTechniqueForm.centre_controle"
                  label="Centre de contrôle (optionnel)"
                  variant="outlined"
                  density="compact"
                />
              </v-col>
            </v-row>
            <v-alert v-if="controleTechniqueError" type="error" density="compact" class="mb-2">
              {{ controleTechniqueError }}
            </v-alert>
            <v-btn type="submit" color="primary" size="small" :loading="controleTechniqueSaving">
              Enregistrer
            </v-btn>
          </v-form>

          <v-table v-if="controlesTechniques.length" density="compact" class="mt-2">
            <thead>
              <tr>
                <th>Date de passage</th>
                <th>Résultat</th>
                <th>Échéance</th>
                <th>Centre</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="controle in controlesTechniques" :key="controle.id">
                <td>{{ controle.date_passage }}</td>
                <td>
                  <v-chip size="small" variant="outlined" :color="resultatColor(controle.resultat)">
                    {{ resultatLabel(controle.resultat) }}
                  </v-chip>
                </td>
                <td>{{ controle.date_echeance }}</td>
                <td>{{ controle.centre_controle || '-' }}</td>
              </tr>
            </tbody>
          </v-table>
          <p v-else class="text-caption text-grey">Aucun contrôle technique enregistré.</p>
        </v-col>

        <!-- Diagnostic OBD (US-022) -->
        <v-col cols="12" class="mt-4">
          <div class="d-flex align-center justify-space-between mb-2">
            <h3 class="text-h6 mb-0">Diagnostic OBD</h3>
            <v-btn
              v-if="store.getters.hasPermission('obd:create')"
              size="small"
              variant="outlined"
              @click="showCodeDefautForm = !showCodeDefautForm"
            >
              Saisir un code défaut
            </v-btn>
          </div>

          <v-form
            v-if="showCodeDefautForm"
            ref="codeDefautFormRef"
            @submit.prevent="submitCodeDefaut"
          >
            <v-row dense>
              <v-col cols="12" md="3">
                <v-text-field
                  v-model="codeDefautForm.code"
                  label="Code DTC"
                  placeholder="P0301"
                  variant="outlined"
                  density="compact"
                  :rules="[requiredRule]"
                />
              </v-col>
              <v-col cols="12" md="5">
                <v-text-field
                  v-model="codeDefautForm.description"
                  label="Description (optionnel)"
                  variant="outlined"
                  density="compact"
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="codeDefautForm.date_lecture"
                  label="Date de lecture"
                  type="datetime-local"
                  variant="outlined"
                  density="compact"
                  :rules="[requiredRule]"
                />
              </v-col>
            </v-row>
            <v-alert v-if="codeDefautError" type="error" density="compact" class="mb-2">
              {{ codeDefautError }}
            </v-alert>
            <v-btn type="submit" color="primary" size="small" :loading="codeDefautSaving">
              Enregistrer
            </v-btn>
          </v-form>

          <v-table v-if="codesDefautObd.length" density="compact" class="mt-2">
            <thead>
              <tr>
                <th>Code</th>
                <th>Description</th>
                <th>Date de lecture</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="codeDefaut in codesDefautObd" :key="codeDefaut.id">
                <td>{{ codeDefaut.code }}</td>
                <td>{{ codeDefaut.description || '-' }}</td>
                <td>{{ codeDefaut.date_lecture }}</td>
                <td>
                  <v-chip size="small" variant="outlined">
                    {{ codeDefaut.source === 'AUTOMATIQUE' ? 'Automatique' : 'Manuel' }}
                  </v-chip>
                </td>
              </tr>
            </tbody>
          </v-table>
          <p v-else class="text-caption text-grey">Aucun code défaut enregistré.</p>
        </v-col>
      </v-row>

      <v-row v-else>
        <v-col>
          <v-alert type="info" variant="outlined">
            Aucune donnée disponible pour ce véhicule.
          </v-alert>
        </v-col>
      </v-row>
    </template>
  </BaseDetailView>

  <v-btn
    v-if="store.getters.hasPermission('veh:edit')"
    color="primary"
    size="large"
    icon
    class="floating-edit-button"
    elevation="4"
    @click="editVehicle"
  >
    <v-icon size="large">mdi-pencil</v-icon>
    <v-tooltip activator="parent" location="left">Modifier le véhicule</v-tooltip>
  </v-btn>
</template>

<script setup>
  /** Fiche détail d'un véhicule (US-003), lecture seule + accès à l'édition. */
  import { computed, onMounted, ref } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import { useStore } from 'vuex'
  import BaseDetailView from '@/components/common/BaseDetailView.vue'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'
  import { getStatusColor, getStatusLabel } from '@/utils/helpers'

  const GENRE_LABELS = {
    VL: 'Véhicule léger',
    PL: 'Poids lourd',
    UTILITAIRE: 'Utilitaire',
    REMORQUE: 'Remorque',
  }

  const ENERGIE_LABELS = {
    ESSENCE: 'Essence',
    DIESEL: 'Diesel',
    ELECTRIQUE: 'Électrique',
    HYBRIDE: 'Hybride',
    GPL: 'GPL',
    AUTRE: 'Autre',
  }

  const RESULTAT_OPTIONS = [
    { value: 'FAVORABLE', title: 'Favorable' },
    { value: 'DEFAVORABLE', title: 'Défavorable' },
    { value: 'CONTRE_VISITE', title: 'Contre-visite' },
  ]

  const RESULTAT_LABELS = {
    FAVORABLE: 'Favorable',
    DEFAVORABLE: 'Défavorable',
    CONTRE_VISITE: 'Contre-visite',
  }

  const RESULTAT_COLORS = {
    FAVORABLE: 'success',
    DEFAVORABLE: 'error',
    CONTRE_VISITE: 'warning',
  }

  const route = useRoute()
  const router = useRouter()
  const store = useStore()
  const api = useApi(API_BASE_URL)

  const vehicleId = route.params.id
  const vehicleData = ref(null)
  const isLoading = ref(true)
  const errorMessage = ref('')

  const requiredRule = (value) => !!value || 'Champ requis'
  const resultatLabel = (resultat) => RESULTAT_LABELS[resultat] || resultat
  const resultatColor = (resultat) => RESULTAT_COLORS[resultat] || 'grey'

  const genreLabel = computed(() => GENRE_LABELS[vehicleData.value?.vehicule_profile?.genre] || '-')
  const energieLabel = computed(
    () => ENERGIE_LABELS[vehicleData.value?.vehicule_profile?.energie] || '-'
  )

  // Carte grise (US-010)
  const cartesGrises = ref([])
  const showCarteGriseForm = ref(false)
  const carteGriseFormRef = ref(null)
  const carteGriseSaving = ref(false)
  const carteGriseError = ref('')
  const carteGriseForm = ref({
    immatriculation: '',
    titulaire: '',
    date_premiere_mise_circulation: '',
    date_emission: '',
  })

  const loadCartesGrises = async () => {
    try {
      cartesGrises.value = await api.get('cartes-grises/', { vehicule_profile: vehicleId })
    } catch {
      // Historique non bloquant pour l'affichage de la fiche véhicule.
      cartesGrises.value = []
    }
  }

  const submitCarteGrise = async () => {
    const { valid } = await carteGriseFormRef.value.validate()
    if (!valid) return

    carteGriseSaving.value = true
    carteGriseError.value = ''
    try {
      await api.post('cartes-grises/', { ...carteGriseForm.value, vehicule_profile: vehicleId })
      showCarteGriseForm.value = false
      carteGriseForm.value = {
        immatriculation: '',
        titulaire: '',
        date_premiere_mise_circulation: '',
        date_emission: '',
      }
      await loadCartesGrises()
    } catch {
      carteGriseError.value = "Erreur lors de l'enregistrement de la carte grise."
    } finally {
      carteGriseSaving.value = false
    }
  }

  // Contrôles techniques (US-011)
  const controlesTechniques = ref([])
  const showControleTechniqueForm = ref(false)
  const controleTechniqueFormRef = ref(null)
  const controleTechniqueSaving = ref(false)
  const controleTechniqueError = ref('')
  const controleTechniqueForm = ref({
    date_passage: '',
    date_echeance: '',
    resultat: null,
    centre_controle: '',
  })

  const loadControlesTechniques = async () => {
    try {
      controlesTechniques.value = await api.get('controles-techniques/', {
        vehicule_profile: vehicleId,
      })
    } catch {
      controlesTechniques.value = []
    }
  }

  const submitControleTechnique = async () => {
    const { valid } = await controleTechniqueFormRef.value.validate()
    if (!valid) return

    controleTechniqueSaving.value = true
    controleTechniqueError.value = ''
    try {
      await api.post('controles-techniques/', {
        ...controleTechniqueForm.value,
        vehicule_profile: vehicleId,
      })
      showControleTechniqueForm.value = false
      controleTechniqueForm.value = {
        date_passage: '',
        date_echeance: '',
        resultat: null,
        centre_controle: '',
      }
      await loadControlesTechniques()
    } catch {
      controleTechniqueError.value = "Erreur lors de l'enregistrement du contrôle technique."
    } finally {
      controleTechniqueSaving.value = false
    }
  }

  // Diagnostic OBD (US-022)
  const codesDefautObd = ref([])
  const showCodeDefautForm = ref(false)
  const codeDefautFormRef = ref(null)
  const codeDefautSaving = ref(false)
  const codeDefautError = ref('')
  const codeDefautForm = ref({
    code: '',
    description: '',
    date_lecture: '',
  })

  const loadCodesDefautObd = async () => {
    try {
      codesDefautObd.value = await api.get('codes-defaut-obd/', { vehicule_profile: vehicleId })
    } catch {
      codesDefautObd.value = []
    }
  }

  const submitCodeDefaut = async () => {
    const { valid } = await codeDefautFormRef.value.validate()
    if (!valid) return

    codeDefautSaving.value = true
    codeDefautError.value = ''
    try {
      await api.post('codes-defaut-obd/', {
        ...codeDefautForm.value,
        vehicule_profile: vehicleId,
        source: 'MANUEL',
      })
      showCodeDefautForm.value = false
      codeDefautForm.value = { code: '', description: '', date_lecture: '' }
      await loadCodesDefautObd()
    } catch {
      codeDefautError.value = "Erreur lors de l'enregistrement du code défaut."
    } finally {
      codeDefautSaving.value = false
    }
  }

  const loadVehicleData = async () => {
    isLoading.value = true
    try {
      vehicleData.value = await api.get(`vehicules/${vehicleId}/`)
    } catch {
      errorMessage.value = 'Erreur lors du chargement du véhicule.'
    } finally {
      isLoading.value = false
    }
  }

  const editVehicle = () => {
    router.push({ name: 'EditVehicle', params: { id: vehicleId } })
  }

  onMounted(async () => {
    await Promise.allSettled([
      loadVehicleData(),
      loadCartesGrises(),
      loadControlesTechniques(),
      loadCodesDefautObd(),
    ])
  })
</script>

<style scoped>
  .floating-edit-button {
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 1000;
  }
</style>
