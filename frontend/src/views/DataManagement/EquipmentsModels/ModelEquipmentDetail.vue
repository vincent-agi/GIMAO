<template>
  <BaseDetailView
    :data="modelEquipment"
    :loading="isLoading"
    :error-message="errorMessage"
    :success-message="successMessage"
    :title="'Détail du modèle d\'équipement'"
    :auto-display="false"
    :show-edit-button="false"
    @delete="handleDelete"
    @clear-error="errorMessage = ''"
    @clear-success="successMessage = ''"
  >
    <template #default>
      <v-row v-if="modelEquipment" dense>
        <v-col cols="12">
          <h3 class="text-h6 mb-3">Informations générales</h3>
        </v-col>
        <v-col cols="12" md="6">
          <strong>Nom du modèle d'équipement</strong>
          <div>{{ modelEquipment.nom || '-' }}</div>
        </v-col>
        <v-col cols="12" md="6">
          <strong>Fabricant</strong>
          <div>{{ modelEquipment.fabricant?.nom || '-' }}</div>
        </v-col>
      </v-row>

      <v-row v-else>
        <v-col cols="12">
          <p v-if="isLoading">Chargement en cours...</p>
          <p v-else>Aucune donnée disponible.</p>
        </v-col>
      </v-row>
    </template>
  </BaseDetailView>

  <!-- Bouton de modification -->
  <v-btn
    v-if="store.getters.hasPermission('eqmod:edit')"
    color="primary"
    size="large"
    icon
    class="floating-edit-button"
    elevation="4"
    @click="editModelEquipment"
  >
    <v-icon size="large">mdi-pencil</v-icon>
    <v-tooltip activator="parent" location="left"> Modifier le modèle d'équipement </v-tooltip>
  </v-btn>
</template>

<script setup>
  import { ref, onMounted } from 'vue'
  import { useStore } from 'vuex'
  import { useRoute, useRouter } from 'vue-router'
  import { useApi } from '@/composables/useApi.js'
  import { API_BASE_URL } from '@/utils/constants'
  import BaseDetailView from '@/components/common/BaseDetailView.vue'

  const route = useRoute()
  const router = useRouter()
  const api = useApi(API_BASE_URL)
  const store = useStore()

  const modelEquipment = ref(null)
  const isLoading = ref(true)
  const errorMessage = ref('')
  const successMessage = ref('')

  const loadModelEquipment = async () => {
    console.log('loadModelEquipment appelée !')
    isLoading.value = true
    try {
      const id = route.params.id
      console.log('ID récupéré :', id)

      const response = await api.get(`modele-equipements/${id}/`)
      console.log('Réponse API :', response)

      modelEquipment.value = response || null
    } catch (error) {
      console.error('Erreur API :', error)
      errorMessage.value = "Erreur lors du chargement du modèle d'équipement."
      modelEquipment.value = null
    } finally {
      isLoading.value = false
    }
  }

  const handleDelete = () => {
    // Implémente ta logique de suppression
    console.log('Delete clicked')
  }

  onMounted(async () => {
    await loadModelEquipment()
  })

  const editModelEquipment = () => {
    const id = route.params.id
    router.push({ name: 'EditModelEquipment', params: { id: id } })
  }
</script>

<style scoped>
  .detail-label {
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.875rem;
    color: #666;
    margin-bottom: 4px;
  }

  .detail-value {
    font-size: 1rem;
    color: #333;
    padding: 8px 0;
    border-bottom: 1px solid #e0e0e0;
  }

  .floating-edit-button {
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 1000;
  }
</style>
