<template>
  <BaseListView
    ref="tableContainer"
    :title="title"
    :subtitle="subtitle"
    :headers="vuetifyHeaders"
    :items="displayedItems"
    :sort-by="defaultSortBy"
    :loading="loading"
    :error-message="resolvedErrorMessage"
    :show-search="showSearch"
    :show-create-button="false"
    :search-value="usesLocalItems ? undefined : searchQuery"
    :create-button-text="createButtonText"
    :internal-search="usesLocalItems ? internalSearch : false"
    :items-per-page="usesLocalItems ? 10 : -1"
    :hide-default-footer="!usesLocalItems"
    table-class="bt-table"
    no-data-icon="mdi-wrench-outline"
    :no-data-text="noDataText"
    @row-click="onRowClick"
    @create="$emit('create')"
    @clear-error="errorMessage = ''"
    @search="handleSearch"
  >
    <template #filters>
      <v-btn
        :color="showAncien ? 'primary' : undefined"
        :variant="showAncien ? 'flat' : 'outlined'"
        prepend-icon="mdi-history"
        size="small"
        class="mr-2"
        @click="toggleAncien"
      >
        {{ showAncien ? 'Voir les actifs' : 'Anciens' }}
      </v-btn>
      <v-btn
        :color="showTout ? 'primary' : undefined"
        :variant="showTout ? 'flat' : 'outlined'"
        prepend-icon="mdi-format-list-bulleted"
        size="small"
        class="mr-2"
        @click="toggleTout"
      >
        {{ showTout ? 'Voir les actifs' : 'Tout afficher' }}
      </v-btn>
      <v-select
        v-if="showStatutFilter && !showAncien && !showTout"
        v-model="selectedStatut"
        label="Statut"
        :items="statutOptions"
        item-title="title"
        item-value="value"
        density="compact"
        variant="outlined"
        clearable
        hide-details
      />
      <slot name="filters"></slot>
    </template>

    <template #[`item.id`]="{ item }">
      <span class="font-weight-medium">{{ formatBTNumber(item.id) }}</span>
    </template>

    <template #[`item.nom`]="{ item }">
      <span class="bt-diagnostic-truncate" :title="item.nom || ''">
        {{ item.nom || '-' }}
      </span>
    </template>

    <template #[`item.date_assignation`]="{ item }">
      {{ formatDateTime(item.date_assignation) }}
    </template>

    <template #[`item.equipement_designation`]="{ item }">
      {{ item.equipement_designation || '-' }}
    </template>

    <template #[`item.diagnostic`]="{ item }">
      <span class="bt-diagnostic-truncate" :title="item.diagnostic || ''">
        {{ item.diagnostic || '-' }}
      </span>
    </template>

    <template #[`item.date_cloture`]="{ item }">
      {{ item.date_cloture ? formatDateTime(item.date_cloture) : '-' }}
    </template>

    <template #[`item.date_prevue`]="{ item }">
      {{ item.date_prevue ? formatDateTime(item.date_prevue) : '-' }}
    </template>

    <template #[`item.utilisateur_assigne`]="{ item }">
      <span v-if="item.utilisateur_assigne && item.utilisateur_assigne.length > 0">
        {{
          item.utilisateur_assigne
            .map((u) => formatUserDisplay(u))
            .filter(Boolean)
            .join(', ') || '-'
        }}
      </span>
      <span v-else class="text-grey">Non assigné</span>
    </template>

    <template #[`item.statut`]="{ item }">
      <v-chip v-if="item.statut" :color="getInterventionStatusColor(item.statut)">
        {{ INTERVENTION_STATUS[item.statut] || item.statut }}
      </v-chip>
      <span v-else>-</span>
    </template>

    <template v-if="!usesLocalItems" #after-table>
      <ServerPaginationControls
        :page="currentPage"
        :page-size="pageSize"
        :page-count="totalPages"
        :total-items="totalItems"
        item-label-singular="bon de travail"
        item-label-plural="bons de travail"
        :reserve-fab-space="showCreateButton"
        @update:page="currentPage = $event"
        @update:page-size="pageSize = $event"
      />
    </template>
  </BaseListView>

  <FloatingCreateButton
    :visible="showCreateButton"
    :tooltip="createButtonText"
    @click="$emit('create')"
  />
</template>

<script setup>
  import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
  import { useDisplay } from 'vuetify'
  import BaseListView from '@/components/common/BaseListView.vue'
  import FloatingCreateButton from '@/components/common/FloatingCreateButton.vue'
  import ServerPaginationControls from '@/components/common/ServerPaginationControls.vue'
  import { useApi } from '@/composables/useApi'
  import { usePaginatedList } from '@/composables/usePaginatedList'
  import { formatDateTime, getInterventionStatusColor } from '@/utils/helpers'
  import { API_BASE_URL, TABLE_HEADERS, INTERVENTION_STATUS } from '@/utils/constants'

  const props = defineProps({
    title: { type: String, default: 'Liste des bons de travail' },
    subtitle: { type: String, default: '' },
    showSearch: { type: Boolean, default: true },
    internalSearch: { type: Boolean, default: false },
    createButtonText: { type: String, default: '' },
    noDataText: { type: String, default: 'Aucun bon de travail' },
    showCreateButton: { type: Boolean, default: true },
    items: { type: Array, default: null },
    fetchOnMount: { type: Boolean, default: true },
    apiEndpoint: { type: String, default: 'bons-travail/' },
    variant: {
      type: String,
      default: 'auto',
      validator: (value) => ['auto', 'mobile', 'light', 'full'].includes(value),
    },
    showStatutFilter: { type: Boolean, default: false },
    statut: { type: String, default: '' },
  })

  const emit = defineEmits(['row-click', 'create', 'loaded'])

  const { smAndDown, lgAndUp } = useDisplay()
  const api = useApi(API_BASE_URL)

  const errorMessage = ref('')
  const containerWidth = ref(0)
  const tableContainer = ref(null)
  const selectedStatut = ref(props.statut || '')
  const showAncien = ref(false)
  const showTout = ref(false)

  const toggleAncien = () => {
    showAncien.value = !showAncien.value
    if (showAncien.value) showTout.value = false
  }

  const toggleTout = () => {
    showTout.value = !showTout.value
    if (showTout.value) showAncien.value = false
  }

  const formatBTNumber = (id) => (id != null ? `BT-${String(id).padStart(4, '0')}` : '-')

  let resizeObserver = null
  let rafId = null

  const usesLocalItems = computed(() => Array.isArray(props.items))

  const statutOptions = computed(() => {
    const options = [
      { value: '', title: 'Tous (hors clôturés)' },
      { value: 'ALL', title: 'Tous (avec clôturés)' },
    ]

    for (const [value, label] of Object.entries(INTERVENTION_STATUS)) {
      options.push({ value, title: label })
    }

    return options
  })

  const activeStatut = computed(() => {
    if (props.showStatutFilter) {
      return String(selectedStatut.value || '').trim()
    }

    return String(props.statut || '').trim()
  })

  const {
    items,
    currentPage,
    pageSize,
    totalItems,
    totalPages,
    searchQuery,
    loading,
    errorMessage: paginationErrorMessage,
    fetchPage,
    handleSearch,
  } = usePaginatedList({
    api,
    endpoint: () => props.apiEndpoint,
    initialPageSize: 10,
    enabled: () => !usesLocalItems.value && props.fetchOnMount,
    buildParams: () => {
      if (showAncien.value) {
        return { vue: 'ancien' }
      }

      if (showTout.value) {
        return { vue: 'tout' }
      }

      const statut = activeStatut.value

      if (!statut) {
        return {}
      }

      if (statut === 'ALL') {
        return { cloture: true }
      }

      return {
        statut,
        cloture: statut === 'CLOTURE' ? true : undefined,
      }
    },
    watchSource: () => [
      props.apiEndpoint,
      activeStatut.value,
      showAncien.value,
      showTout.value,
      props.fetchOnMount,
    ],
    onFetched: (_response, normalized) => {
      emit('loaded', normalized.items)
    },
  })

  const resolvedErrorMessage = computed(() => errorMessage.value || paginationErrorMessage.value)

  const displayedItems = computed(() => {
    if (usesLocalItems.value) {
      const list = Array.isArray(props.items) ? props.items : []
      const statut = activeStatut.value

      if (!statut) {
        return list.filter((item) => item && item.statut !== 'CLOTURE')
      }

      if (statut === 'ALL') {
        return list
      }

      return list.filter((item) => item && item.statut === statut)
    }

    return items.value
  })

  const resolvedVariant = computed(() => {
    if (props.variant === 'auto') {
      if (smAndDown.value) return 'mobile'
      return lgAndUp.value ? 'full' : 'light'
    }

    return props.variant
  })

  const baseHeaders = computed(() => {
    if (containerWidth.value < 860 && props.variant === 'auto') {
      return TABLE_HEADERS.INTERVENTIONS_MOBILE || []
    }

    if (resolvedVariant.value === 'full') return TABLE_HEADERS.INTERVENTIONS || []
    if (resolvedVariant.value === 'mobile') return TABLE_HEADERS.INTERVENTIONS_MOBILE || []
    return TABLE_HEADERS.INTERVENTIONS_LIGHT || []
  })

  const vuetifyHeaders = computed(() =>
    baseHeaders.value.map((header) => ({
      title: header.title,
      key: header.key || header.value,
      value: header.value,
      align: header.align,
      sortable: header.sortable,
      width: header.width,
      maxWidth: header.maxWidth,
    }))
  )

  const defaultSortBy = [{ key: 'id', order: 'desc' }]

  const onRowClick = (item) => {
    emit('row-click', item)
  }

  const formatUserDisplay = (user) => {
    if (!user) return ''

    const prenom = String(user.prenom || '').trim()
    const nomFamille = String(user.nomFamille || '').trim()

    if (prenom || nomFamille) {
      return `${prenom} ${nomFamille}`.trim()
    }

    return String(user.nomUtilisateur || '').trim()
  }

  const observeTableContainer = () => {
    if (!resizeObserver) return

    const tableElement =
      tableContainer.value?.$el?.querySelector('.v-data-table') || tableContainer.value?.$el
    if (tableElement) {
      resizeObserver.observe(tableElement)
    }
  }

  onMounted(() => {
    if (!usesLocalItems.value && props.fetchOnMount) {
      fetchPage().catch(() => {
        errorMessage.value = 'Erreur lors du chargement des bons de travail'
      })
    } else if (usesLocalItems.value) {
      emit('loaded', displayedItems.value)
    }

    resizeObserver = new ResizeObserver((entries) => {
      if (entries?.[0]) {
        if (rafId) {
          cancelAnimationFrame(rafId)
        }

        rafId = requestAnimationFrame(() => {
          containerWidth.value = Math.round(entries[0].contentRect.width)
        })
      }
    })

    nextTick(() => {
      observeTableContainer()
    })
  })

  watch(
    () => props.items,
    (value) => {
      if (Array.isArray(value)) {
        emit('loaded', displayedItems.value)
      }
    }
  )

  onBeforeUnmount(() => {
    if (rafId) {
      cancelAnimationFrame(rafId)
    }

    if (resizeObserver) {
      resizeObserver.disconnect()
    }
  })
</script>

<style scoped>
  .bt-diagnostic-truncate {
    display: block;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  :deep(.bt-table .v-table__wrapper > table) {
    table-layout: fixed;
    width: 100%;
    min-width: 600px;
  }

  :deep(.bt-table td) {
    overflow: hidden;
  }
</style>
