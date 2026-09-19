<template>
  <BaseListView
    :title="title"
    :headers="tableHeaders"
    :items="displayedItems"
    :loading="loading"
    :error-message="errorMessage"
    :show-search="showSearch"
    :show-create-button="false"
    :search-value="serverPagination ? serverSearch : undefined"
    :no-data-text="noDataText"
    :items-per-page="serverPagination ? -1 : 10"
    :hide-default-footer="serverPagination"
    no-data-icon="mdi-package-variant-closed"
    :internal-search="!serverPagination"
    @row-click="$emit('row-click', $event)"
    @clear-error="errorMessage = ''"
    @search="handleSearch"
  >
    <template v-if="store.getters.hasPermission('eq:create')" #actions>
      <v-btn
        variant="outlined"
        color="primary"
        prepend-icon="mdi-file-download-outline"
        size="small"
        :loading="downloadingTemplate"
        @click="downloadTemplate"
      >
        <span class="d-none d-sm-inline">Modèle Excel</span>
        <span class="d-inline d-sm-none">Modèle</span>
      </v-btn>
      <v-btn
        variant="outlined"
        color="primary"
        prepend-icon="mdi-file-upload-outline"
        size="small"
        @click="showImportDialog = true"
      >
        <span class="d-none d-sm-inline">Importer depuis Excel</span>
        <span class="d-inline d-sm-none">Importer</span>
      </v-btn>
    </template>

    <template #[`item.statut.statut`]="{ item }">
      <v-chip
        v-if="item.statut && item.statut.statut"
        :color="getStatusColor(item.statut.statut)"
        variant="tonal"
        size="small"
      >
        {{ getStatusLabel(item.statut.statut) }}
      </v-chip>

      <v-chip v-else color="grey" variant="outlined" size="small"> Non renseigné </v-chip>
    </template>

    <template v-if="serverPagination" #after-table>
      <ServerPaginationControls
        :page="currentPage"
        :page-size="pageSize"
        :page-count="totalPages"
        :total-items="totalItems"
        item-label-singular="équipement"
        item-label-plural="équipements"
        :reserve-fab-space="reserveFabSpace"
        @update:page="currentPage = $event"
        @update:page-size="pageSize = $event"
      />
    </template>
  </BaseListView>

  <!-- Dialog d'import Excel -->
  <v-dialog v-model="showImportDialog" max-width="700" scrollable persistent>
    <v-card>
      <v-card-title class="text-h6 pa-4 pb-2">Importer des équipements depuis Excel</v-card-title>
      <v-divider />
      <v-card-text class="pa-4">
        <p class="text-body-2 mb-4">
          Téléchargez le modèle Excel, remplissez-le avec vos données, puis importez-le ici. Les
          lieux, fabricants, fournisseurs et familles indiqués seront créés automatiquement s'ils
          n'existent pas encore.
        </p>

        <v-file-input
          v-model="importFile"
          label="Fichier Excel (.xlsx)"
          accept=".xlsx"
          variant="outlined"
          density="comfortable"
          prepend-icon="mdi-file-excel-outline"
          :disabled="importing"
        />

        <v-alert v-if="importError" type="error" variant="tonal" density="compact" class="mt-2">
          {{ importError }}
        </v-alert>

        <div v-if="importResults.length" class="mt-4">
          <div v-for="result in importResults" :key="result.onglet" class="mb-3">
            <div class="d-flex align-center">
              <strong>{{ result.onglet }}</strong>
              <v-chip size="small" color="success" variant="tonal" class="ml-2">
                {{ result.crees }} créé(s)
              </v-chip>
              <v-chip size="small" color="grey" variant="tonal" class="ml-2">
                {{ result.existants_reutilises }} déjà existant(s)
              </v-chip>
              <v-chip
                v-if="result.erreurs.length"
                size="small"
                color="error"
                variant="tonal"
                class="ml-2"
              >
                {{ result.erreurs.length }} erreur(s)
              </v-chip>
            </div>
            <ul v-if="result.erreurs.length" class="text-caption text-error mt-1">
              <li v-for="(err, idx) in result.erreurs" :key="idx">
                Ligne {{ err.ligne }} : {{ err.message }}
              </li>
            </ul>
          </div>
        </div>
      </v-card-text>
      <v-divider />
      <v-card-actions class="pa-4">
        <v-spacer />
        <v-btn variant="text" @click="closeImportDialog">Fermer</v-btn>
        <v-btn color="primary" :loading="importing" :disabled="!importFile" @click="submitImport">
          Importer
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
  import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
  import { useStore } from 'vuex'
  import BaseListView from '@/components/common/BaseListView.vue'
  import ServerPaginationControls from '@/components/common/ServerPaginationControls.vue'
  import { useApi } from '@/composables/useApi'
  import { getStatusColor, getStatusLabel } from '@/utils/helpers'
  import { API_BASE_URL } from '@/utils/constants'
  import { extractItems, fetchAllPages } from '@/utils/paginatedApi'

  const store = useStore()

  const props = defineProps({
    title: {
      type: String,
      default: 'Liste des Équipements',
    },
    showSearch: {
      type: Boolean,
      default: true,
    },
    noDataText: {
      type: String,
      default: 'Aucun équipement trouvé',
    },
    additionalHeaders: {
      type: Array,
      default: () => [],
    },
    tableHeaders: {
      type: Array,
      default: () => [
        { title: 'Code GMAO', key: 'reference', sortable: true, align: 'center' },
        { title: 'Désignation', key: 'designation', sortable: true, align: 'center' },
        { title: 'Lieu', key: 'lieu.nomLieu', sortable: false, align: 'center' },
        { title: 'Modèle', key: 'modele', sortable: false, align: 'center' },
        {
          title: 'Statut',
          key: 'statut.statut',
          sortable: true,
          align: 'center',
          sort: (a, b) => {
            const order = ['EN_FONCTIONNEMENT', 'DEGRADE', 'A_LARRET', 'HORS_SERVICE']
            return order.indexOf(a) - order.indexOf(b)
          },
        },
      ],
    },
    filteredItems: {
      type: Array,
      default: () => [],
    },
    getItemsBySelf: {
      type: Boolean,
      default: false,
    },
    serverPagination: {
      type: Boolean,
      default: false,
    },
    selectedLocationIds: {
      type: Array,
      default: () => [],
    },
    selectedModelIds: {
      type: Array,
      default: () => [],
    },
    reserveFabSpace: {
      type: Boolean,
      default: false,
    },
  })

  const emit = defineEmits(['row-click', 'equipments-loaded', 'locations-loaded', 'models-loaded'])

  const equipmentsApi = useApi(API_BASE_URL)
  const locationsApi = useApi(API_BASE_URL)
  const modelsApi = useApi(API_BASE_URL)
  const importApi = useApi(API_BASE_URL)

  // Import d'équipements depuis un fichier Excel
  const showImportDialog = ref(false)
  const importFile = ref(null)
  const importing = ref(false)
  const importError = ref('')
  const importResults = ref([])
  const downloadingTemplate = ref(false)

  const downloadTemplate = async () => {
    downloadingTemplate.value = true
    try {
      const response = await importApi.getRaw(
        'import/equipements/template/',
        {},
        { responseType: 'blob' }
      )
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'modele_import_equipements.xlsx')
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Erreur lors du téléchargement du modèle :', error)
      errorMessage.value = 'Erreur lors du téléchargement du modèle Excel'
    } finally {
      downloadingTemplate.value = false
    }
  }

  const closeImportDialog = () => {
    showImportDialog.value = false
    importFile.value = null
    importError.value = ''
    importResults.value = []
  }

  const submitImport = async () => {
    const file = Array.isArray(importFile.value) ? importFile.value[0] : importFile.value
    if (!file) return

    importing.value = true
    importError.value = ''
    importResults.value = []

    const form = new FormData()
    form.append('file', file)

    try {
      const response = await importApi.post('import/equipements/', form)
      importResults.value = response?.resultats || []
      await fetchData()
    } catch (error) {
      console.error("Erreur lors de l'import :", error)
      importError.value =
        error?.response?.data?.error || "Une erreur est survenue lors de l'import du fichier."
    } finally {
      importing.value = false
    }
  }

  const errorMessage = ref('')
  const currentItems = ref([])
  const currentPage = ref(1)
  const pageSize = ref(25)
  const totalItems = ref(0)
  const serverSearch = ref('')

  let searchDebounceId = null

  const locations = computed(() => extractItems(locationsApi.data.value))
  const equipmentModels = computed(() => extractItems(modelsApi.data.value))
  const loading = computed(
    () => equipmentsApi.loading.value || locationsApi.loading.value || modelsApi.loading.value
  )
  const totalPages = computed(() => Math.max(1, Math.ceil(totalItems.value / pageSize.value)))

  const displayedItems = computed(() => {
    if (props.serverPagination || props.getItemsBySelf) {
      return currentItems.value
    }
    return props.filteredItems
  })

  const buildEquipementParams = () => {
    if (!props.serverPagination) {
      return {}
    }

    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
    }

    const searchValue = serverSearch.value.trim()
    if (searchValue) {
      params.search = searchValue
    }

    if (props.selectedLocationIds.length > 0) {
      params.lieu_ids = props.selectedLocationIds.join(',')
    }

    if (props.selectedModelIds.length > 0) {
      params.modele_ids = props.selectedModelIds.join(',')
    }

    return params
  }

  const fetchEquipments = async () => {
    const response = props.serverPagination
      ? await equipmentsApi.get('equipements/', buildEquipementParams())
      : await fetchAllPages(equipmentsApi, 'equipements/')
    const items = extractItems(response)

    currentItems.value = items
    totalItems.value = props.serverPagination ? Number(response?.count || 0) : items.length
    emit('equipments-loaded', items)
  }

  const fetchSupportData = async () => {
    const [locationsResponse, modelsResponse] = await Promise.all([
      locationsApi.get('lieux/hierarchy/'),
      modelsApi.get('modele-equipements/'),
    ])

    emit('locations-loaded', extractItems(locationsResponse))
    emit('models-loaded', extractItems(modelsResponse))
  }

  const fetchData = async () => {
    try {
      await Promise.all([fetchSupportData(), fetchEquipments()])
    } catch (error) {
      console.error('Erreur lors du chargement des données:', error)
      errorMessage.value = 'Erreur lors du chargement des données'
    }
  }

  const resetToFirstPageAndFetch = () => {
    if (currentPage.value !== 1) {
      currentPage.value = 1
      return
    }
    fetchEquipments().catch((error) => {
      console.error('Erreur lors du chargement des équipements:', error)
      errorMessage.value = 'Erreur lors du chargement des équipements'
    })
  }

  const handleSearch = (value) => {
    if (!props.serverPagination) {
      return
    }

    serverSearch.value = typeof value === 'string' ? value : value?.target?.value || ''

    if (searchDebounceId) {
      clearTimeout(searchDebounceId)
    }

    searchDebounceId = setTimeout(() => {
      resetToFirstPageAndFetch()
    }, 300)
  }

  watch(currentPage, () => {
    if (!props.serverPagination) {
      return
    }
    fetchEquipments().catch((error) => {
      console.error('Erreur lors du chargement des équipements:', error)
      errorMessage.value = 'Erreur lors du chargement des équipements'
    })
  })

  watch(pageSize, () => {
    if (!props.serverPagination) {
      return
    }
    resetToFirstPageAndFetch()
  })

  watch(
    () => [props.selectedLocationIds.join(','), props.selectedModelIds.join(',')],
    () => {
      if (!props.serverPagination) {
        return
      }
      resetToFirstPageAndFetch()
    }
  )

  defineExpose({
    fetchData,
    fetchEquipments,
    locations,
    equipmentModels,
  })

  onMounted(() => {
    fetchData()
  })

  onBeforeUnmount(() => {
    if (searchDebounceId) {
      clearTimeout(searchDebounceId)
    }
  })
</script>

<style scoped>
  .v-data-table tr:hover {
    background-color: #e6f2ff;
    transition: background-color 0.3s ease;
  }

  .v-data-table tr:hover td {
    color: #0056b3;
  }

  .v-data-table th {
    color: black !important;
  }
</style>
