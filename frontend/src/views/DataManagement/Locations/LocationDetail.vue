<template>
  <v-app>
    <v-main>
      <v-container>
        <v-alert v-if="loading" type="info" variant="tonal" class="mb-4">
          <v-progress-circular indeterminate size="20" class="mr-2"></v-progress-circular>
          Chargement des données...
        </v-alert>

        <v-alert v-else-if="error" type="error" class="mb-4">
          {{ error }}
        </v-alert>

        <v-card v-else-if="location">
          <v-card-title>Détails du Lieu</v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item>
                <v-list-item-title class="font-weight-bold">Nom du Lieu</v-list-item-title>
                <v-list-item-subtitle>{{ location.nomLieu }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title class="font-weight-bold">Type du Lieu</v-list-item-title>
                <v-list-item-subtitle>{{ location.typeLieu }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item v-if="location.lieuParent">
                <v-list-item-title class="font-weight-bold">Lieu Parent</v-list-item-title>
                <v-list-item-subtitle>{{ location.lieuParent.nomLieu }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item v-if="location.lienPlan">
                <v-list-item-title class="font-weight-bold">Lien du Plan</v-list-item-title>
                <v-list-item-subtitle>
                  <a :href="location.lienPlan" target="_blank">{{ location.lienPlan }}</a>
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
          <v-card-actions>
            <v-btn color="primary" @click="goBack">
              <v-icon left>mdi-arrow-left</v-icon>
              Retour
            </v-btn>
            <v-spacer />
            <v-btn
              v-if="canEdit"
              color="primary"
              variant="flat"
              prepend-icon="mdi-pencil"
              @click="openEditDialog"
            >
              Modifier
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-container>
    </v-main>

    <!-- Dialog de modification du lieu -->
    <v-dialog v-model="showEditDialog" max-width="600" scrollable>
      <v-card>
        <v-card-text class="pa-6">
          <LieuForm
            title="Modifier le lieu"
            submit-button-text="Enregistrer"
            :is-edit="true"
            :initial-data="editData"
            :locations="locations"
            @updated="onUpdated"
            @close="showEditDialog = false"
          />
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<script setup>
  import { useApi } from '@/composables/useApi'
  import { ref, computed, onMounted } from 'vue'
  import { useStore } from 'vuex'
  import { useRouter, useRoute } from 'vue-router'
  import { API_BASE_URL } from '@/utils/constants'
  import LieuForm from '@/components/Forms/LieuForm.vue'

  const router = useRouter()
  const route = useRoute()
  const store = useStore()
  const api = useApi(API_BASE_URL)

  const location = ref(null)
  const loading = ref(false)
  const error = ref('')
  const showEditDialog = ref(false)
  const locations = ref([])

  const canEdit = computed(() => store.getters.hasPermission('loc:edit'))

  const editData = computed(() => {
    if (!location.value) return {}
    return {
      id: location.value.id,
      nomLieu: location.value.nomLieu || '',
      typeLieu: location.value.typeLieu || '',
      lienPlan: location.value.lienPlan || '',
      lieuParent: location.value.lieuParent?.id || location.value.lieuParent || null,
    }
  })

  const fetchLocation = async () => {
    loading.value = true
    error.value = ''

    try {
      location.value = await api.get(`lieux/${route.params.id}/`)
    } catch (err) {
      console.error('Error loading the location:', err)
      error.value = 'Erreur lors du chargement du lieu'
    } finally {
      loading.value = false
    }
  }

  const fetchLocations = async () => {
    try {
      locations.value = await api.get('lieux/hierarchy/')
    } catch (err) {
      console.error('Error loading locations hierarchy:', err)
    }
  }

  const openEditDialog = () => {
    showEditDialog.value = true
  }

  const onUpdated = async () => {
    showEditDialog.value = false
    await fetchLocation()
  }

  const goBack = () => {
    router.back()
  }

  onMounted(() => {
    fetchLocation()
    fetchLocations()
  })
</script>
