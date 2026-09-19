<template>
  <v-container>
    <v-alert v-if="isLoading" type="info" variant="tonal" class="mb-4">
      <v-progress-circular indeterminate size="20" class="mr-2"></v-progress-circular>
      Chargement des données...
    </v-alert>

    <v-alert v-else-if="errorLoading !== ''" type="error" variant="tonal" class="mb-4">
      {{ errorLoading }}
    </v-alert>

    <FabricantForm
      v-if="!isLoading && manufacturerData"
      title="Modifier le fabricant"
      submit-button-text="Enregistrer les modifications"
      :is-edit="true"
      :initial-data="manufacturerData"
      :connected-user-id="connectedUserId"
      @updated="handleUpdated"
      @close="handleClose"
    />
  </v-container>
</template>

<script setup>
  import { ref, onMounted, computed } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import { useStore } from 'vuex'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'
  import FabricantForm from '@/components/Forms/FabricantForm.vue'

  const route = useRoute()
  const router = useRouter()
  const store = useStore()
  const api = useApi(API_BASE_URL)

  const manufacturerId = route.params.id
  const manufacturerData = ref(null)
  const originalData = ref(null)
  const isLoading = ref(false)
  const errorLoading = ref('')

  const connectedUserId = computed(() => store.getters.currentUser?.id)

  const loadManufacturerData = async () => {
    isLoading.value = true
    errorLoading.value = ''
    try {
      manufacturerData.value = await api.get(`fabricants/${manufacturerId}`)
      originalData.value = JSON.parse(JSON.stringify(manufacturerData.value))
      isLoading.value = false
    } catch (error) {
      console.error('Error loading manufacturer data:', error)
      errorLoading.value = 'Erreur lors du chargement des données du fabricant'
      isLoading.value = false
    } finally {
      isLoading.value = false
    }
  }

  const handleUpdated = () => {
    router.push({
      name: 'ManufacturerDetail',
      params: { id: manufacturerId },
    })
  }

  const handleClose = () => {
    router.push({
      name: 'ManufacturerDetail',
      params: { id: manufacturerId },
    })
  }

  onMounted(() => {
    loadManufacturerData()
  })
</script>
