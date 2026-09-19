<template>
  <v-card class="rounded-lg pa-4" elevation="1">
    <div class="mb-4">
      <h1 class="text-h4 text-primary">BT en attente de mise de côté</h1>
      <p class="text-subtitle-1 stock-summary mb-0">
        {{ pendingCount }} BT en attente, {{ reservedCount }} BT mis de côté,
        {{ recoveredCount }} BT récupérés
      </p>
    </div>

    <v-text-field
      v-model="searchInput"
      placeholder="Rechercher un bon ou un consommable..."
      prepend-inner-icon="mdi-magnify"
      variant="outlined"
      density="compact"
      hide-details
      clearable
      class="mb-4"
      @keydown.enter.prevent
    />

    <v-card-text class="pt-0 px-0 pb-0">
      <!-- Loading -->
      <div v-if="loading" class="text-center py-4">
        <v-progress-circular indeterminate color="primary" size="32" />
      </div>

      <!-- Liste vide -->
      <v-alert
        v-else-if="pendingCount === 0 && reservedCount === 0 && recoveredCount === 0"
        type="success"
        variant="tonal"
        icon="mdi-check-circle"
      >
        Aucun bon de travail en attente de mise de côté
      </v-alert>

      <v-alert
        v-if="stockError"
        type="warning"
        variant="tonal"
        icon="mdi-alert-circle"
        class="mb-3"
      >
        {{ stockError }}
      </v-alert>

      <!-- Liste des BT -->
      <div v-else class="bt-list">
        <div v-if="pendingBons.length > 0" class="bt-section">
          <button type="button" class="section-toggle" @click="toggleSection('pending')">
            <div class="section-toggle-content">
              <div class="section-title mb-0">En attente</div>
              <v-chip size="small" color="primary" variant="tonal">
                {{ pendingBons.length }} BT
              </v-chip>
            </div>
            <v-icon size="20" class="section-toggle-icon">
              {{ isSectionCollapsed('pending') ? 'mdi-chevron-down' : 'mdi-chevron-up' }}
            </v-icon>
          </button>

          <v-expand-transition>
            <div v-show="!isSectionCollapsed('pending')">
              <v-expansion-panels variant="accordion">
                <v-expansion-panel
                  v-for="bt in pendingBons"
                  :key="bt.id"
                  class="bt-item mb-2"
                  elevation="0"
                >
                  <v-expansion-panel-title class="py-3">
                    <v-row no-gutters align="center" class="w-100">
                      <v-col cols="8" class="d-flex align-center">
                        <v-icon color="primary" size="20" class="mr-3">mdi-wrench</v-icon>
                        <div class="bt-info">
                          <span class="bt-name">{{ bt.nom }}</span>
                          <span class="bt-date">Date : {{ formatDate(bt.date_assignation) }}</span>
                        </div>
                      </v-col>
                      <v-col cols="4" class="text-right">
                        <div class="bt-title-metrics">
                          <v-chip size="small" color="primary" variant="tonal">
                            {{ getReservedCount(bt) }}/{{ getTotalCount(bt) }} préparé(s)
                          </v-chip>
                        </div>
                      </v-col>
                    </v-row>
                  </v-expansion-panel-title>

                  <v-expansion-panel-text>
                    <v-list density="compact" class="py-0">
                      <v-list-item
                        v-for="cons in getSortedConsommables(bt)"
                        :key="cons.consommable"
                        class="consommable-item px-0"
                        :class="{ 'consommable-item--reserved': isReserved(cons) }"
                      >
                        <template #prepend>
                          <v-icon :color="isReserved(cons) ? 'success' : 'primary'" class="mr-3">
                            {{
                              isReserved(cons)
                                ? 'mdi-package-variant-closed-check'
                                : 'mdi-package-variant'
                            }}
                          </v-icon>
                        </template>

                        <div class="consommable-body">
                          <div class="consommable-main">
                            <v-list-item-title class="text-body-2 consommable-title">
                              {{ cons.designation }}
                            </v-list-item-title>
                            <span
                              v-if="isReserved(cons)"
                              class="consommable-status consommable-status--reserved"
                            >
                              <v-icon size="14">mdi-check-circle</v-icon>
                              Mis de côté
                            </span>
                            <v-tooltip v-else location="top">
                              <template #activator="{ props: tooltipProps }">
                                <span
                                  v-bind="tooltipProps"
                                  class="consommable-status consommable-status--pending consommable-status--icon"
                                >
                                  <v-icon size="14">mdi-clock-outline</v-icon>
                                </span>
                              </template>
                              À préparer
                            </v-tooltip>
                          </div>
                          <v-list-item-subtitle class="text-caption consommable-meta">
                            Quantité demandée : {{ cons.quantite }}
                          </v-list-item-subtitle>
                          <div
                            v-if="isReserved(cons) && getReservationEntries(cons).length > 0"
                            class="reservation-list"
                          >
                            <v-chip
                              v-for="reservation in getReservationEntries(cons)"
                              :key="`${cons.consommable}-${reservation.magasin_id}`"
                              size="x-small"
                              color="success"
                              variant="tonal"
                            >
                              {{ reservation.magasin_nom }} : {{ reservation.quantite }}
                            </v-chip>
                          </div>
                        </div>

                        <template #append>
                          <v-tooltip v-if="!isReserved(cons)" location="top">
                            <template #activator="{ props: tooltipProps }">
                              <span v-bind="tooltipProps" class="d-inline-flex">
                                <v-btn
                                  color="primary"
                                  size="small"
                                  variant="flat"
                                  :disabled="isDistributeDisabled(cons)"
                                  :loading="distributingId === `${bt.id}-${cons.consommable}`"
                                  @click="requestDistribute(bt, cons)"
                                >
                                  <v-icon size="18" class="mr-1">mdi-package-variant-closed</v-icon>
                                  Mettre de côté
                                </v-btn>
                              </span>
                            </template>
                            {{ getConsommableStockTooltip(cons) }}
                          </v-tooltip>
                          <v-tooltip v-else location="top">
                            <template #activator="{ props: tooltipProps }">
                              <v-btn
                                v-bind="tooltipProps"
                                icon
                                size="small"
                                variant="text"
                                class="stock-icon-button"
                                :loading="distributingId === `${bt.id}-${cons.consommable}`"
                                @click="requestDistribute(bt, cons)"
                              >
                                <v-icon size="18">mdi-pencil</v-icon>
                              </v-btn>
                            </template>
                            Modifier la mise de côté
                          </v-tooltip>
                        </template>
                      </v-list-item>
                    </v-list>

                    <div class="d-flex justify-end mt-3 pt-3 border-t">
                      <v-btn
                        color="primary"
                        variant="flat"
                        size="small"
                        :loading="distributingAll === bt.id"
                        @click="requestReserveAll(bt)"
                      >
                        <v-icon size="18" class="mr-1">mdi-check-all</v-icon>
                        Tout mettre de côté
                      </v-btn>
                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
            </div>
          </v-expand-transition>
        </div>

        <div v-if="reservedBons.length > 0" class="bt-section">
          <button type="button" class="section-toggle" @click="toggleSection('reserved')">
            <div class="section-toggle-content">
              <div class="section-title mb-0">Mis de côté</div>
              <v-chip size="small" color="success" variant="tonal">
                {{ reservedBons.length }} BT
              </v-chip>
            </div>
            <v-icon size="20" class="section-toggle-icon">
              {{ isSectionCollapsed('reserved') ? 'mdi-chevron-down' : 'mdi-chevron-up' }}
            </v-icon>
          </button>

          <v-expand-transition>
            <div v-show="!isSectionCollapsed('reserved')">
              <v-expansion-panels variant="accordion">
                <v-expansion-panel
                  v-for="bt in reservedBons"
                  :key="bt.id"
                  class="bt-item mb-2"
                  elevation="0"
                >
                  <v-expansion-panel-title class="py-3">
                    <v-row no-gutters align="center" class="w-100">
                      <v-col cols="8" class="d-flex align-center">
                        <v-icon color="success" size="20" class="mr-3">mdi-check-circle</v-icon>
                        <div class="bt-info">
                          <span class="bt-name">{{ bt.nom }}</span>
                          <span class="bt-date">Date : {{ formatDate(bt.date_assignation) }}</span>
                        </div>
                      </v-col>
                      <v-col cols="4" class="text-right">
                        <v-chip size="small" color="success" variant="tonal"> Mis de côté </v-chip>
                      </v-col>
                    </v-row>
                  </v-expansion-panel-title>

                  <v-expansion-panel-text>
                    <v-list density="compact" class="py-0">
                      <v-list-item
                        v-for="cons in getAllConsommables(bt)"
                        :key="cons.consommable"
                        class="consommable-item px-0"
                      >
                        <template #prepend>
                          <v-icon class="mr-3 stock-muted-icon">mdi-package-variant</v-icon>
                        </template>
                        <div class="consommable-body">
                          <div class="consommable-main">
                            <v-list-item-title class="text-body-2 consommable-title">
                              {{ cons.designation }}
                            </v-list-item-title>
                            <span class="consommable-status consommable-status--reserved">
                              <v-icon size="14">mdi-check-circle</v-icon>
                              Mis de côté
                            </span>
                          </div>
                          <v-list-item-subtitle class="text-caption consommable-meta">
                            Quantité demandée : {{ cons.quantite }}
                          </v-list-item-subtitle>
                          <div
                            v-if="getReservationEntries(cons).length > 0"
                            class="reservation-list"
                          >
                            <v-chip
                              v-for="reservation in getReservationEntries(cons)"
                              :key="`${cons.consommable}-${reservation.magasin_id}`"
                              size="x-small"
                              color="success"
                              variant="tonal"
                            >
                              {{ reservation.magasin_nom }} : {{ reservation.quantite }}
                            </v-chip>
                          </div>
                        </div>
                        <template #append>
                          <v-tooltip location="top">
                            <template #activator="{ props: tooltipProps }">
                              <v-btn
                                v-bind="tooltipProps"
                                icon
                                size="small"
                                variant="text"
                                class="stock-icon-button"
                                :loading="distributingId === `${bt.id}-${cons.consommable}`"
                                @click="requestDistribute(bt, cons)"
                              >
                                <v-icon size="18">mdi-pencil</v-icon>
                              </v-btn>
                            </template>
                            Modifier la mise de côté
                          </v-tooltip>
                        </template>
                      </v-list-item>
                    </v-list>
                    <div class="d-flex justify-end mt-3 pt-3 border-t ga-2">
                      <v-btn
                        color="error"
                        variant="outlined"
                        size="small"
                        @click="requestCancelReserve(bt)"
                      >
                        <v-icon size="18" class="mr-1">mdi-close</v-icon>
                        Annuler
                      </v-btn>
                      <v-btn
                        color="success"
                        variant="flat"
                        size="small"
                        @click="requestSetRecupere(bt)"
                      >
                        <v-icon size="18" class="mr-1">mdi-check</v-icon>
                        Valider le retrait
                      </v-btn>
                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
            </div>
          </v-expand-transition>
        </div>

        <div v-if="recoveredBons.length > 0" class="bt-section">
          <button type="button" class="section-toggle" @click="toggleSection('recovered')">
            <div class="section-toggle-content">
              <div class="section-title mb-0">Récupérés</div>
              <v-chip size="small" color="success" variant="tonal">
                {{ recoveredBons.length }} BT
              </v-chip>
            </div>
            <v-icon size="20" class="section-toggle-icon">
              {{ isSectionCollapsed('recovered') ? 'mdi-chevron-down' : 'mdi-chevron-up' }}
            </v-icon>
          </button>

          <v-expand-transition>
            <div v-show="!isSectionCollapsed('recovered')">
              <v-expansion-panels variant="accordion">
                <v-expansion-panel
                  v-for="bt in recoveredBons"
                  :key="bt.id"
                  class="bt-item mb-2"
                  elevation="0"
                >
                  <v-expansion-panel-title class="py-3">
                    <v-row no-gutters align="center" class="w-100">
                      <v-col cols="8" class="d-flex align-center">
                        <v-icon color="success" size="20" class="mr-3">mdi-check-circle</v-icon>
                        <div class="bt-info">
                          <span class="bt-name">{{ bt.nom }}</span>
                          <span class="bt-date">Date : {{ formatDate(bt.date_assignation) }}</span>
                        </div>
                      </v-col>
                      <v-col cols="4" class="text-right">
                        <v-chip size="small" color="success" variant="tonal">
                          Pièces récupérées
                        </v-chip>
                      </v-col>
                    </v-row>
                  </v-expansion-panel-title>

                  <v-expansion-panel-text>
                    <v-list density="compact" class="py-0">
                      <v-list-item
                        v-for="cons in getAllConsommables(bt)"
                        :key="cons.consommable"
                        class="consommable-item px-0"
                      >
                        <template #prepend>
                          <v-icon class="mr-3 stock-muted-icon">mdi-package-variant</v-icon>
                        </template>

                        <v-list-item-title class="text-body-2">
                          {{ cons.designation }}
                        </v-list-item-title>
                        <v-list-item-subtitle class="text-caption">
                          Quantité demandée : {{ cons.quantite }}
                        </v-list-item-subtitle>
                        <div v-if="getReservationEntries(cons).length > 0" class="reservation-list">
                          <v-chip
                            v-for="reservation in getReservationEntries(cons)"
                            :key="`${cons.consommable}-${reservation.magasin_id}`"
                            size="x-small"
                            color="success"
                            variant="tonal"
                          >
                            {{ reservation.magasin_nom }} : {{ reservation.quantite }}
                          </v-chip>
                        </div>
                        <template #append>
                          <v-tooltip location="top">
                            <template #activator="{ props: tooltipProps }">
                              <v-btn
                                v-bind="tooltipProps"
                                icon
                                size="small"
                                variant="text"
                                class="stock-icon-button"
                                :loading="distributingId === `${bt.id}-${cons.consommable}`"
                                @click="requestDistribute(bt, cons)"
                              >
                                <v-icon size="18">mdi-pencil</v-icon>
                              </v-btn>
                            </template>
                            Modifier la mise de côté
                          </v-tooltip>
                        </template>
                      </v-list-item>
                    </v-list>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
            </div>
          </v-expand-transition>
        </div>

        <ServerPaginationControls
          :page="currentPage"
          :page-size="pageSize"
          :page-count="totalPages"
          :total-items="totalItems"
          item-label-singular="BT"
          item-label-plural="BT"
          @update:page="currentPage = $event"
          @update:page-size="pageSize = $event"
        />
      </div>
    </v-card-text>
  </v-card>

  <ConfirmationModal
    v-model="confirmDialog"
    type="info"
    title="Confirmer la mise de côté"
    message="Êtes-vous sûr de vouloir mettre ce consommable de côté ?"
    confirm-text="Mettre de côté"
    confirm-icon="mdi-check"
    :loading="confirmLoading"
    @confirm="confirmDistribute"
    @cancel="cancelDistributeConfirmation"
  />

  <ConfirmationModal
    v-model="confirmCancelDialog"
    type="error"
    title="Confirmer l'annulation"
    message="Êtes-vous sûr de vouloir annuler la mise de côté pour ce BT ?"
    confirm-text="Annuler"
    confirm-icon="mdi-close"
    :loading="confirmCancelLoading"
    @confirm="confirmCancelReserve"
    @cancel="confirmCancelDialog = false"
  />

  <ConfirmationModal
    v-model="confirmRecupereDialog"
    type="success"
    title="Confirmer la récupération"
    message="Êtes-vous sûr de vouloir valider la récupération de ce BT ?"
    confirm-text="Valider"
    confirm-icon="mdi-check"
    :loading="confirmRecupereLoading"
    @confirm="confirmSetRecupere"
    @cancel="confirmRecupereDialog = false"
  />

  <v-dialog v-model="bulkReserveDialog" max-width="720">
    <v-card class="rounded-xl stock-dialog-card">
      <v-card-title class="pa-4 pb-2 stock-dialog-title">
        Choisir un magasin pour chaque pièce
      </v-card-title>
      <v-card-subtitle class="px-4 pb-0 text-caption stock-subtitle">
        Le premier magasin disponible est présélectionné. Vous pouvez le modifier avant de
        confirmer.
      </v-card-subtitle>
      <v-card-text class="pa-4 stock-dialog-body">
        <div class="bulk-reserve-list">
          <div v-for="item in bulkReserveItems" :key="item.consommableId" class="bulk-reserve-item">
            <div class="bulk-reserve-item__header">
              <span class="bulk-reserve-item__title">{{ item.designation }}</span>
              <v-chip size="x-small" color="info" variant="tonal">
                Quantité demandée : {{ item.quantite }}
              </v-chip>
            </div>

            <v-select
              v-model="item.magasinId"
              :items="item.magasins"
              item-title="label"
              item-value="id"
              label="Magasin"
              variant="outlined"
              density="compact"
              hide-details
            />
          </div>
        </div>
      </v-card-text>
      <v-card-actions class="pa-4 pt-0 d-flex justify-end ga-2 stock-dialog-actions">
        <v-btn variant="outlined" @click="cancelBulkReserve"> Annuler </v-btn>
        <v-btn
          color="primary"
          :disabled="!canConfirmBulkReserve"
          :loading="bulkReserveLoading"
          @click="confirmBulkReserve"
        >
          Tout mettre de côté
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <v-dialog v-model="magasinDialog" max-width="760">
    <v-card class="rounded-xl magasin-dialog-card stock-dialog-card">
      <v-card-title class="pa-5 pb-2 stock-dialog-title"> Ajuster la mise de côté </v-card-title>
      <v-card-subtitle
        v-if="magasinPendingAction.cons"
        class="px-5 pb-0 text-body-2 magasin-dialog-subtitle"
      >
        {{ magasinPendingAction.cons.designation }} - Quantité demandée :
        {{ magasinPendingAction.cons.quantite }}
      </v-card-subtitle>
      <v-card-text class="pa-5 pt-4 stock-dialog-body">
        <div class="magasin-summary mb-5">
          <v-chip size="small" color="info" variant="tonal">
            Demande : {{ magasinNeededQuantity }}
          </v-chip>
          <v-chip size="small" color="primary" variant="tonal">
            Selectionne : {{ magasinAllocatedQuantity }}
          </v-chip>
          <v-chip
            size="small"
            :color="magasinRemainingQuantity === 0 ? 'success' : 'warning'"
            variant="tonal"
          >
            Reste : {{ magasinRemainingQuantity }}
          </v-chip>
        </div>

        <div class="magasin-allocation-list">
          <div
            v-for="magasin in magasinAllocations"
            :key="magasin.id"
            class="magasin-allocation-item"
          >
            <div class="magasin-allocation-item__header">
              <span class="magasin-allocation-item__title">{{ magasin.nom }}</span>
              <v-chip size="x-small" class="stock-neutral-chip" variant="tonal">
                Disponible : {{ magasin.quantite }}
              </v-chip>
            </div>

            <v-text-field
              :model-value="magasin.quantiteSelectionnee"
              type="number"
              min="0"
              :max="magasin.quantite"
              label="Quantite a prendre"
              variant="outlined"
              density="compact"
              hide-details
              @update:model-value="updateMagasinAllocation(magasin.id, $event)"
            />
          </div>
        </div>
      </v-card-text>
      <v-card-actions class="magasin-dialog-actions pa-5 pt-0">
        <v-btn
          v-if="isEditingReservedCons"
          color="error"
          variant="outlined"
          :loading="
            distributingId ===
            `${magasinPendingAction.bt?.id}-${magasinPendingAction.cons?.consommable}`
          "
          @click="cancelSingleReserveFromModal"
        >
          Annuler cette mise de cote
        </v-btn>
        <v-btn variant="text" @click="resetMagasinSelectionState">Fermer</v-btn>
        <v-btn
          color="primary"
          size="large"
          :disabled="!canSubmitMagasinSelection"
          @click="confirmMagasinSelection"
        >
          Confirmer
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <v-dialog v-model="stockIssueDialog" max-width="560">
    <v-card class="rounded-xl stock-dialog-card">
      <v-card-title class="pa-4 pb-2 d-flex align-center stock-dialog-title">
        <v-icon color="warning" size="22" class="mr-2">mdi-alert-circle</v-icon>
        Stock insuffisant
      </v-card-title>
      <v-card-subtitle class="px-4 pb-2 text-caption stock-subtitle">
        {{ stockIssueMessage || 'Impossible de mettre de côté les pièces suivantes' }}
      </v-card-subtitle>
      <v-card-text class="pa-4 pt-2 stock-dialog-body">
        <v-list density="compact" class="py-0 stock-issue-list">
          <v-list-item
            v-for="(item, index) in stockIssueItems"
            :key="`${item.consommable_id}-${item.magasin_id || 'global'}-${index}`"
            class="px-0 stock-issue-item"
          >
            <v-list-item-title class="text-body-2 d-flex align-center">
              <v-icon size="18" class="mr-2 stock-muted-icon">mdi-package-variant</v-icon>
              {{ item.designation || 'Consommable #' + item.consommable_id }}
            </v-list-item-title>
            <v-list-item-subtitle class="text-caption d-flex align-center ga-2">
              <v-chip size="x-small" color="error" variant="tonal">
                Besoin : {{ item.needed }}
              </v-chip>
              <v-chip size="x-small" color="warning" variant="tonal">
                Disponible : {{ item.available }}
              </v-chip>
              <v-chip
                v-if="item.magasin_nom"
                size="x-small"
                class="stock-neutral-chip"
                variant="tonal"
              >
                Magasin : {{ item.magasin_nom }}
              </v-chip>
            </v-list-item-subtitle>
          </v-list-item>
        </v-list>
      </v-card-text>
      <v-card-actions class="pa-4 pt-0 d-flex justify-end stock-dialog-actions">
        <v-btn variant="outlined" @click="stockIssueDialog = false">Fermer</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
  import { computed, onMounted, ref, watch } from 'vue'
  import ServerPaginationControls from '@/components/common/ServerPaginationControls.vue'
  import { useApi } from '@/composables/useApi'
  import { usePaginatedList } from '@/composables/usePaginatedList'
  import { API_BASE_URL } from '@/utils/constants'
  import ConfirmationModal from '@/components/common/ConfirmationModal.vue'

  defineProps({
    consommables: {
      type: Array,
      default: () => [],
    },
  })

  const api = useApi(API_BASE_URL)
  const listApi = useApi(API_BASE_URL)
  const emit = defineEmits(['count-updated', 'counts-updated', 'stock-updated'])

  const {
    items: bonsTravail,
    currentPage,
    pageSize,
    totalItems,
    totalPages,
    searchQuery,
    loading,
    extra,
    fetchPage: fetchBonsTravail,
    handleSearch,
  } = usePaginatedList({
    api: listApi,
    endpoint: 'bons-travail/list_stock/',
    initialPageSize: 10,
  })

  const distributingId = ref(null)
  const distributingAll = ref(null)
  const confirmDialog = ref(false)
  const confirmLoading = ref(false)
  const pendingAction = ref({ bt: null, cons: null, magasinId: null, repartition: [] })
  const confirmCancelDialog = ref(false)
  const confirmCancelLoading = ref(false)
  const pendingCancelBt = ref(null)
  const confirmRecupereDialog = ref(false)
  const confirmRecupereLoading = ref(false)
  const pendingRecupereBt = ref(null)
  const stockError = ref('')
  const bulkReserveDialog = ref(false)
  const bulkReserveLoading = ref(false)
  const bulkReserveBt = ref(null)
  const bulkReserveItems = ref([])
  const magasinDialog = ref(false)
  const magasinOptions = ref([])
  const magasinAllocations = ref([])
  const magasinPendingAction = ref({ bt: null, cons: null })
  const stockIssueDialog = ref(false)
  const stockIssueItems = ref([])
  const stockIssueMessage = ref('')
  const collapsedSections = ref({
    pending: false,
    reserved: false,
    recovered: false,
  })

  const searchInput = computed({
    get: () => searchQuery.value,
    set: (value) => handleSearch(value),
  })

  const summary = computed(() => extra.value?.summary || {})
  const pendingCount = computed(() => Number(summary.value.pending_count || 0))
  const reservedCount = computed(() => Number(summary.value.reserved_count || 0))
  const recoveredCount = computed(() => Number(summary.value.recovered_count || 0))

  const consommableStockMap = computed(() => {
    const consumables = bonsTravail.value.flatMap((bt) => bt.consommables || [])
    return consumables.reduce((map, consommable) => {
      map.set(Number(consommable.consommable), Number(consommable.stock_total ?? 0))
      return map
    }, new Map())
  })

  const consommableDetailsMap = computed(() => {
    const consumables = bonsTravail.value.flatMap((bt) => bt.consommables || [])
    return consumables.reduce((map, consommable) => {
      map.set(Number(consommable.consommable), {
        id: consommable.consommable,
        stocks: consommable.stocks || [],
        quantite_totale: consommable.stock_total ?? 0,
      })
      return map
    }, new Map())
  })

  const canConfirmBulkReserve = computed(() => {
    return (
      bulkReserveItems.value.length > 0 &&
      bulkReserveItems.value.every(
        (item) => item.magasinId !== null && item.magasinId !== undefined
      )
    )
  })

  const magasinNeededQuantity = computed(() => {
    return Number(magasinPendingAction.value.cons?.quantite ?? 0)
  })

  const magasinAllocatedQuantity = computed(() => {
    return magasinAllocations.value.reduce(
      (total, magasin) => total + Number(magasin.quantiteSelectionnee ?? 0),
      0
    )
  })

  const magasinRemainingQuantity = computed(() => {
    return Math.max(magasinNeededQuantity.value - magasinAllocatedQuantity.value, 0)
  })

  const canSubmitMagasinSelection = computed(() => {
    return (
      magasinNeededQuantity.value > 0 &&
      magasinAllocatedQuantity.value === magasinNeededQuantity.value
    )
  })

  const isEditingReservedCons = computed(() => {
    return isReserved(magasinPendingAction.value.cons)
  })

  // Helpers locaux pour garder l'UI synchronisee sans recharger les BT
  const updateBt = (btId, updater) => {
    const btIndex = bonsTravail.value.findIndex((b) => b.id === btId)
    if (btIndex !== -1) {
      updater(bonsTravail.value[btIndex])
    }
  }

  const updateConsommable = (btId, consommableId, updater) => {
    updateBt(btId, (bt) => {
      const consIndex = bt.consommables.findIndex((c) => c.consommable === consommableId)
      if (consIndex !== -1) {
        updater(bt.consommables[consIndex], bt)
      }
    })
  }

  const setConsommableReservationState = (
    cons,
    { reserved, magasinId = null, dateDistribution = null, reservations = [] }
  ) => {
    cons.distribue = reserved
    cons.date_distribution = reserved ? dateDistribution || new Date().toISOString() : null
    cons.magasin_reserve = reserved ? (magasinId ?? cons.magasin_reserve ?? null) : null
    cons.magasins_reserves = reserved ? reservations : []
  }

  const getReservationEntries = (cons) => {
    if (Array.isArray(cons?.magasins_reserves) && cons.magasins_reserves.length > 0) {
      return cons.magasins_reserves.map((reservation) => ({
        magasin_id: reservation.magasin_id,
        magasin_nom: reservation.magasin_nom,
        quantite: Number(reservation.quantite ?? 0),
      }))
    }

    if (cons?.magasin_reserve) {
      const stock = getConsommableStocks(cons).find(
        (item) => Number(item.magasin) === Number(cons.magasin_reserve)
      )

      return [
        {
          magasin_id: Number(cons.magasin_reserve),
          magasin_nom: stock?.magasin_nom ?? `Magasin #${cons.magasin_reserve}`,
          quantite: Number(cons.quantite ?? 0),
        },
      ]
    }

    return []
  }

  const resetMagasinSelectionState = () => {
    magasinDialog.value = false
    magasinOptions.value = []
    magasinAllocations.value = []
    magasinPendingAction.value = { bt: null, cons: null }
  }

  const resetBulkReserveState = () => {
    bulkReserveDialog.value = false
    bulkReserveBt.value = null
    bulkReserveItems.value = []
  }

  // Gestion des erreurs stock (modal ou message simple)
  const clearStockIssue = () => {
    stockIssueItems.value = []
    stockIssueMessage.value = ''
  }

  const clearStockFeedback = () => {
    stockError.value = ''
    clearStockIssue()
  }

  const isSectionCollapsed = (section) => {
    return Boolean(collapsedSections.value[section])
  }

  const toggleSection = (section) => {
    collapsedSections.value[section] = !collapsedSections.value[section]
  }

  const getConsommableTotalStock = (consommable) => {
    return consommableStockMap.value.get(Number(consommable?.consommable)) ?? 0
  }

  const getConsommableStocks = (consommable) => {
    const details = consommableDetailsMap.value.get(Number(consommable?.consommable))
    return Array.isArray(details?.stocks) ? details.stocks : []
  }

  const getConsommableMaxStock = (consommable) => {
    const stocks = getConsommableStocks(consommable)

    return stocks.reduce((max, stock) => Math.max(max, Number(stock?.quantite ?? 0)), 0)
  }

  const getEligibleMagasins = (consommable) => {
    const needed = Number(consommable?.quantite ?? 0)

    return getConsommableStocks(consommable)
      .map((stock) => ({
        id: stock.magasin,
        nom: stock.magasin_nom,
        quantite: Number(stock.quantite ?? 0),
      }))
      .filter((stock) => stock.quantite >= needed)
  }

  const getAvailableMagasins = (consommable) => {
    return getConsommableStocks(consommable)
      .map((stock) => ({
        id: stock.magasin,
        nom: stock.magasin_nom,
        quantite: Number(stock.quantite ?? 0),
      }))
      .filter((stock) => stock.quantite > 0)
  }

  const getEditableMagasins = (consommable) => {
    const magasins = new Map()

    getAvailableMagasins(consommable).forEach((magasin) => {
      magasins.set(magasin.id, { ...magasin })
    })

    getReservationEntries(consommable).forEach((reservation) => {
      const existingMagasin = magasins.get(reservation.magasin_id)

      magasins.set(reservation.magasin_id, {
        id: reservation.magasin_id,
        nom: reservation.magasin_nom,
        quantite: Number(existingMagasin?.quantite ?? 0) + Number(reservation.quantite ?? 0),
      })
    })

    return Array.from(magasins.values())
  }

  const isDistributeDisabled = (consommable) => {
    return getConsommableTotalStock(consommable) <= 0
  }

  const getConsommableStockTooltip = (consommable) => {
    const totalStock = getConsommableTotalStock(consommable)
    const maxStock = getConsommableMaxStock(consommable)
    const needed = Number(consommable?.quantite ?? 0)

    if (totalStock <= 0) {
      return 'Aucun stock disponible.'
    }

    if (needed > 0 && totalStock >= needed && maxStock < needed) {
      return `Stock total disponible : ${totalStock}. Aucun magasin ne couvre seul la quantité demandée (${needed}).`
    }

    return `Stock total disponible : ${totalStock}`
  }

  const openStockIssue = (data, fallback) => {
    stockIssueItems.value = data?.insuffisants || []
    stockIssueMessage.value = data?.error || fallback
    stockIssueDialog.value = true
  }

  const openMagasinSelection = (data, bt, cons) => {
    const options = data?.magasins || getEditableMagasins(cons)
    const needed = Number(data?.needed ?? cons?.quantite ?? 0)
    const existingReservations = getReservationEntries(cons)

    magasinOptions.value = options
    magasinAllocations.value = buildDefaultMagasinAllocations(options, needed, existingReservations)
    magasinPendingAction.value = { bt, cons }
    magasinDialog.value = true
  }

  const buildDefaultMagasinAllocations = (options, needed, existingReservations = []) => {
    const reservationMap = existingReservations.reduce((map, reservation) => {
      map.set(Number(reservation.magasin_id), Number(reservation.quantite ?? 0))
      return map
    }, new Map())

    if (reservationMap.size > 0) {
      return options.map((magasin) => ({
        ...magasin,
        quantite: Number(magasin.quantite ?? 0),
        quantiteSelectionnee: reservationMap.get(Number(magasin.id)) ?? 0,
      }))
    }

    let remaining = Number(needed ?? 0)

    return options.map((magasin) => {
      const quantiteDisponible = Number(magasin.quantite ?? 0)
      const quantiteSelectionnee = Math.min(remaining, quantiteDisponible)

      remaining -= quantiteSelectionnee

      return {
        ...magasin,
        quantite: quantiteDisponible,
        quantiteSelectionnee,
      }
    })
  }

  const updateMagasinAllocation = (magasinId, value) => {
    const parsedValue = Number.parseInt(value, 10)

    magasinAllocations.value = magasinAllocations.value.map((magasin) => {
      if (magasin.id !== magasinId) {
        return magasin
      }

      const quantiteSelectionnee = Number.isNaN(parsedValue)
        ? 0
        : Math.min(Math.max(parsedValue, 0), magasin.quantite)

      return {
        ...magasin,
        quantiteSelectionnee,
      }
    })
  }

  const buildBulkReserveItems = (bt) => {
    const items = []
    const insuffisants = []

    getPendingConsommables(bt).forEach((consommable) => {
      const eligibleMagasins = getEligibleMagasins(consommable)

      if (eligibleMagasins.length === 0) {
        insuffisants.push(
          normalizeStockIssueItem({ available: getConsommableTotalStock(consommable) }, consommable)
        )
        return
      }

      items.push({
        consommableId: consommable.consommable,
        designation: consommable.designation,
        quantite: Number(consommable.quantite ?? 0),
        magasinId: eligibleMagasins[0].id,
        magasins: eligibleMagasins.map((magasin) => ({
          ...magasin,
          label: `${magasin.nom} (disponible : ${magasin.quantite})`,
        })),
      })
    })

    return { items, insuffisants }
  }
  // Filtrer les BT qui ont des consommables non distribués
  const pendingBons = computed(() => {
    return bonsTravail.value.filter((bt) => {
      const hasConsommables = (bt.consommables || []).length > 0
      return hasConsommables && bt.consommables.some((c) => !isReserved(c))
    })
  })

  const reservedBons = computed(() => {
    return bonsTravail.value.filter((bt) => {
      const hasConsommables = (bt.consommables || []).length > 0
      return hasConsommables && bt.consommables.every((c) => isReserved(c)) && !bt.pieces_recuperees
    })
  })

  const recoveredBons = computed(() => {
    return bonsTravail.value.filter((bt) => bt.pieces_recuperees === true)
  })

  // Émettre les compteurs globaux retournés par l'API paginée
  watch(
    [pendingCount, reservedCount, recoveredCount],
    ([pending, reserved, recovered]) => {
      emit('count-updated', pending)
      emit('counts-updated', { pending, reserved, recovered })
    },
    { immediate: true }
  )

  // Récupérer les consommables non distribués d'un BT
  const getPendingConsommables = (bt) => {
    return bt.consommables?.filter((c) => !isReserved(c)) || []
  }

  const getReservedConsommables = (bt) => {
    return bt.consommables?.filter((c) => isReserved(c)) || []
  }

  const getAllConsommables = (bt) => {
    return bt.consommables || []
  }

  const getSortedConsommables = (bt) => {
    return [...getPendingConsommables(bt), ...getReservedConsommables(bt)]
  }

  const getTotalCount = (bt) => {
    return getAllConsommables(bt).length
  }

  const getReservedCount = (bt) => {
    return getReservedConsommables(bt).length
  }

  const getBtById = (btId) => {
    return bonsTravail.value.find((bt) => bt.id === btId) || null
  }

  const syncAfterServerError = async (btId) => {
    await fetchBonsTravail()
    emit('stock-updated')
    return getBtById(btId)
  }

  // Compat backend : le champ "distribue" correspond ici au statut "mis de cote".
  const isReserved = (cons) => {
    return cons?.distribue === true || cons?.distribue === 1 || cons?.distribue === 'true'
  }

  const requestDistribute = (bt, cons) => {
    clearStockFeedback()

    const magasinsEditables = getEditableMagasins(cons)
    const totalStock = magasinsEditables.reduce(
      (total, magasin) => total + Number(magasin.quantite ?? 0),
      0
    )
    const needed = Number(cons?.quantite ?? 0)

    if (totalStock >= needed) {
      openMagasinSelection(
        {
          magasins: magasinsEditables,
          needed,
        },
        bt,
        cons
      )
      return
    }

    openStockIssue(
      {
        error: getConsommableStockTooltip(cons),
        insuffisants: [
          normalizeStockIssueItem({ available: getConsommableTotalStock(cons) }, cons),
        ],
      },
      'Stock insuffisant pour ce consommable.'
    )
  }

  const confirmDistribute = async () => {
    if (!pendingAction.value.bt || !pendingAction.value.cons) {
      confirmDialog.value = false
      return
    }
    confirmLoading.value = true
    try {
      await handleDistribute(pendingAction.value.bt, pendingAction.value.cons, {
        magasinId: pendingAction.value.magasinId,
        repartition: pendingAction.value.repartition,
      })
    } finally {
      confirmLoading.value = false
      confirmDialog.value = false
      pendingAction.value = { bt: null, cons: null, magasinId: null, repartition: [] }
    }
  }

  const cancelDistributeConfirmation = () => {
    confirmDialog.value = false
    pendingAction.value = { bt: null, cons: null, magasinId: null, repartition: [] }
  }

  const requestReserveAll = (bt) => {
    clearStockFeedback()

    const { items, insuffisants } = buildBulkReserveItems(bt)

    if (insuffisants.length > 0) {
      openStockIssue(
        {
          insuffisants,
          error: buildBulkStockIssueMessage(insuffisants),
        },
        'Stock insuffisant pour ce BT.'
      )
      return
    }

    if (items.length === 0) {
      return
    }

    bulkReserveBt.value = bt
    bulkReserveItems.value = items
    bulkReserveDialog.value = true
  }

  const cancelBulkReserve = () => {
    resetBulkReserveState()
  }

  const confirmBulkReserve = async () => {
    if (!bulkReserveBt.value || !canConfirmBulkReserve.value) {
      resetBulkReserveState()
      return
    }

    bulkReserveLoading.value = true
    try {
      const magasinSelections = bulkReserveItems.value.reduce((selections, item) => {
        selections[item.consommableId] = item.magasinId
        return selections
      }, {})

      await handleDistributeAll(bulkReserveBt.value, magasinSelections)
    } finally {
      bulkReserveLoading.value = false
      resetBulkReserveState()
    }
  }

  const confirmMagasinSelection = async () => {
    if (
      !magasinPendingAction.value.bt ||
      !magasinPendingAction.value.cons ||
      !canSubmitMagasinSelection.value
    ) {
      resetMagasinSelectionState()
      return
    }

    const repartition = magasinAllocations.value
      .filter((magasin) => Number(magasin.quantiteSelectionnee ?? 0) > 0)
      .map((magasin) => ({
        magasin_id: magasin.id,
        quantite: Number(magasin.quantiteSelectionnee),
      }))

    pendingAction.value = {
      bt: magasinPendingAction.value.bt,
      cons: magasinPendingAction.value.cons,
      magasinId: repartition.length === 1 ? repartition[0].magasin_id : null,
      repartition,
    }
    confirmDialog.value = true
    resetMagasinSelectionState()
  }

  const handleCancelSingleReserve = async (bt, consommable) => {
    distributingId.value = `${bt.id}-${consommable.consommable}`
    try {
      clearStockFeedback()
      await api.patch(`bons-travail/${bt.id}/update_consommable_distribution/`, {
        consommable_id: consommable.consommable,
        distribue: false,
      })

      updateConsommable(bt.id, consommable.consommable, (localCons) => {
        setConsommableReservationState(localCons, { reserved: false })
      })

      resetMagasinSelectionState()
      emit('stock-updated')
    } catch (error) {
      stockError.value =
        error?.response?.data?.error ||
        'Une erreur est survenue lors de l annulation de cette mise de cote.'
      console.error('Erreur annulation mise de cote unitaire:', error)
    } finally {
      distributingId.value = null
    }
  }

  const cancelSingleReserveFromModal = async () => {
    if (
      !magasinPendingAction.value.bt ||
      !magasinPendingAction.value.cons ||
      !isEditingReservedCons.value
    ) {
      resetMagasinSelectionState()
      return
    }

    await handleCancelSingleReserve(magasinPendingAction.value.bt, magasinPendingAction.value.cons)
  }

  const requestCancelReserve = (bt) => {
    pendingCancelBt.value = bt
    confirmCancelDialog.value = true
  }

  const confirmCancelReserve = async () => {
    if (!pendingCancelBt.value) {
      confirmCancelDialog.value = false
      return
    }
    confirmCancelLoading.value = true
    try {
      await handleCancelReserve(pendingCancelBt.value)
    } finally {
      confirmCancelLoading.value = false
      confirmCancelDialog.value = false
      pendingCancelBt.value = null
    }
  }

  const requestSetRecupere = (bt) => {
    pendingRecupereBt.value = bt
    confirmRecupereDialog.value = true
  }

  const confirmSetRecupere = async () => {
    if (!pendingRecupereBt.value) {
      confirmRecupereDialog.value = false
      return
    }
    confirmRecupereLoading.value = true
    try {
      await handleSetRecupere(pendingRecupereBt.value)
    } finally {
      confirmRecupereLoading.value = false
      confirmRecupereDialog.value = false
      pendingRecupereBt.value = null
    }
  }

  // Formater la date
  const formatDate = (dateString) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleDateString('fr-FR')
  }

  const normalizeStockIssueItem = (item, consommable) => {
    const stocks = Array.isArray(item?.stocks) ? item.stocks : []
    const available =
      item?.available ?? stocks.reduce((total, stock) => total + Number(stock.quantite || 0), 0)

    return {
      consommable_id: item?.consommable_id ?? consommable?.consommable ?? null,
      designation: item?.designation ?? consommable?.designation ?? null,
      needed: item?.needed ?? consommable?.quantite ?? 0,
      available,
      magasin_id: item?.magasin_id ?? null,
      magasin_nom: item?.magasin_nom ?? null,
    }
  }

  const buildBulkStockIssueMessage = (insuffisants) => {
    if (insuffisants.length > 1) {
      return 'Impossible de mettre de côté les pièces suivantes.'
    }
    if (insuffisants.length === 1) {
      return 'Impossible de mettre de côté la pièce suivante.'
    }
    return 'Impossible de mettre de côté tout le BT.'
  }

  // Distribuer un consommable
  const handleDistribute = async (bt, consommable, { magasinId = null, repartition = [] } = {}) => {
    distributingId.value = `${bt.id}-${consommable.consommable}`
    try {
      clearStockFeedback()
      const payload = {
        consommable_id: consommable.consommable,
        distribue: true,
      }

      if (Array.isArray(repartition) && repartition.length > 0) {
        payload.repartition = repartition
        if (repartition.length === 1) {
          payload.magasin_id = repartition[0].magasin_id
        }
      } else {
        payload.magasin_id = magasinId
      }

      const response = await api.patch(
        `bons-travail/${bt.id}/update_consommable_distribution/`,
        payload
      )
      // Mettre a jour localement
      updateConsommable(bt.id, consommable.consommable, (c) => {
        setConsommableReservationState(c, {
          reserved: true,
          magasinId: response?.magasin_reserve ?? magasinId,
          dateDistribution: response?.date_distribution,
          reservations: response?.magasins_reserves ?? repartition,
        })
      })
      emit('stock-updated')
    } catch (error) {
      if ((error?.response?.status ?? 0) >= 500) {
        const refreshedBt = await syncAfterServerError(bt.id)
        const refreshedConsommable = refreshedBt?.consommables?.find(
          (cons) => cons.consommable === consommable.consommable
        )

        if (refreshedConsommable && isReserved(refreshedConsommable)) {
          clearStockFeedback()
          return
        }
      }

      const data = error?.response?.data
      if (error?.response?.status === 409 && data?.needs_magasin_selection) {
        openMagasinSelection(data, bt, consommable)
        return
      }
      if (data?.insuffisants) {
        openStockIssue(data, 'Stock insuffisant pour ce consommable.')
      } else if (data?.error) {
        stockError.value = data.error
      } else {
        stockError.value = 'Une erreur est survenue lors de la mise de côté de ce consommable.'
      }
      console.error('Erreur distribution:', error)
    } finally {
      distributingId.value = null
    }
  }

  // Distribuer tous les consommables d'un BT
  const handleDistributeAll = async (bt, magasinSelections = {}) => {
    distributingAll.value = bt.id
    let hasPartialSuccess = false
    const insuffisants = []
    const otherErrors = []

    try {
      clearStockFeedback()
      const pendingConsommables = getPendingConsommables(bt)

      for (const cons of pendingConsommables) {
        const magasinId = magasinSelections[cons.consommable] ?? null

        try {
          const response = await api.patch(
            `bons-travail/${bt.id}/update_consommable_distribution/`,
            {
              consommable_id: cons.consommable,
              distribue: true,
              magasin_id: magasinId,
            }
          )
          hasPartialSuccess = true
          updateConsommable(bt.id, cons.consommable, (localCons) => {
            setConsommableReservationState(localCons, {
              reserved: true,
              magasinId: response?.magasin_reserve ?? magasinId,
              dateDistribution: response?.date_distribution,
            })
          })
        } catch (error) {
          const data = error?.response?.data

          if (error?.response?.status === 409 && data?.needs_magasin_selection) {
            otherErrors.push(`${cons.designation} : choix du magasin requis.`)
            continue
          }

          if (Array.isArray(data?.insuffisants) && data.insuffisants.length > 0) {
            insuffisants.push(
              ...data.insuffisants.map((item) => normalizeStockIssueItem(item, cons))
            )
            continue
          }

          if (data?.error) {
            otherErrors.push(`${cons.designation} : ${data.error}`)
            continue
          }

          otherErrors.push(`${cons.designation} : impossible de mettre de côté ce consommable.`)
        }
      }

      if (hasPartialSuccess) {
        emit('stock-updated')
      }

      if (insuffisants.length > 0) {
        openStockIssue(
          {
            insuffisants,
            error: buildBulkStockIssueMessage(insuffisants),
          },
          'Stock insuffisant pour ce BT.'
        )
        return
      }

      if (otherErrors.length > 0) {
        stockError.value = otherErrors.join(' ')
      }
    } finally {
      distributingAll.value = null
    }
  }

  const handleCancelReserve = async (bt) => {
    try {
      clearStockFeedback()
      await api.patch(`bons-travail/${bt.id}/cancel_mise_de_cote/`, {})
      updateBt(bt.id, (btLocal) => {
        btLocal.consommables.forEach((c) => {
          setConsommableReservationState(c, { reserved: false })
        })
        btLocal.pieces_recuperees = false
        btLocal.date_recuperation = null
      })
      emit('stock-updated')
    } catch (error) {
      if ((error?.response?.status ?? 0) >= 500) {
        const refreshedBt = await syncAfterServerError(bt.id)
        const consommables = refreshedBt?.consommables || []

        if (consommables.length > 0 && consommables.every((cons) => !isReserved(cons))) {
          clearStockFeedback()
          return
        }
      }

      stockError.value =
        error?.response?.data?.error ||
        'Une erreur est survenue lors de l’annulation de la mise de côté.'
      console.error('Erreur annulation mise de cote:', error)
    }
  }

  const handleSetRecupere = async (bt) => {
    try {
      clearStockFeedback()
      const response = await api.patch(`bons-travail/${bt.id}/set_recupere/`, { recupere: true })
      updateBt(bt.id, (btLocal) => {
        btLocal.pieces_recuperees = response?.pieces_recuperees ?? true
        btLocal.date_recuperation = response?.date_recuperation ?? new Date().toISOString()
      })
    } catch (error) {
      if ((error?.response?.status ?? 0) >= 500) {
        const refreshedBt = await syncAfterServerError(bt.id)

        if (refreshedBt?.pieces_recuperees) {
          clearStockFeedback()
          return
        }
      }

      stockError.value =
        error?.response?.data?.error || 'Une erreur est survenue lors de la validation du retrait.'
      console.error('Erreur validation recuperation:', error)
    }
  }
  onMounted(() => {
    fetchBonsTravail()
  })
</script>

<style scoped>
  .bt-list,
  .bt-section,
  .reservation-list,
  .magasin-summary,
  .magasin-dialog-actions,
  .stock-dialog-card,
  .stock-dialog-actions,
  .bulk-reserve-list,
  .magasin-allocation-list {
    --stock-border-color: rgba(var(--v-theme-on-surface), 0.12);
    --stock-divider-color: rgba(var(--v-theme-on-surface), 0.08);
    --stock-muted-color: rgba(var(--v-theme-on-surface), 0.68);
    --stock-soft-surface: rgba(var(--v-theme-on-surface), 0.03);
    --stock-hover-surface: rgba(var(--v-theme-primary), 0.06);
  }

  .stock-dialog-card {
    border: 1px solid var(--stock-border-color);
    box-shadow: 0 22px 50px rgba(10, 15, 30, 0.18);
    overflow: hidden;
  }

  .stock-dialog-title {
    color: rgba(var(--v-theme-on-surface), 0.96);
    font-weight: 600;
  }

  .stock-dialog-body {
    color: rgba(var(--v-theme-on-surface), 0.8);
  }

  .stock-dialog-actions {
    border-top: 1px solid var(--stock-divider-color);
  }

  .stock-dialog-card :deep(.v-field) {
    background: rgba(var(--v-theme-on-surface), 0.02);
  }

  .stock-dialog-card :deep(.v-list) {
    background: transparent;
  }

  .bt-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .bt-section {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .section-toggle {
    align-items: center;
    background: none;
    border: none;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    padding: 0;
    text-align: left;
    width: 100%;
  }

  .section-toggle-content {
    align-items: center;
    display: flex;
    gap: 8px;
  }

  .bt-title-metrics {
    display: inline-flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: flex-end;
  }

  .section-title {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--stock-muted-color);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .bt-item {
    border: 1px solid var(--stock-border-color);
    border-radius: 8px !important;
  }

  .bt-item:hover {
    border-color: rgba(var(--v-theme-primary), 0.4);
  }

  .bt-info {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .bt-name {
    font-size: 0.875rem;
    font-weight: 500;
    color: rgba(var(--v-theme-on-surface), 0.92);
    white-space: normal;
  }

  .bt-date {
    font-size: 0.75rem;
    color: var(--stock-muted-color);
  }

  .consommable-item {
    border-bottom: 1px solid var(--stock-divider-color);
    border-radius: 10px;
    margin-bottom: 6px;
    padding-inline: 8px !important;
  }

  .consommable-item:last-child {
    border-bottom: none;
    margin-bottom: 0;
  }

  .consommable-item--reserved {
    background-color: rgba(var(--v-theme-success), 0.08);
  }

  .consommable-item :deep(.v-list-item__content) {
    flex: 1 1 auto;
    min-width: 0;
  }

  .consommable-item :deep(.v-list-item__append) {
    margin-left: auto;
  }

  .consommable-body {
    display: flex;
    flex: 1 1 auto;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
  }

  .consommable-main {
    align-items: center;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .consommable-title {
    color: rgba(var(--v-theme-on-surface), 0.9);
    font-weight: 500;
  }

  .consommable-meta {
    color: var(--stock-muted-color);
  }

  .consommable-status {
    align-items: center;
    border-radius: 999px;
    display: inline-flex;
    font-size: 0.72rem;
    font-weight: 600;
    gap: 4px;
    line-height: 1;
    padding: 4px 8px;
  }

  .consommable-status--reserved {
    background: rgba(var(--v-theme-success), 0.14);
    color: rgb(var(--v-theme-success));
  }

  .consommable-status--pending {
    background: rgba(var(--v-theme-primary), 0.12);
    color: rgb(var(--v-theme-primary));
  }

  .consommable-status--icon {
    justify-content: center;
    min-width: 24px;
    padding: 4px 6px;
  }

  .reservation-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .magasin-dialog-card {
    overflow: hidden;
  }

  .stock-summary,
  .stock-subtitle,
  .magasin-dialog-subtitle,
  .section-toggle-icon,
  .stock-icon-button {
    color: var(--stock-muted-color) !important;
  }

  .stock-muted-icon {
    color: var(--stock-muted-color) !important;
  }

  .stock-neutral-chip {
    background: rgba(var(--v-theme-on-surface), 0.08) !important;
    color: var(--stock-muted-color) !important;
  }

  .magasin-dialog-actions {
    align-items: center;
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    justify-content: flex-end;
  }

  .bulk-reserve-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .bulk-reserve-item {
    background: var(--stock-soft-surface);
    border: 1px solid var(--stock-border-color);
    border-radius: 10px;
    padding: 12px;
  }

  .bulk-reserve-item__header {
    align-items: center;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: space-between;
    margin-bottom: 12px;
  }

  .bulk-reserve-item__title {
    color: rgba(var(--v-theme-on-surface), 0.9);
    font-size: 0.95rem;
    font-weight: 500;
  }

  .magasin-summary {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .magasin-allocation-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .magasin-allocation-item {
    background: var(--stock-soft-surface);
    border: 1px solid var(--stock-border-color);
    border-radius: 10px;
    padding: 14px;
  }

  .magasin-allocation-item__header {
    align-items: center;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: space-between;
    margin-bottom: 12px;
  }

  .magasin-allocation-item__title {
    color: rgba(var(--v-theme-on-surface), 0.9);
    font-size: 0.95rem;
    font-weight: 500;
  }

  @media (max-width: 600px) {
    .magasin-dialog-actions {
      justify-content: stretch;
    }

    .magasin-dialog-actions .v-btn {
      width: 100%;
    }
  }

  .stock-issue-item {
    border-bottom: 1px solid var(--stock-divider-color);
    padding-bottom: 8px;
    margin-bottom: 8px;
  }

  .stock-issue-list {
    background: transparent;
  }

  .stock-issue-item:last-child {
    border-bottom: none;
    padding-bottom: 0;
    margin-bottom: 0;
  }

  .border-t {
    border-top: 1px solid var(--stock-border-color);
  }

  @media (max-width: 960px) {
    .bt-title-metrics {
      justify-content: flex-start;
      margin-top: 8px;
    }
  }
</style>
