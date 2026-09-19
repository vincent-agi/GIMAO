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

        <InterventionForm
          v-if="!loading && bonTravailData"
          :title="`Modifier le bon de travail #${bonId}`"
          submit-button-text="Enregistrer"
          submit-button-color="primary"
          :is-edit="true"
          :initial-data="bonTravailData"
          :equipments="equipments"
          :users="users"
          :consommables="consommables"
          :type-documents="typeDocuments"
          :connected-user-id="connectedUser?.id"
          @updated="handleUpdated"
          @close="handleClose"
        />
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
  import { computed, onMounted, ref } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import { useStore } from 'vuex'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'
  import InterventionForm from '@/components/Forms/InterventionForm.vue'
  import { toTimeInputValue } from '@/utils/helpers'
  import { fetchAllPages } from '@/utils/paginatedApi'

  const route = useRoute()
  const router = useRouter()
  const store = useStore()
  const api = useApi(API_BASE_URL)

  const bonId = route.params.id

  const loading = ref(false)
  const errorLoading = ref('')
  const bonTravailData = ref(null)
  const equipments = ref([])
  const users = ref([])
  const consommables = ref([])
  const typeDocuments = ref([])

  const connectedUser = computed(() => store.getters.currentUser)

  const toDatetimeLocalValue = (value) => {
    if (!value) return null
    if (typeof value !== 'string') return null

    // Accepte :
    // - "2026-01-10 09:00:00.000000" (format DB)
    // - "2026-01-10T09:00:00" / "2026-01-10T09:00:00.000000" (ISO)
    const match = value.match(/^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})/)
    if (!match) return null
    return `${match[1]}T${match[2]}`
  }

  const fetchBonTravail = async () => {
    loading.value = true
    errorLoading.value = ''

    try {
      const bon = await api.get(`bons-travail/${bonId}/`)

      const consommablesLines = Array.isArray(bon?.consommables)
        ? bon.consommables.map((c) => ({
            consommable_id: c?.consommable ?? null,
            quantite_utilisee: Number.isFinite(Number(c?.quantite)) ? Number(c.quantite) : 0,
          }))
        : []

      const documentsLines = Array.isArray(bon?.documentsBT)
        ? bon.documentsBT.map((d) => ({
            document_id: d?.id ?? null,
            nomDocument: d?.titre || '',
            typeDocument_id: d?.type ?? null,
            file: null,
            existingFileName: d?.path ? d.path.split('/').pop() : '',
          }))
        : []

      bonTravailData.value = {
        id: bonId,
        equipement_id: bon?.demande_intervention?.equipement?.id ?? null,
        nom: bon?.nom ?? '',
        type: bon?.type ?? 'CORRECTIF',
        date_prevue: toDatetimeLocalValue(bon?.date_prevue),
        duree_previsionnelle: toTimeInputValue(bon?.duree_previsionnelle),
        commentaire: bon?.commentaire ?? '',
        diagnostic: bon?.diagnostic ?? '',
        responsable_id: bon?.responsable?.id ?? null,
        utilisateur_assigne_ids: Array.isArray(bon?.utilisateur_assigne)
          ? bon.utilisateur_assigne.map((u) => u.id)
          : [],
        consommables: consommablesLines.length
          ? consommablesLines
          : [{ consommable_id: null, quantite_utilisee: null }],
        documents: documentsLines.length
          ? documentsLines
          : [{ document_id: null, nomDocument: '', typeDocument_id: null, file: null }],
      }
    } catch (error) {
      console.error('Erreur lors de la récupération des données:', error)
      errorLoading.value = 'Erreur lors du chargement des données du bon de travail'
    } finally {
      loading.value = false
    }
  }

  const handleUpdated = () => {
    router.push({ name: 'InterventionDetail', params: { id: bonId } })
  }

  const handleClose = () => {
    router.push({ name: 'InterventionDetail', params: { id: bonId } })
  }

  onMounted(async () => {
    loading.value = true
    try {
      await Promise.all([
        fetchAllPages(api, 'utilisateurs/').then((data) => (users.value = data)),
        fetchAllPages(api, 'equipements/').then((data) => (equipments.value = data)),
        fetchAllPages(api, 'consommables/').then((data) => (consommables.value = data)),
        api.get('types-documents/').then((data) => (typeDocuments.value = data)),
        fetchBonTravail(),
      ])
    } catch (error) {
      console.error('Erreur lors du chargement:', error)
      errorLoading.value = 'Erreur lors du chargement des données'
    } finally {
      loading.value = false
    }
  })
</script>
