<template>
  <v-app>
    <v-main>
      <v-container>
        <v-alert v-if="loading" type="info" variant="tonal" class="mb-4">
          <v-progress-circular indeterminate size="20" class="mr-2"></v-progress-circular>
          Chargement des données...
        </v-alert>

        <v-alert v-if="errorLoading" type="error" variant="tonal" class="mb-4">
          {{ errorLoading }}
        </v-alert>

        <FailureForm
          v-if="!loading && failureData"
          :title="`Modifier la demande d'intervention #${failureId}`"
          submit-button-text="Enregistrer les modifications"
          :is-edit="true"
          :initial-data="failureData"
          :equipments="equipments"
          :types-documents="typesDocuments"
          @updated="handleUpdated"
          @close="handleClose"
        />
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
  import { ref, computed, onMounted } from 'vue'
  import { useRouter, useRoute } from 'vue-router'
  import FailureForm from '@/components/Forms/FailureForm.vue'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'
  import { fetchAllPages } from '@/utils/paginatedApi'

  const router = useRouter()
  const route = useRoute()
  const api = useApi(API_BASE_URL)

  const failureId = computed(() => route.params.id || null)
  const loading = ref(false)
  const errorLoading = ref('')
  const failureData = ref(null)
  const equipments = ref([])
  const typesDocuments = ref([])

  const fetchEquipments = async () => {
    try {
      equipments.value = await fetchAllPages(api, 'equipements/')
    } catch (error) {
      console.error('Erreur lors de la récupération des équipements:', error)
    }
  }

  const fetchTypesDocuments = async () => {
    try {
      typesDocuments.value = await api.get('types-documents/')
    } catch (error) {
      console.error('Erreur lors de la récupération des types de documents:', error)
    }
  }

  const fetchFailureData = async () => {
    loading.value = true
    errorLoading.value = ''

    try {
      const response = await api.get(`demandes-intervention/${failureId.value}/`)

      // Formatter les documents existants pour DocumentForm
      const documentsLines = Array.isArray(response?.documentsDI)
        ? response.documentsDI.map((d) => ({
            document_id: d?.id ?? null,
            nomDocument: d?.nomDocument || d?.titre || '',
            typeDocument_id: d?.type ?? null,
            file: null,
            existingFileName: d?.path ? d.path.split('/').pop() : null,
          }))
        : []

      failureData.value = {
        id: failureId.value,
        nom: response.nom || '',
        commentaire: response.commentaire || '',
        equipement_id: response.equipement?.id || null,
        documents: documentsLines.length ? documentsLines : [],
        statut_suppose: response.statut_suppose || '',
      }
    } catch (error) {
      console.error('Erreur lors de la récupération des données:', error)
      errorLoading.value = 'Erreur lors du chargement des données de la demande'
    } finally {
      loading.value = false
    }
  }

  const handleUpdated = () => {
    router.back()
  }

  const handleClose = () => {
    router.back()
  }

  onMounted(() => {
    fetchEquipments()
    fetchTypesDocuments()
    fetchFailureData()
  })
</script>
