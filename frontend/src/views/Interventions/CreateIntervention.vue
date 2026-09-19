<template>
  <v-app>
    <v-main>
      <v-container>
        <v-alert v-if="loadingData" type="info" variant="tonal" class="mb-4">
          <v-progress-circular indeterminate size="20" class="mr-2"></v-progress-circular>
          Chargement des données...
        </v-alert>

        <InterventionForm
          v-if="!loadingData"
          title="Créer un bon de travail"
          submit-button-text="Créer"
          submit-button-color="success"
          :equipments="equipments"
          :users="users"
          :consommables="consommables"
          :type-documents="typeDocuments"
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
  import { computed, onMounted, ref } from 'vue'
  import { useRouter } from 'vue-router'
  import { useStore } from 'vuex'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'
  import InterventionForm from '@/components/Forms/InterventionForm.vue'
  import { fetchAllPages } from '@/utils/paginatedApi'

  const router = useRouter()
  const store = useStore()
  const api = useApi(API_BASE_URL)

  const loadingData = ref(false)
  const users = ref([])
  const equipments = ref([])
  const consommables = ref([])
  const typeDocuments = ref([])

  const connectedUser = computed(() => store.getters.currentUser)

  const initialData = ref({
    responsable_id: null,
  })

  const fetchData = async () => {
    loadingData.value = true
    try {
      const [usersResponse, equipmentsResponse, consommablesResponse, typeDocumentsResponse] =
        await Promise.all([
          fetchAllPages(api, 'utilisateurs/'),
          fetchAllPages(api, 'equipements/'),
          fetchAllPages(api, 'consommables/'),
          api.get('types-documents/'),
        ])

      users.value = usersResponse
      equipments.value = equipmentsResponse
      consommables.value = consommablesResponse
      typeDocuments.value = typeDocumentsResponse

      initialData.value.responsable_id = connectedUser.value?.id ?? null
    } catch (error) {
      console.error('Erreur lors du chargement:', error)
    } finally {
      loadingData.value = false
    }
  }

  const handleCreated = (newBonTravail) => {
    router.push({ name: 'InterventionDetail', params: { id: newBonTravail.id } })
  }

  const handleClose = () => {
    router.back()
  }

  onMounted(() => {
    fetchData()
  })
</script>
