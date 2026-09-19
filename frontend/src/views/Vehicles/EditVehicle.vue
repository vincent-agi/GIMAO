<template>
  <v-container>
    <v-alert v-if="loading" type="info" variant="tonal" class="mb-4">
      <v-progress-circular indeterminate size="20" class="mr-2"></v-progress-circular>
      Chargement des données...
    </v-alert>

    <v-alert v-else-if="errorMessage" type="error" variant="tonal" class="mb-4">
      {{ errorMessage }}
    </v-alert>

    <VehiculeForm
      v-if="!loading && vehicleData"
      title="Modifier le véhicule"
      submit-button-text="Enregistrer les modifications"
      :is-edit="true"
      :initial-data="vehicleData"
      :lieux="lieux"
      :familles="familles"
      :fabricants="fabricants"
      :fournisseurs="fournisseurs"
      :modeles="modeles"
      @updated="handleUpdated"
      @close="handleClose"
    />
  </v-container>
</template>

<script setup>
  /** Vue d'édition d'un véhicule (US-003) : charge le véhicule et les référentiels puis délègue à VehiculeForm. */
  import { ref, onMounted } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import VehiculeForm from '@/components/Forms/VehiculeForm.vue'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'

  const route = useRoute()
  const router = useRouter()
  const api = useApi(API_BASE_URL)

  const vehicleId = route.params.id
  const vehicleData = ref(null)
  const lieux = ref([])
  const familles = ref([])
  const fabricants = ref([])
  const fournisseurs = ref([])
  const modeles = ref([])
  const loading = ref(true)
  const errorMessage = ref('')

  const loadData = async () => {
    loading.value = true
    errorMessage.value = ''
    try {
      const [vehicule, lieuxRes, famillesRes, fabricantsRes, fournisseursRes, modelesRes] =
        await Promise.all([
          api.get(`vehicules/${vehicleId}/`),
          api.get('lieux/'),
          api.get('famille-equipements/'),
          api.get('fabricants/'),
          api.get('fournisseurs/'),
          api.get('modele-equipements/'),
        ])
      vehicleData.value = vehicule
      lieux.value = lieuxRes
      familles.value = famillesRes
      fabricants.value = fabricantsRes
      fournisseurs.value = fournisseursRes
      modeles.value = modelesRes
    } catch {
      errorMessage.value = 'Erreur lors du chargement des données du véhicule.'
    } finally {
      loading.value = false
    }
  }

  const handleUpdated = () => {
    router.push({ name: 'VehicleDetail', params: { id: vehicleId } })
  }

  const handleClose = () => {
    router.push({ name: 'VehicleDetail', params: { id: vehicleId } })
  }

  onMounted(loadData)
</script>
