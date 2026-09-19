<template>
  <BaseListView
    :title="title"
    :items="modelEquipments"
    :loading="loading"
    :error-message="errorMessage"
    :headers="TABLE_HEADERS.MODEL_EQUIPMENTS"
    :show-create-button="false"
    @row-click="goToModelEquipmentDetail($event.id)"
    @create-button-click="goToModelEquipmentCreation"
  >
    <template #[`item.fabricant`]="{ item }">
      {{ item.fabricant?.nom }}
    </template>

    <template v-if="store.getters.hasPermission('eqmod:viewDetail')" #[`item.action`]="{ item }">
      <v-btn icon size="small" @click.stop="goToModelEquipmentDetail(item.id)">
        <v-icon>mdi-eye</v-icon>
      </v-btn>
    </template>
  </BaseListView>

  <!-- Bouton flottant en bas à droite -->
  <v-btn
    v-if="store.getters.hasPermission('eqmod:create')"
    color="primary"
    size="large"
    icon
    class="floating-add-button"
    elevation="4"
    @click="goToModelEquipmentCreation"
  >
    <v-icon size="large">mdi-plus</v-icon>
    <v-tooltip activator="parent" location="left">
      {{ createButtonText }}
    </v-tooltip>
  </v-btn>
</template>

<script setup>
  import BaseListView from '@/components/common/BaseListView.vue'
  import { useStore } from 'vuex'
  import { ref, onMounted } from 'vue'
  import { useApi } from '@/composables/useApi.js'
  import { API_BASE_URL, TABLE_HEADERS } from '@/utils/constants'
  import { useRouter } from 'vue-router'

  // Données
  const title = "Liste des modèles d'équipements"
  const api = useApi(API_BASE_URL)
  const modelEquipments = ref([])
  const loading = ref(true)
  const errorMessage = ref('')
  const router = useRouter()
  const createButtonText = "Créer un nouveau modèle d'équipement"
  const store = useStore()

  // Récup des données
  onMounted(async () => {
    console.log('Headers : ', TABLE_HEADERS.MODEL_EQUIPMENTS)
    loadModelEquipments()
  })

  const loadModelEquipments = async () => {
    try {
      modelEquipments.value = await api.get('modele-equipements/')
      loading.value = false
    } catch {
      errorMessage.value = "Erreur lors du chargement des modèles d'équipements."
    } finally {
      loading.value = false
    }
  }

  // Navigation
  const goToModelEquipmentDetail = (id) => {
    router.push({
      name: 'ModelEquipmentDetail',
      params: { id: id },
    })
  }
  const goToModelEquipmentCreation = () => {
    router.push({ name: 'CreateModelEquipment' })
  }
</script>

<style scoped>
  .floating-add-button {
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 1000;
  }
</style>
