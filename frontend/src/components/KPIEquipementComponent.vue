<template>
  <v-card elevation="2" class="mb-4">
    <v-card-title class="text-h6">
      <v-icon class="mr-2">mdi-chart-bar</v-icon>
      Indicateurs de maintenance corrective
    </v-card-title>
    <v-divider></v-divider>

    <v-card-text>
      <!-- Chargement -->
      <v-row v-if="loading" justify="center" class="py-4">
        <v-progress-circular indeterminate color="primary" />
      </v-row>

      <!-- Erreur -->
      <v-alert v-else-if="erreur" type="error" variant="tonal" class="mb-0">
        Impossible de charger les indicateurs.
      </v-alert>

      <!-- KPI -->
      <v-row v-else>
        <!-- Nombre de pannes -->
        <v-col cols="12" md="4">
          <v-card variant="tonal" color="error" class="text-center pa-4">
            <v-icon size="32" class="mb-2">mdi-alert-circle-outline</v-icon>
            <div class="text-h4 font-weight-bold">{{ kpi.nombre_pannes }}</div>
            <div class="text-caption mt-1">Nombre de pannes</div>
          </v-card>
        </v-col>

        <!-- MTBF -->
        <v-col cols="12" md="4">
          <v-card variant="tonal" color="warning" class="text-center pa-4">
            <v-icon size="32" class="mb-2">mdi-timer-sand</v-icon>
            <div class="text-h4 font-weight-bold">
              {{ kpi.mtbf_heures !== null ? kpi.mtbf_heures : '—' }}
            </div>
            <div class="text-caption mt-1">
              MTBF (heures)
              <v-tooltip activator="parent" location="bottom">
                Temps moyen entre deux pannes
              </v-tooltip>
            </div>
          </v-card>
        </v-col>

        <!-- MTTR -->
        <v-col cols="12" md="4">
          <v-card variant="tonal" color="info" class="text-center pa-4">
            <v-icon size="32" class="mb-2">mdi-wrench-clock</v-icon>
            <div class="text-h4 font-weight-bold">
              {{ kpi.mttr_heures !== null ? kpi.mttr_heures : '—' }}
            </div>
            <div class="text-caption mt-1">
              MTTR (heures)
              <v-tooltip activator="parent" location="bottom">
                Temps moyen de réparation
              </v-tooltip>
            </div>
          </v-card>
        </v-col>
      </v-row>

      <!-- Note si données partielles -->
      <p
        v-if="!loading && !erreur && kpi.mttr_heures === null && kpi.nombre_pannes > 0"
        class="text-caption text-grey mt-3"
      >
        * Le MTTR ne peut pas être calculé : aucun bon de travail clôturé ne possède de date de
        début et de fin renseignées.
      </p>
    </v-card-text>
  </v-card>
</template>

<script setup>
  import { ref, onMounted } from 'vue'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'

  // ── Props ────────────────────────────────────────────────────────────────────
  const props = defineProps({
    equipementId: {
      type: [Number, String],
      required: true,
    },
  })

  // ── État ─────────────────────────────────────────────────────────────────────
  const kpiApi = useApi(API_BASE_URL)
  const loading = ref(true)
  const erreur = ref(false)
  const kpi = ref({ nombre_pannes: 0, mtbf_heures: null, mttr_heures: null })

  // ── Chargement des KPI ───────────────────────────────────────────────────────
  const fetchKpi = async () => {
    loading.value = true
    erreur.value = false
    try {
      const response = await kpiApi.get(`equipements/${props.equipementId}/kpi/`)
      kpi.value = response
    } catch {
      erreur.value = true
    } finally {
      loading.value = false
    }
  }

  onMounted(fetchKpi)
</script>
