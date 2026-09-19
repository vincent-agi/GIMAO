<template>
  <v-app>
    <v-main>
      <v-container>
        <v-alert v-if="loadingData" type="info" variant="tonal" class="mb-4">
          <v-progress-circular indeterminate size="20" class="mr-2"></v-progress-circular>
          Chargement des données...
        </v-alert>

        <FailureForm
          v-if="!loadingData"
          title="Créer une Demande d'intervention"
          submit-button-text="Valider"
          :equipments="equipments"
          :types-documents="typesDocuments"
          :connected-user-id="connectedUser?.id"
          :initial-data="initialData"
          @created="handleCreated"
          @close="handleClose"
        />
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
  import { ref, onMounted, computed } from 'vue'
  import { useRouter, useRoute } from 'vue-router'
  import { useStore } from 'vuex'
  import FailureForm from '@/components/Forms/FailureForm.vue'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'
  import { fetchAllPages } from '@/utils/paginatedApi'
  import '@/assets/css/global.css'

  const router = useRouter()
  const route = useRoute()
  const store = useStore()
  const api = useApi(API_BASE_URL)

  const loadingData = ref(false)
  const equipments = ref([])
  const typesDocuments = ref([])
  const connectedUser = computed(() => store.getters.currentUser)
  const initialData = ref({})

  const fetchData = async () => {
    loadingData.value = true

    try {
      const [equipmentsResponse, typesDocumentsResponse] = await Promise.all([
        fetchAllPages(api, 'equipements/'),
        api.get('types-documents/'),
      ])

      equipments.value = equipmentsResponse
      typesDocuments.value = typesDocumentsResponse

      // Si un équipement est passé en paramètre
      const equipmentId = route.params.equipmentId
      if (equipmentId) {
        initialData.value.equipement_id = parseInt(equipmentId)
      }
    } catch (error) {
      console.error('Erreur lors de la récupération des données:', error)
    } finally {
      loadingData.value = false
    }
  }

  const handleCreated = (newFailure) => {
    router.push({ name: 'FailureDetail', params: { id: newFailure.id } })
  }

  const handleClose = () => {
    router.back()
  }

  onMounted(() => {
    fetchData()
  })
</script>
