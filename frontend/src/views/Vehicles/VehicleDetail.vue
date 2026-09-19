<template>
  <BaseDetailView :data="vehicleData" :loading="isLoading" :error-message="errorMessage"
    title="Détail du véhicule" :auto-display="false" :show-edit-button="false"
    @clear-error="errorMessage = ''">
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
            <v-chip v-if="data.statut" variant="outlined" size="small" :color="getStatusColor(data.statut.statut)">
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
          <div>{{ data.vehicule_profile?.co2 != null ? `${data.vehicule_profile.co2} g/km` : '-' }}</div>
        </v-col>

        <v-col cols="12" md="4">
          <strong>Puissance fiscale</strong>
          <div>{{ data.vehicule_profile?.puissanceFiscale != null ? `${data.vehicule_profile.puissanceFiscale} CV` : '-' }}</div>
        </v-col>

        <v-col cols="12" md="4">
          <strong>PTAC</strong>
          <div>{{ data.vehicule_profile?.ptac != null ? `${data.vehicule_profile.ptac} kg` : '-' }}</div>
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

const route = useRoute()
const router = useRouter()
const store = useStore()
const api = useApi(API_BASE_URL)

const vehicleId = route.params.id
const vehicleData = ref(null)
const isLoading = ref(true)
const errorMessage = ref('')

const genreLabel = computed(() => GENRE_LABELS[vehicleData.value?.vehicule_profile?.genre] || '-')
const energieLabel = computed(() => ENERGIE_LABELS[vehicleData.value?.vehicule_profile?.energie] || '-')

const loadVehicleData = async () => {
  isLoading.value = true
  try {
    vehicleData.value = await api.get(`vehicules/${vehicleId}/`)
  } catch (error) {
    errorMessage.value = 'Erreur lors du chargement du véhicule.'
  } finally {
    isLoading.value = false
  }
}

const editVehicle = () => {
  router.push({ name: 'EditVehicle', params: { id: vehicleId } })
}

onMounted(loadVehicleData)
</script>

<style scoped>
.floating-edit-button {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 1000;
}
</style>
