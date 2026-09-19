<template>
  <BaseDetailView
    :data="supplierData"
    :loading="isLoading"
    :error-message="errorMessage"
    :title="'Détail du fournisseur'"
    :success-message="successMessage"
    :auto-display="false"
    :show-edit-button="false"
    @delete="handleDelete"
    @clear-error="errorMessage = ''"
    @clear-success="successMessage = ''"
  >
    <template #default="{ data }">
      <v-row v-if="data" dense>
        <!-- Informations générales -->
        <v-col cols="12">
          <h3 class="text-h6 mb-3">Informations générales</h3>
        </v-col>

        <v-col cols="12" md="6">
          <strong>Nom</strong>
          <div>{{ data.nom }}</div>
        </v-col>

        <v-col cols="12" md="6">
          <strong>Email</strong>
          <div>{{ data.email }}</div>
        </v-col>

        <v-col cols="12" md="6">
          <strong>Téléphone</strong>
          <div>{{ data.numTelephone }}</div>
        </v-col>

        <v-col cols="12" md="6">
          <strong>Service après-vente</strong>
          <div>
            <v-chip
              :color="data.serviceApresVente ? 'success' : 'error'"
              variant="outlined"
              size="small"
            >
              {{ data.serviceApresVente ? 'Oui' : 'Non' }}
            </v-chip>
          </div>
        </v-col>

        <!-- Adresse -->
        <v-col cols="12" class="mt-4">
          <h3 class="text-h6 mb-3">Adresse</h3>
        </v-col>

        <template v-if="data.adresse">
          <v-col cols="12" md="6">
            <strong>Rue</strong>
            <div>{{ data.adresse.numero }} {{ data.adresse.rue }}</div>
          </v-col>

          <v-col cols="12" md="6">
            <strong>Complément</strong>
            <div>
              {{ data.adresse.complement || '-' }}
            </div>
          </v-col>

          <v-col cols="12" md="6">
            <strong>Ville</strong>
            <div>{{ data.adresse.ville }}</div>
          </v-col>

          <v-col cols="12" md="6">
            <strong>Code postal</strong>
            <div>{{ data.adresse.code_postal }}</div>
          </v-col>

          <v-col cols="12" md="6">
            <strong>Pays</strong>
            <div>{{ data.adresse.pays }}</div>
          </v-col>
        </template>

        <v-col v-else cols="12">
          <span class="text-grey">Aucune adresse renseignée</span>
        </v-col>
      </v-row>

      <v-row v-else>
        <v-col>
          <v-alert type="info" outlined> Aucune donnée disponible pour ce fournisseur. </v-alert>
        </v-col>
      </v-row>
    </template>
  </BaseDetailView>

  <!-- Bouton flottant pour modifier -->
  <v-btn
    v-if="store.getters.hasPermission('sup:edit')"
    color="primary"
    size="large"
    icon
    class="floating-edit-button"
    elevation="4"
    @click="editSupplier"
  >
    <v-icon size="large">mdi-pencil</v-icon>
    <v-tooltip activator="parent" location="left"> Modifier le fournisseur </v-tooltip>
  </v-btn>
</template>

<script setup>
  import { onMounted, ref } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import { useStore } from 'vuex'
  import BaseDetailView from '@/components/common/BaseDetailView.vue'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants.js'

  // Données
  const route = useRoute()
  const router = useRouter()
  const store = useStore()
  const supplierId = route.params.id
  const supplierData = ref(null)
  const isLoading = ref(true)
  const api = useApi(API_BASE_URL)

  onMounted(async () => {
    loadSupplierData()
  })

  const loadSupplierData = async () => {
    isLoading.value = true
    try {
      supplierData.value = await api.get(`fournisseurs/${supplierId}`)
    } catch (error) {
      console.error('Error loading supplier data:', error)
    } finally {
      isLoading.value = false
    }
  }

  const editSupplier = () => {
    router.push({
      name: 'EditSupplier',
      params: { id: supplierId },
    })
  }
</script>

<style scoped>
  .floating-edit-button {
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 1000;
  }
</style>
