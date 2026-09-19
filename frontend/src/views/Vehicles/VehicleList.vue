<template>
  <BaseListView
    :title="title"
    :headers="headers"
    :items="displayedVehicules"
    :loading="loading"
    :error-message="errorMessage"
    :show-search="true"
    :show-create-button="false"
    no-data-icon="mdi-car-off"
    no-data-text="Aucun véhicule trouvé"
    :internal-search="false"
    @clear-error="errorMessage = ''"
    @row-click="goToVehicleDetail($event.id)"
    @search="handleSearch"
  >
    <template #item.statut="{ item }">
      <v-chip v-if="item.statut" variant="outlined" size="small" :color="getStatusColor(item.statut)">
        {{ getStatusLabel(item.statut) }}
      </v-chip>
      <span v-else>-</span>
    </template>

    <template #after-table>
      <ServerPaginationControls
        :page="currentPage"
        :page-size="pageSize"
        :page-count="totalPages"
        :total-items="totalItems"
        item-label-singular="véhicule"
        item-label-plural="véhicules"
        :reserve-fab-space="store.getters.hasPermission('veh:create')"
        @update:page="currentPage = $event"
        @update:page-size="pageSize = $event"
      />
    </template>
  </BaseListView>

  <FloatingCreateButton
    :visible="store.getters.hasPermission('veh:create')"
    :tooltip="createButtonText"
    @click="goToCreateVehicle"
  />
</template>

<script setup>
/**
 * Liste des véhicules de la flotte (US-001).
 *
 * Pagination et recherche côté serveur via `/api/vehicules/` (délégué à
 * `usePaginatedList`), sur le même modèle que `UserList.vue`/`SupplierList.vue`.
 */
import { computed, onMounted } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';
import BaseListView from '@/components/common/BaseListView.vue';
import FloatingCreateButton from '@/components/common/FloatingCreateButton.vue';
import ServerPaginationControls from '@/components/common/ServerPaginationControls.vue';
import { useApi } from '@/composables/useApi';
import { usePaginatedList } from '@/composables/usePaginatedList';
import { API_BASE_URL } from '@/utils/constants';
import { getStatusColor, getStatusLabel } from '@/utils/helpers';

const title = 'Véhicules';
const createButtonText = 'Ajouter un véhicule';

const router = useRouter();
const store = useStore();
const api = useApi(API_BASE_URL);

const headers = [
  { title: 'Immatriculation', value: 'immatriculation', sortable: true, align: 'start' },
  { title: 'Désignation', value: 'designation', sortable: true, align: 'start' },
  { title: 'Modèle', value: 'modele', sortable: false, align: 'start' },
  { title: 'Genre', value: 'genre', sortable: false, align: 'center' },
  { title: 'Lieu', value: 'lieu', sortable: false, align: 'start' },
  { title: 'Statut', value: 'statut', sortable: false, align: 'center' },
];

const {
  items,
  currentPage,
  pageSize,
  totalItems,
  totalPages,
  loading,
  errorMessage,
  fetchPage,
  handleSearch,
} = usePaginatedList({
  api,
  endpoint: 'vehicules/',
  initialPageSize: 10,
});

/**
 * Aplatit chaque véhicule (Equipement + VehiculeProfile imbriqué) pour l'affichage tabulaire.
 * @param {object[]} vehicules
 * @returns {object[]}
 */
const displayedVehicules = computed(() =>
  items.value.map((vehicule) => ({
    id: vehicule?.id,
    immatriculation: vehicule?.vehicule_profile?.immatriculation ?? '-',
    designation: vehicule?.designation ?? '-',
    modele: vehicule?.modele ?? '-',
    genre: vehicule?.vehicule_profile?.genre ?? '-',
    lieu: vehicule?.lieu?.nomLieu ?? '-',
    statut: vehicule?.statut?.statut ?? null,
  })),
);

const goToVehicleDetail = (id) => {
  router.push({ name: 'VehicleDetail', params: { id } });
};

const goToCreateVehicle = () => {
  router.push({ name: 'CreateVehicle' });
};

onMounted(fetchPage);
</script>
