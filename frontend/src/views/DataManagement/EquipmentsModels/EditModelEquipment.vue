<template>
  <v-container>
    <v-alert v-if="loading" type="info" variant="tonal" class="mb-4">
      <v-progress-circular indeterminate size="20" class="mr-2"></v-progress-circular>
      Chargement des données...
    </v-alert>

    <v-alert v-else-if="errorLoading" type="error" variant="tonal" class="mb-4">
      {{ errorLoading }}
    </v-alert>

    <ModeleEquipementForm
      v-if="!loading && modelEquipment"
      title="Modifier le modèle d'équipement"
      submit-button-text="Enregistrer les modifications"
      :is-edit="true"
      :initial-data="modelEquipment"
      :fabricants="fabricants"
      :connected-user-id="connectedUserId"
      @updated="handleUpdated"
      @close="handleClose"
      @fabricant-created="handleFabricantCreated"
    />
  </v-container>
</template>

<script setup>
  import { onMounted, ref, computed } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import { useApi } from '@/composables/useApi'
  import { useStore } from 'vuex'
  import { API_BASE_URL } from '@/utils/constants'
  import ModeleEquipementForm from '@/components/Forms/ModeleEquipementForm.vue'

  const route = useRoute()
  const router = useRouter()
  const store = useStore()
  const api = useApi(API_BASE_URL)

  const modelEquipment = ref(null)
  const fabricants = ref([])
  const loading = ref(false)
  const errorLoading = ref('')

  const connectedUserId = computed(() => store.getters.currentUser?.id)

  const loadModelEquipmentData = async () => {
    loading.value = true
    errorLoading.value = ''

    try {
      const response = await api.get(`modele-equipements/${route.params.id}/`)
      console.log('Données chargées:', response)
      modelEquipment.value = response
    } catch (error) {
      console.error('Error loading model equipment:', error)
      errorLoading.value = 'Erreur lors du chargement des données'
    } finally {
      loading.value = false
    }
  }

  const loadFabricants = async () => {
    try {
      fabricants.value = await api.get('fabricants/')
    } catch (error) {
      console.error('Error loading fabricants:', error)
    }
  }

  const handleUpdated = (updatedModel) => {
    router.push({
      name: 'ModelEquipmentDetail',
      params: { id: updatedModel.id },
    })
  }

  const handleClose = () => {
    router.push({
      name: 'ModelEquipmentDetail',
      params: { id: route.params.id },
    })
  }

  const handleFabricantCreated = (newFabricant) => {
    fabricants.value.push(newFabricant)
  }

  onMounted(() => {
    loadModelEquipmentData()
    loadFabricants()
  })
</script>
