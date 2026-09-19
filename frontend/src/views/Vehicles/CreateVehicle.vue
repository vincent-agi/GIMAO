<template>
  <v-container>
    <v-alert v-if="loadingData" type="info" variant="tonal" class="mb-4">
      <v-progress-circular indeterminate size="20" class="mr-2"></v-progress-circular>
      Chargement des données...
    </v-alert>

    <VehiculeForm
      v-if="!loadingData"
      title="Créer un véhicule"
      submit-button-text="Créer le véhicule"
      :lieux="lieux"
      :familles="familles"
      :fabricants="fabricants"
      :fournisseurs="fournisseurs"
      :modeles="modeles"
      @created="handleCreated"
      @close="handleClose"
    />
  </v-container>
</template>

<script setup>
  /** Vue de création d'un véhicule (US-002) : charge les référentiels puis délègue à VehiculeForm. */
  import { ref, onMounted } from 'vue'
  import { useRouter } from 'vue-router'
  import VehiculeForm from '@/components/Forms/VehiculeForm.vue'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'

  const router = useRouter()
  const api = useApi(API_BASE_URL)

  const lieux = ref([])
  const familles = ref([])
  const fabricants = ref([])
  const fournisseurs = ref([])
  const modeles = ref([])
  const loadingData = ref(true)

  const loadReferenceData = async () => {
    loadingData.value = true
    try {
      const [lieuxRes, famillesRes, fabricantsRes, fournisseursRes, modelesRes] = await Promise.all(
        [
          api.get('lieux/'),
          api.get('famille-equipements/'),
          api.get('fabricants/'),
          api.get('fournisseurs/'),
          api.get('modele-equipements/'),
        ]
      )
      lieux.value = lieuxRes
      familles.value = famillesRes
      fabricants.value = fabricantsRes
      fournisseurs.value = fournisseursRes
      modeles.value = modelesRes
    } catch (error) {
      console.error('Erreur lors du chargement des référentiels véhicule :', error)
    } finally {
      loadingData.value = false
    }
  }

  const handleCreated = (newVehicule) => {
    router.push({ name: 'VehicleDetail', params: { id: newVehicule.id } })
  }

  const handleClose = () => {
    router.push({ name: 'VehicleList' })
  }

  onMounted(loadReferenceData)
</script>
