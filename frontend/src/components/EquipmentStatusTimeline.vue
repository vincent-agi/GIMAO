<template>
  <v-card elevation="2" class="mb-4">
    <v-card-title class="text-h6">
      <v-icon class="mr-2">mdi-chart-timeline</v-icon>
      Historique des états
    </v-card-title>
    <v-divider></v-divider>

    <v-card-text>
      <!-- Chargement -->
      <v-row v-if="loading" justify="center" class="py-4">
        <v-progress-circular indeterminate color="primary" />
      </v-row>

      <!-- Erreur -->
      <v-alert v-else-if="erreur" type="error" variant="tonal">
        Impossible de charger l'historique des états.
      </v-alert>

      <!-- Aucun historique -->
      <p v-else-if="!plages.length" class="text-caption text-grey text-center py-4">
        Aucun historique d'état disponible pour cet équipement.
      </p>

      <template v-else>
        <!-- Filtre par période -->
        <v-row dense class="mb-3" align="center">
          <v-col cols="12" sm="5">
            <v-text-field
              v-model="filtreDebut"
              type="date"
              label="Du"
              density="compact"
              variant="outlined"
              hide-details
              clearable
              :max="filtreFin || undefined"
            />
          </v-col>
          <v-col cols="12" sm="5">
            <v-text-field
              v-model="filtreFin"
              type="date"
              label="Au"
              density="compact"
              variant="outlined"
              hide-details
              clearable
              :min="filtreDebut || undefined"
            />
          </v-col>
          <v-col cols="12" sm="2">
            <v-btn variant="text" color="primary" size="small" block @click="toutVoir">
              Tout voir
            </v-btn>
          </v-col>
        </v-row>

        <!-- Message si aucun résultat après filtre -->
        <p v-if="!series.length" class="text-caption text-grey text-center py-4">
          Aucun état sur cette période.
        </p>

        <!-- Conteneur scrollable horizontalement -->
        <div v-else style="overflow-x: auto; overflow-y: hidden; width: 100%">
          <apexchart
            type="rangeBar"
            height="180"
            :width="chartWidth"
            :options="chartOptions"
            :series="series"
          />
        </div>

        <p class="text-caption text-grey text-center mt-1">
          <v-icon size="14">mdi-gesture-swipe-horizontal</v-icon>
          Faire défiler horizontalement pour voir toute la période
        </p>
      </template>
    </v-card-text>
  </v-card>
</template>

<script setup>
  import { ref, computed, onMounted } from 'vue'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'

  // ── Props ────────────────────────────────────────────────────────────────────
  const props = defineProps({
    equipementId: {
      type: [Number, String],
      required: true,
    },
  })

  // ── Constantes ───────────────────────────────────────────────────────────────
  const STATUTS_CONFIG = {
    EN_FONCTIONNEMENT: { label: 'En fonctionnement', couleur: '#4CAF50' },
    DEGRADE: { label: 'Dégradé', couleur: '#FF9800' },
    A_LARRET: { label: "À l'arrêt", couleur: '#F44336' },
    HORS_SERVICE: { label: 'Hors service', couleur: '#616161' },
  }

  // ── État ─────────────────────────────────────────────────────────────────────
  const historiqueApi = useApi(API_BASE_URL)
  const loading = ref(true)
  const erreur = ref(false)
  const historique = ref([])

  const filtreDebut = ref(null)
  const filtreFin = ref(null)

  // ── Chargement ───────────────────────────────────────────────────────────────
  const fetchHistorique = async () => {
    loading.value = true
    erreur.value = false
    try {
      historique.value = await historiqueApi.get(
        `equipements/${props.equipementId}/historique_statuts/`
      )
    } catch {
      erreur.value = true
    } finally {
      loading.value = false
    }
  }

  // ── Calcul des plages de temps ────────────────────────────────────────────────
  const plages = computed(() => {
    if (!historique.value.length) return []
    return historique.value.map((entry, i) => {
      const debut = new Date(entry.dateChangement).getTime()
      const fin =
        i < historique.value.length - 1
          ? new Date(historique.value[i + 1].dateChangement).getTime()
          : Date.now()
      return { statut: entry.statut, debut, fin }
    })
  })

  // ── Bornes visibles selon le filtre ──────────────────────────────────────────
  const limiteMin = computed(() =>
    filtreDebut.value
      ? new Date(filtreDebut.value).getTime()
      : plages.value.length
        ? Math.min(...plages.value.map((p) => p.debut))
        : null
  )
  const limiteMax = computed(() =>
    filtreFin.value ? new Date(filtreFin.value + 'T23:59:59').getTime() : Date.now()
  )

  // Plage minimale de l'axe (1 jour) pour éviter un axe dégénéré
  // quand l'équipement vient d'être créé (début ≈ fin).
  const UN_JOUR_MS = 24 * 60 * 60 * 1000

  const axisMin = computed(() => {
    if (limiteMin.value == null || limiteMax.value == null) return undefined
    const span = limiteMax.value - limiteMin.value
    if (span < UN_JOUR_MS) {
      return limiteMin.value - (UN_JOUR_MS - span) / 2
    }
    return limiteMin.value
  })

  const axisMax = computed(() => {
    if (limiteMin.value == null || limiteMax.value == null) return undefined
    const span = limiteMax.value - limiteMin.value
    if (span < UN_JOUR_MS) {
      return limiteMax.value + (UN_JOUR_MS - span) / 2
    }
    return limiteMax.value
  })

  // ── Plages filtrées ───────────────────────────────────────────────────────────
  const plagesFiltrees = computed(() => {
    if (!filtreDebut.value && !filtreFin.value) return plages.value
    return plages.value.filter((p) => p.fin >= limiteMin.value && p.debut <= limiteMax.value)
  })

  // ── Séries ApexCharts ─────────────────────────────────────────────────────────
  const series = computed(() => {
    const parStatut = {}
    plagesFiltrees.value.forEach(({ statut, debut, fin }) => {
      const debutAffiche = Math.max(debut, limiteMin.value)
      const finAffiche = Math.min(fin, limiteMax.value)
      if (!parStatut[statut]) parStatut[statut] = []
      parStatut[statut].push({ x: 'État', y: [debutAffiche, finAffiche] })
    })
    return Object.entries(parStatut).map(([statut, data]) => ({
      name: STATUTS_CONFIG[statut]?.label ?? statut,
      color: STATUTS_CONFIG[statut]?.couleur ?? '#999999',
      data,
    }))
  })

  // ── Largeur du graphique proportionnelle à la durée ──────────────────────────
  // 150px par mois — ainsi toutes les périodes ont la même échelle
  const chartWidth = computed(() => {
    if (!limiteMin.value || !limiteMax.value) return 800
    const mois = (limiteMax.value - limiteMin.value) / (30 * 24 * 60 * 60 * 1000)
    return Math.max(800, Math.round(mois * 150))
  })

  // ── Réinitialiser ─────────────────────────────────────────────────────────────
  const toutVoir = () => {
    filtreDebut.value = null
    filtreFin.value = null
  }

  // ── Options du graphique ──────────────────────────────────────────────────────
  const chartOptions = computed(() => ({
    chart: {
      type: 'rangeBar',
      toolbar: { show: false }, // pas de barre d'outils
      zoom: { enabled: false }, // pas de zoom
    },
    plotOptions: {
      bar: {
        horizontal: true,
        barHeight: '50%',
        rangeBarGroupRows: false,
      },
    },
    xaxis: {
      type: 'datetime',
      min: axisMin.value ?? undefined,
      max: axisMax.value ?? undefined,
      tickAmount: 6,
      labels: {
        datetimeUTC: false,
        datetimeFormatter: {
          year: 'yyyy',
          month: 'MMM yyyy',
          day: 'dd MMM',
          hour: 'HH:mm',
        },
      },
    },
    yaxis: { show: false },
    legend: { show: true, position: 'bottom' },
    tooltip: {
      x: { format: 'dd MMM yyyy HH:mm' },
      y: { title: { formatter: () => '' } },
    },
    grid: { padding: { left: 10, right: 10 } },
  }))

  onMounted(fetchHistorique)
</script>
