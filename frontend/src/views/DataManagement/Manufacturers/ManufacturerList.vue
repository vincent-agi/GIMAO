<template>
  <BaseListView
    :title="title"
    :headers="TABLE_HEADERS.SUPPLIERS"
    :items="manufacturers"
    :loading="loading"
    :error-message="errorMessage"
    :show-search="true"
    :show-create-button="false"
    no-data-icon="mdi-package-variant-closed"
    :internal-search="true"
    @row-click="goToManufacturerDetail($event.id)"
    @clear-error="errorMessage = ''"
  >
    <template #[`item.serviceApresVente`]="{ item }">
      <v-chip :color="item.serviceApresVente ? 'success' : 'error'" variant="outlined" size="small">
        {{ item.serviceApresVente ? 'Oui' : 'Non' }}
      </v-chip>
    </template>

    <template v-if="store.getters.hasPermission('man:viewDetail')" #[`item.actions`]="{ item }">
      <v-btn icon size="small" @click.stop="goToManufacturerDetail(item.id)">
        <v-icon>mdi-eye</v-icon>
      </v-btn>
    </template>
  </BaseListView>

  <!-- Bouton flottant en bas à droite -->
  <v-btn
    v-if="store.getters.hasPermission('man:create')"
    color="primary"
    size="large"
    icon
    class="floating-add-button"
    elevation="4"
    @click="goToManufacturerCreation"
  >
    <v-icon size="large">mdi-plus</v-icon>
    <v-tooltip activator="parent" location="left">
      {{ createButtonText }}
    </v-tooltip>
  </v-btn>
</template>

<script setup>
  import BaseListView from '@/components/common/BaseListView.vue'
  import { ref, onMounted } from 'vue'
  import { useStore } from 'vuex'
  import { useApi } from '@/composables/useApi.js'
  import { API_BASE_URL, TABLE_HEADERS } from '@/utils/constants'
  import { useRouter } from 'vue-router'

  // Données
  const title = 'Liste des fabricants'
  const api = useApi(API_BASE_URL)
  const manufacturers = ref([])
  const store = useStore()
  const loading = ref(true)
  const errorMessage = ref('')
  const router = useRouter()
  const createButtonText = 'Créer un nouveau fabricant'

  // Récup des données
  onMounted(async () => {
    loadManufacturers()
  })

  const loadManufacturers = async () => {
    try {
      manufacturers.value = await api.get('fabricants/')
      loading.value = false
    } catch {
      errorMessage.value = 'Erreur lors du chargement des fabricants.'
    } finally {
      loading.value = false
    }
  }

  // Navigation
  const goToManufacturerDetail = (id) => {
    router.push({
      name: 'ManufacturerDetail',
      params: { id: id },
    })
  }

  const goToManufacturerCreation = () => {
    router.push({ name: 'CreateManufacturer' })
  }
</script>

<style scoped>
  .floating-add-button {
    position: fixed !important;
    bottom: 24px;
    right: 24px;
    z-index: 100;
  }

  .floating-add-button:hover {
    transform: scale(1.1);
    transition: transform 0.2s ease;
  }
</style>
