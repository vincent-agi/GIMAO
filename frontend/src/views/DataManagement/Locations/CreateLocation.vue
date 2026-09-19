<template>
  <v-container>
    <v-alert v-if="loadingData" type="info" variant="tonal" class="mb-4">
      <v-progress-circular indeterminate size="20" class="mr-2"></v-progress-circular>
      Chargement des données...
    </v-alert>

    <LieuForm
      v-if="!loadingData"
      title="Créer un nouveau lieu"
      submit-button-text="Créer le lieu"
      :use-tree-view="false"
      :locations="locationOptions"
      :parent-id="parentIdFromRoute"
      :show-lien-plan="false"
      @created="handleCreated"
      @close="handleClose"
    />
  </v-container>
</template>

<script setup>
  import { onMounted, ref } from 'vue'
  import LieuForm from '@/components/Forms/LieuForm.vue'
  import { useApi } from '@/composables/useApi.js'
  import { API_BASE_URL } from '@/utils/constants.js'
  import { useRoute, useRouter } from 'vue-router'

  const route = useRoute()
  const router = useRouter()
  const api = useApi(API_BASE_URL)

  const locationOptions = ref([])
  const loadingData = ref(false)
  const parentIdFromRoute = ref(null)

  const fetchAvailableLocations = async () => {
    loadingData.value = true

    try {
      locationOptions.value = await api.get('lieux/')

      // Définir le parent si présent dans la route
      const parentIdParam = route.query.parentId
      if (parentIdParam && parentIdParam !== 'root') {
        parentIdFromRoute.value = parseInt(parentIdParam, 10)
        console.log('Parent ID défini depuis la route:', parentIdFromRoute.value)
      }
    } catch (error) {
      console.error('Erreur lors de la récupération des lieux :', error)
    } finally {
      loadingData.value = false
    }
  }

  const handleCreated = (_newLocation) => {
    router.push({ name: 'LocationList' })
  }

  const handleClose = () => {
    router.push({ name: 'LocationList' })
  }

  onMounted(() => {
    fetchAvailableLocations()
  })
</script>
