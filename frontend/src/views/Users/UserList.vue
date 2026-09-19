<template>
  <BaseListView
    :title="title"
    :headers="headers"
    :items="displayedUsers"
    :loading="loading"
    :error-message="resolvedErrorMessage"
    :show-search="true"
    :show-create-button="false"
    :search-value="searchQuery"
    :items-per-page="-1"
    :hide-default-footer="true"
    no-data-icon="mdi-account-off"
    :internal-search="false"
    @clear-error="errorMessage = ''"
    @row-click="goToAfficherUser($event.id)"
    @search="handleSearch"
  >
    <template #before-table>
      <v-card elevation="1" class="rounded-lg pa-3 mb-4 role-filter-card">
        <div class="d-flex align-center justify-space-between flex-wrap gap-2">
          <div class="text-subtitle-1 font-weight-bold text-primary">Filtrer par rôle</div>
          <v-chip-group
            v-model="selectedRole"
            mandatory
            selected-class="text-primary"
            class="role-chip-group"
          >
            <v-chip
              v-for="role in roles"
              :key="role.id ?? 'all'"
              :value="role.id"
              variant="outlined"
              size="small"
            >
              {{ role.label }}
            </v-chip>
          </v-chip-group>
        </div>
      </v-card>
    </template>

    <template #[`item.role`]="{ item }">
      <v-chip variant="outlined" size="small" color="primary">
        {{ item.role || '-' }}
      </v-chip>
    </template>

    <template #[`item.actif`]="{ item }">
      <v-chip variant="outlined" size="small" :color="item.actif ? 'success' : 'grey'">
        {{ item.actif ? 'Oui' : 'Non' }}
      </v-chip>
    </template>

    <template #after-table>
      <ServerPaginationControls
        :page="currentPage"
        :page-size="pageSize"
        :page-count="totalPages"
        :total-items="totalItems"
        item-label-singular="utilisateur"
        item-label-plural="utilisateurs"
        :reserve-fab-space="store.getters.hasPermission('user:create')"
        @update:page="currentPage = $event"
        @update:page-size="pageSize = $event"
      />
    </template>
  </BaseListView>

  <FloatingCreateButton
    :visible="store.getters.hasPermission('user:create')"
    :tooltip="createButtonText"
    @click="goToCreerUser"
  />
</template>

<script setup>
  import { computed, onMounted, ref } from 'vue'
  import { useStore } from 'vuex'
  import { useRouter } from 'vue-router'
  import { useDisplay } from 'vuetify'
  import BaseListView from '@/components/common/BaseListView.vue'
  import FloatingCreateButton from '@/components/common/FloatingCreateButton.vue'
  import ServerPaginationControls from '@/components/common/ServerPaginationControls.vue'
  import { useApi } from '@/composables/useApi'
  import { usePaginatedList } from '@/composables/usePaginatedList'
  import { API_BASE_URL } from '@/utils/constants'

  const title = 'Gestion des comptes'
  const createButtonText = 'Créer un nouvel utilisateur'

  const router = useRouter()
  const store = useStore()
  const { smAndDown } = useDisplay()

  const api = useApi(API_BASE_URL)
  const rolesApi = useApi(API_BASE_URL)

  const errorMessage = ref('')
  const roles = ref([{ id: null, label: 'Tous' }])
  const selectedRole = ref(null)

  const baseHeaders = [
    { title: "Nom d'utilisateur", value: 'nomUtilisateur', sortable: true, align: 'start' },
    { title: 'Nom', value: 'nom', sortable: true, align: 'start' },
    { title: 'Rôle', value: 'role', sortable: true, align: 'center' },
    { title: 'Actif', value: 'actif', sortable: true, align: 'end' },
  ]

  const headers = computed(() => {
    if (smAndDown.value) {
      return baseHeaders.filter((header) => header.value !== 'actif')
    }

    return baseHeaders
  })

  const {
    items,
    currentPage,
    pageSize,
    totalItems,
    totalPages,
    loading,
    errorMessage: paginationErrorMessage,
    fetchPage,
    handleSearch,
  } = usePaginatedList({
    api,
    endpoint: 'utilisateurs/',
    initialPageSize: 10,
    buildParams: () => ({
      role_id: selectedRole.value ?? undefined,
    }),
    watchSource: () => selectedRole.value,
  })

  const displayedUsers = computed(() =>
    items.value.map((user) => ({
      id: user?.id,
      nomUtilisateur: user?.nomUtilisateur ?? '-',
      nom: `${user?.prenom ?? ''} ${user?.nomFamille ?? ''}`.trim() || '-',
      role: user?.role?.nomRole || user?.role || '-',
      actif: Boolean(user?.actif),
    }))
  )

  const resolvedErrorMessage = computed(() => errorMessage.value || paginationErrorMessage.value)

  const loadRoles = async () => {
    try {
      const response = await rolesApi.get('roles/')
      const roleItems = Array.isArray(response)
        ? response
            .map((role) => ({
              id: role?.id ?? null,
              label: role?.nomRole ?? '',
            }))
            .filter((role) => role.label)
        : []

      roles.value = [{ id: null, label: 'Tous' }, ...roleItems]
    } catch {
      roles.value = [{ id: null, label: 'Tous' }]
      errorMessage.value = 'Erreur lors du chargement des rôles.'
    }
  }

  const goToAfficherUser = (id) => {
    router.push({
      name: 'UserDetail',
      params: { id },
    })
  }

  const goToCreerUser = () => {
    router.push({ name: 'CreateUser' })
  }

  onMounted(async () => {
    await Promise.allSettled([loadRoles(), fetchPage()])
  })
</script>

<style scoped>
  .role-filter-card {
    background-color: var(--card-bg-color);
    transition: background-color 0.2s ease;
  }

  .role-chip-group {
    max-width: 100%;
  }
</style>
