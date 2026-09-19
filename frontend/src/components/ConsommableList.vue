<template>
  <v-container fluid>
    <StockStatistics
      :consommables="displayedConsommables"
      :summary="stockSummary"
      :selected-filter="selectedStockFilter"
      :bt-count="btPendingCount"
      class="mb-4"
      @filter-change="selectedStockFilter = $event"
    />

    <v-row class="mb-4" align="start">
      <v-col cols="12" lg="6">
        <v-card class="rounded-lg pa-4" elevation="1">
          <div class="mb-4">
            <h1 class="text-h4 text-primary">{{ title }}</h1>
            <p class="text-subtitle-1 text-grey">{{ currentSubtitle }}</p>
          </div>

          <div class="d-flex align-center ga-3 mb-4">
            <v-btn
              v-if="store.getters.hasPermission('mag:viewList')"
              prepend-icon="mdi-filter-variant"
              variant="flat"
              class="filter-btn"
              rounded="lg"
              @click="showMagasinFilterDialog = true"
            >
              Filtrer
            </v-btn>

            <v-text-field
              v-model="searchInput"
              placeholder="Rechercher un consommable..."
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              hide-details
              clearable
              class="flex-grow-1"
              @keydown.enter.prevent
            />
          </div>

          <v-data-table
            :headers="tableHeaders"
            :items="displayedConsommables"
            :loading="loading"
            :items-per-page="-1"
            hide-default-footer
            class="elevation-0"
            @click:row="(event, { item }) => $emit('row-click', item)"
          >
            <template #[`item.quantite`]="{ item }">
              <v-chip
                size="small"
                :color="getQuantiteColor(item.quantite, item.seuilStockFaible)"
                variant="tonal"
              >
                {{ item.quantite }}
              </v-chip>
            </template>

            <template #no-data>
              <div class="text-center pa-4">
                <v-icon size="64" color="grey">mdi-package-variant</v-icon>
                <p class="text-h6 mt-2">{{ noDataText }}</p>
              </div>
            </template>
          </v-data-table>

          <ServerPaginationControls
            :page="currentPage"
            :page-size="pageSize"
            :page-count="totalPages"
            :total-items="totalItems"
            item-label-singular="consommable"
            item-label-plural="consommables"
            :reserve-fab-space="showCreateButton"
            @update:page="currentPage = $event"
            @update:page-size="pageSize = $event"
          />
        </v-card>
      </v-col>

      <!-- Colonne BT en attente (50%) -->
      <v-col v-if="store.getters.hasPermission('stock:viewReservations')" cols="12" lg="6">
        <BTStockValidation
          ref="btStockValidationRef"
          @count-updated="btPendingCount = $event"
          @counts-updated="handleBtCountsUpdated"
          @stock-updated="handleStockUpdated"
        />
      </v-col>
    </v-row>

    <FloatingCreateButton
      :visible="showCreateButton"
      :tooltip="createButtonText"
      :elevation="8"
      @click="$emit('create')"
    />

    <v-dialog v-model="showMagasinFilterDialog" max-width="900px">
      <v-card class="rounded-lg">
        <v-card-title class="d-flex align-center justify-space-between pa-4 pb-2">
          <span class="text-h6 text-primary font-weight-bold">Filtrer par magasin</span>
          <v-btn icon size="small" variant="text" @click="showMagasinFilterDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>

        <v-divider />

        <v-card-text class="pa-4">
          <MagasinFilter
            v-model:selected-magasin="selectedMagasin"
            :magasins="magasins"
            :consommables="displayedConsommables"
            @edit:magasin="handleOpenEditMagasin"
            @archive:magasin="handleOpenArchiveMagasin"
          />
        </v-card-text>

        <v-divider />

        <v-card-actions class="pa-4">
          <v-btn
            prepend-icon="mdi-plus"
            variant="text"
            color="primary"
            @click="handleCreateMagasin"
          >
            Ajouter un magasin
          </v-btn>
          <v-spacer />
          <v-btn variant="outlined" @click="handleCancelFilter"> Réinitialiser </v-btn>
          <v-btn color="primary" variant="flat" @click="handleApplyFilter"> Fermer </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showMagasinFormDialog" max-width="500px">
      <v-card class="rounded-lg">
        <MagasinForm
          :magasin="magasinToEdit"
          @created="handleMagasinCreated"
          @updated="handleMagasinUpdated"
          @close="showMagasinFormDialog = false"
        />
      </v-card>
    </v-dialog>

    <ConfirmationModal
      v-model="showArchiveDialog"
      type="warning"
      title="Confirmer l'archivage"
      message="Êtes-vous sûr de vouloir archiver le magasin ?\nIl ne sera plus visible dans la liste des magasins."
      confirm-text="Archiver"
      :loading="archiving"
      @confirm="archiveMagasin"
      @cancel="handleCancelArchive"
    />
  </v-container>
</template>

<script setup>
  import { computed, onMounted, ref } from 'vue'
  import { useStore } from 'vuex'
  import MagasinFilter from '@/components/Stock/MagasinFilter.vue'
  import MagasinForm from '@/components/Forms/MagasinForm.vue'
  import StockStatistics from '@/components/Stock/StockStatistics.vue'
  import BTStockValidation from '@/components/Stock/BTStockValidation.vue'
  import ConfirmationModal from '@/components/common/ConfirmationModal.vue'
  import FloatingCreateButton from '@/components/common/FloatingCreateButton.vue'
  import ServerPaginationControls from '@/components/common/ServerPaginationControls.vue'
  import { useApi } from '@/composables/useApi'
  import { usePaginatedList } from '@/composables/usePaginatedList'
  import { API_BASE_URL } from '@/utils/constants'

  defineProps({
    title: {
      type: String,
      default: 'Liste des consommables',
    },
    createButtonText: {
      type: String,
      default: 'Ajouter un consommable',
    },
    noDataText: {
      type: String,
      default: 'Aucun consommable trouvé',
    },
  })

  const emit = defineEmits(['create', 'row-click', 'consommables-loaded'])

  const consommablesApi = useApi(API_BASE_URL)
  const magasinsApi = useApi(API_BASE_URL)
  const archiveApi = useApi(API_BASE_URL)
  const store = useStore()

  const errorMessage = ref('')
  const selectedMagasin = ref(null)
  const selectedStockFilter = ref(null)
  const showMagasinFilterDialog = ref(false)
  const showMagasinFormDialog = ref(false)
  const showArchiveDialog = ref(false)
  const magasinToEdit = ref(null)
  const magasinToArchive = ref(null)
  const btPendingCount = ref(0)
  const btCompletedCount = ref(0)
  const btStockValidationRef = ref(null)
  const archiving = ref(false)

  const magasins = computed(() => magasinsApi.data.value || [])
  const showCreateButton = computed(() => store.getters.hasPermission('cons:create'))

  const tableHeaders = [
    { title: 'Nom', key: 'designation', sortable: true },
    { title: 'Magasin', key: 'magasin_nom' },
    { title: 'Quantité', key: 'quantite', sortable: true, align: 'center' },
  ]

  const {
    items,
    currentPage,
    pageSize,
    totalItems,
    totalPages,
    searchQuery,
    loading,
    extra,
    fetchPage,
    handleSearch,
  } = usePaginatedList({
    api: consommablesApi,
    endpoint: 'consommables/',
    initialPageSize: 10,
    buildParams: () => ({
      magasin_id: selectedMagasin.value ?? undefined,
      stock_status: selectedStockFilter.value ?? undefined,
    }),
    watchSource: () => [selectedMagasin.value ?? '', selectedStockFilter.value ?? ''],
    onFetched: (_response, normalized) => {
      emit('consommables-loaded', normalized.items)
    },
  })

  const searchInput = computed({
    get: () => searchQuery.value,
    set: (value) => handleSearch(value),
  })

  const stockSummary = computed(() => extra.value?.summary || null)

  const displayedConsommables = computed(() =>
    items.value.map((consommable) => {
      let quantite = consommable.quantite_totale ?? 0

      if (selectedMagasin.value !== null) {
        const stock = (consommable.stocks || []).find(
          (item) => item.magasin === selectedMagasin.value
        )
        quantite = stock ? stock.quantite : 0
      }

      const magasinNom = [
        ...new Set((consommable.stocks || []).map((stock) => stock.magasin_nom).filter(Boolean)),
      ].join(', ')

      return {
        ...consommable,
        quantite,
        magasin_nom: magasinNom || '-',
      }
    })
  )

  const currentSubtitle = computed(() => {
    if (selectedMagasin.value === null) {
      return `${totalItems.value} consommable(s) au total`
    }

    const magasin = magasins.value.find((item) => item.id === selectedMagasin.value)
    return magasin ? `Magasin : ${magasin.nom} - ${totalItems.value} consommable(s)` : ''
  })

  const getQuantiteColor = (quantite, seuil) => {
    if (quantite === 0) return 'error'
    if (seuil !== null && seuil !== undefined && quantite <= seuil) return 'warning'
    return 'success'
  }

  const fetchMagasins = async () => {
    try {
      await magasinsApi.get('magasins/')
    } catch {
      errorMessage.value = 'Erreur lors du chargement des magasins'
    }
  }

  const fetchData = async () => {
    await Promise.allSettled([fetchPage(), fetchMagasins()])
  }

  const handleApplyFilter = () => {
    showMagasinFilterDialog.value = false
  }

  const handleCreateMagasin = () => {
    magasinToEdit.value = null
    showMagasinFormDialog.value = true
  }

  const handleOpenEditMagasin = (magasin) => {
    magasinToEdit.value = magasin
    showMagasinFormDialog.value = true
  }

  const handleOpenArchiveMagasin = (magasin) => {
    magasinToArchive.value = magasin
    showArchiveDialog.value = true
  }

  const handleMagasinCreated = async () => {
    await fetchData()
    showMagasinFormDialog.value = false
  }

  const handleMagasinUpdated = async () => {
    await fetchData()
    showMagasinFormDialog.value = false
  }

  const handleCancelArchive = () => {
    showArchiveDialog.value = false
    magasinToArchive.value = null
  }

  const archiveMagasin = async () => {
    if (!magasinToArchive.value?.id) {
      showArchiveDialog.value = false
      return
    }

    archiving.value = true

    try {
      await archiveApi.patch(`magasins/${magasinToArchive.value.id}/set-archive/`, {
        archive: true,
      })
      await fetchData()

      if (selectedMagasin.value === magasinToArchive.value.id) {
        selectedMagasin.value = null
      }

      showArchiveDialog.value = false
    } catch {
      errorMessage.value = "Erreur lors de l'archivage du magasin"
    } finally {
      archiving.value = false
      magasinToArchive.value = null
    }
  }

  const handleCancelFilter = () => {
    selectedMagasin.value = null
    showMagasinFilterDialog.value = false
  }

  const handleBtCountsUpdated = ({ pending, completed, reserved }) => {
    btPendingCount.value = pending ?? 0
    btCompletedCount.value = reserved ?? completed ?? 0
  }

  const handleStockUpdated = async () => {
    await fetchPage()
  }

  onMounted(() => {
    fetchData()
  })
</script>

<style scoped>
  .filter-btn {
    background-color: #f1f5ff !important;
    color: #05004e !important;
    text-transform: none !important;
    font-weight: 500;
    letter-spacing: normal !important;
  }

  .filter-btn:hover {
    background-color: #e4ebff !important;
  }
</style>
