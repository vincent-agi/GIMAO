<template>
  <BaseDetailView
    :title="consumable?.designation"
    :subtitle="''"
    :data="consumable"
    :loading="loading"
    :breadcrumbs="breadcrumbs"
    show-back-button
  >
    <!-- Contenu Principal -->
    <template #default>
      <v-row>
        <!-- Info Consommable -->
        <v-col cols="12" md="4">
          <v-card class="mb-4">
            <v-card-title>Informations</v-card-title>
            <v-card-text>
              <div v-if="consumable?.lienImageConsommable" class="mb-4 text-center">
                <v-img :src="consumable.lienImageConsommable" max-height="200" contain></v-img>
              </div>
              <v-list density="compact">
                <v-list-item>
                  <v-list-item-title class="font-weight-bold">Désignation</v-list-item-title>
                  <v-list-item-subtitle>{{ consumable?.designation }}</v-list-item-subtitle>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title class="font-weight-bold">Seuil Stock Faible</v-list-item-title>
                  <v-list-item-subtitle>{{
                    consumable?.seuilStockFaible || '-'
                  }}</v-list-item-subtitle>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title class="font-weight-bold">Quantité en stock</v-list-item-title>
                  <v-list-item-subtitle>{{ consumable?.quantite_totale }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Stocks par Magasin -->
        <v-col cols="12" md="8">
          <v-card class="mb-4">
            <v-card-title class="d-flex flex-wrap align-center justify-space-between py-2 gap-2">
              <span>Stocks en Magasin</span>
              <v-btn
                v-if="consumable?.stocks?.length && store.getters.hasPermission('stock:transfer')"
                color="secondary"
                prepend-icon="mdi-transfer"
                size="small"
                variant="text"
                @click="showTransferDialog = true"
              >
                <span class="d-none d-sm-inline">Transférer</span>
              </v-btn>
            </v-card-title>
            <v-card-text>
              <v-data-table
                v-if="consumable?.stocks?.length"
                :headers="stockHeaders"
                :items="consumable.stocks.filter((stock) => !stock.quantite == 0)"
                class="elevation-1"
                hide-default-footer
                :items-per-page="-1"
                density="compact"
                mobile-breakpoint="sm"
              >
              </v-data-table>
              <v-alert v-else type="info" variant="tonal" class="mt-2">
                Aucun stock enregistré.
              </v-alert>
            </v-card-text>
          </v-card>

          <!-- Historique des Achats (Fournitures) -->
          <v-card>
            <v-card-title class="d-flex flex-wrap align-center justify-space-between py-2 gap-2">
              <span>Historique des Achats</span>
              <v-btn
                v-if="store.getters.hasPermission('stock:addPurchase')"
                color="primary"
                prepend-icon="mdi-plus"
                size="small"
                @click="showAddPurchaseDialog = true"
              >
                <span class="d-none d-sm-inline">Ajouter un achat</span>
                <span class="d-inline d-sm-none">Ajout</span>
              </v-btn>
            </v-card-title>
            <v-card-text>
              <v-data-table
                v-if="consumable?.fournitures?.length"
                :headers="purchaseHeaders"
                :items="formattedPurchases"
                class="elevation-1"
                :items-per-page="5"
                density="compact"
                mobile-breakpoint="0"
              >
                <template #[`item.date_reference_prix`]="{ item }">
                  {{ formatDate(item.date_reference_prix) }}
                </template>
                <template #[`item.prix_unitaire`]="{ item }">
                  {{ formatPrice(item.prix_unitaire) }}
                </template>
                <template #[`item.total`]="{ item }">
                  {{ formatPrice(item.total) }}
                </template>
              </v-data-table>
              <v-alert v-else type="info" variant="tonal" class="mt-2">
                Aucun historique d'achat.
              </v-alert>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Boutons flottants -->
      <div class="floating-buttons">
        <!-- Bouton archiver -->
        <v-btn
          v-if="consumable && !consumable.archive && store.getters.hasPermission('cons:archive')"
          color="warning"
          size="large"
          icon
          elevation="4"
          @click="showArchiveDialog = true"
        >
          <v-icon>mdi-archive-arrow-down</v-icon>
          <v-tooltip activator="parent" location="left">Archiver</v-tooltip>
        </v-btn>

        <!-- Bouton modifier -->
        <v-btn
          v-if="consumable && store.getters.hasPermission('cons:edit')"
          color="primary"
          size="large"
          icon
          elevation="4"
          @click="goToEditConsumable"
        >
          <v-icon>mdi-pencil</v-icon>
          <v-tooltip activator="parent" location="left">Modifier</v-tooltip>
        </v-btn>
      </div>

      <!-- Dialog de confirmation d'archivage -->
      <ConfirmationModal
        v-model="showArchiveDialog"
        title="Confirmer l'archivage"
        message="Êtes-vous sûr de vouloir archiver le consommable ?
            Il ne sera plus visible dans la liste des consommables."
        confirm-text="Archiver"
        @confirm="archiveConsumable"
        @cancel="showArchiveDialog = false"
      />
    </template>

    <template #additional-content>
      <AddPurchaseForm
        v-model="showAddPurchaseDialog"
        :consumable-id="route.params.id"
        @purchase-added="fetchConsumable"
      />
      <TransferStockForm
        v-model="showTransferDialog"
        :consumable="consumable"
        @transfer-complete="fetchConsumable"
      />
    </template>
  </BaseDetailView>
</template>

<script setup>
  import { ref, onMounted, computed } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import { useDisplay } from 'vuetify'
  import BaseDetailView from '@/components/common/BaseDetailView.vue'
  import AddPurchaseForm from './AddPurchaseForm.vue'
  import TransferStockForm from './TransferStockForm.vue'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'
  import { useStore } from 'vuex'
  import ConfirmationModal from '@/components/common/ConfirmationModal.vue'

  const route = useRoute()
  const router = useRouter()
  const api = useApi(API_BASE_URL)
  const consumable = ref(null)
  const loading = ref(false)
  const showAddPurchaseDialog = ref(false)
  const showTransferDialog = ref(false)
  const showArchiveDialog = ref(false)
  const archiving = ref(false)
  const store = useStore()

  const goToEditConsumable = () => {
    router.push({ name: 'EditConsumable', params: { id: route.params.id } })
  }

  const { mobile } = useDisplay()

  const stockHeaders = [
    { title: 'Magasin', key: 'magasin_nom' },
    { title: 'Quantité', key: 'quantite' },
  ]

  const purchaseHeaders = computed(() => {
    if (mobile.value) {
      return [
        { title: 'Date', key: 'date_reference_prix' },
        { title: 'Qté', key: 'quantite' },
      ]
    }
    return [
      { title: 'Date', key: 'date_reference_prix' },
      { title: 'Fournisseur', key: 'fournisseur_nom' },
      { title: 'Fabricant', key: 'fabricant_nom' },
      { title: 'Qté', key: 'quantite' },
      { title: 'Prix Unitaire', key: 'prix_unitaire' },
      { title: 'Total', key: 'total' },
    ]
  })

  const breadcrumbs = [
    { title: 'Stocks', disabled: false, href: '/stocks' },
    { title: 'Consommables', disabled: false, href: '/stocks/consommables' },
    { title: 'Détail', disabled: true },
  ]

  const fetchConsumable = async () => {
    loading.value = true
    try {
      const response = await api.get(`consommables/${route.params.id}/`)
      consumable.value = response
    } catch (error) {
      console.error('Erreur chargement consommable', error)
    } finally {
      loading.value = false
    }
  }
  // ... (rest of script)

  const formattedPurchases = computed(() => {
    if (!consumable.value?.fournitures) return []
    return consumable.value.fournitures.map((achat) => ({
      ...achat,
      total: achat.quantite * achat.prix_unitaire,
    }))
  })

  const formatDate = (dateString) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleDateString('fr-FR')
  }

  const formatPrice = (price) => {
    if (!price) return '-'
    return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(price)
  }

  const archiveConsumable = async () => {
    archiving.value = true
    try {
      await api.patch(`consommables/${route.params.id}/set-archive/`, { archive: true })
      showArchiveDialog.value = false
      router.push({ name: 'Stocks' })
    } catch (error) {
      console.error('Erreur archivage consommable', error)
    } finally {
      archiving.value = false
    }
  }

  onMounted(fetchConsumable)
</script>

<style scoped>
  .floating-buttons {
    position: fixed !important;
    bottom: 24px;
    right: 24px;
    z-index: 100;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
</style>
