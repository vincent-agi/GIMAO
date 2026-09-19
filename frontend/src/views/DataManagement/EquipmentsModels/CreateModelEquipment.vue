<template>
  <v-container>
    <v-alert v-if="loadingData" type="info" variant="tonal" class="mb-4">
      <v-progress-circular indeterminate size="20" class="mr-2"></v-progress-circular>
      Chargement des données...
    </v-alert>

    <ModeleEquipementForm
      v-if="!loadingData"
      title="Créer un modèle d'équipement"
      submit-button-text="Créer le modèle"
      :fabricants="fabricants"
      @created="handleCreated"
      @close="handleClose"
      @fabricant-created="handleFabricantCreated"
    />
  </v-container>
</template>

<script setup>
  import { ref, onMounted } from 'vue'
  import { useRouter } from 'vue-router'
  import ModeleEquipementForm from '@/components/Forms/ModeleEquipementForm.vue'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'

  const router = useRouter()
  const api = useApi(API_BASE_URL)

  const fabricants = ref([])
  const loadingData = ref(false)

  const loadFabricants = async () => {
    loadingData.value = true

    try {
      fabricants.value = await api.get('fabricants/')
    } catch (error) {
      console.error('Error loading manufacturers:', error)
    } finally {
      loadingData.value = false
    }
  }

  const handleCreated = (newModel) => {
    router.push({
      name: 'ModelEquipmentDetail',
      params: { id: newModel.id },
    })
  }

  const handleClose = () => {
    router.push({ name: 'ModelEquipmentList' })
  }

  const handleFabricantCreated = (newFabricant) => {
    fabricants.value.push(newFabricant)
  }

  onMounted(() => {
    loadFabricants()
  })
</script>
