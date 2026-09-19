<template>
  <v-container class="pa-4" fluid>
    <v-row justify="center">
      <v-col cols="12" md="8" lg="6">
        <v-card class="pa-4">
          <LocationTreeView
            :items="locations"
            :show-create-button="store.getters.hasPermission('loc:create')"
            :show-edit-button="store.getters.hasPermission('loc:edit')"
            @create="createLieu"
            @edit="editLieu"
          />
        </v-card>
      </v-col>
    </v-row>

    <!-- Dialog de modification d'un lieu -->
    <v-dialog v-model="showEditDialog" max-width="600" scrollable>
      <v-card>
        <v-card-text class="pa-6">
          <LieuForm
            v-if="showEditDialog"
            title="Modifier le lieu"
            submit-button-text="Enregistrer"
            :is-edit="true"
            :initial-data="editData"
            :locations="locations"
            @updated="onLieuUpdated"
            @close="showEditDialog = false"
          />
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
  import { ref, onMounted } from 'vue'
  import { API_BASE_URL } from '@/utils/constants.js'
  import { useStore } from 'vuex'
  import { useApi } from '@/composables/useApi.js'
  import { useRouter } from 'vue-router'
  import LocationTreeView from '@/components/LocationTreeView.vue'
  import LieuForm from '@/components/Forms/LieuForm.vue'

  const api = useApi(API_BASE_URL)
  const store = useStore()
  const locations = ref([])
  const router = useRouter()
  const showEditDialog = ref(false)
  const editData = ref({})

  const fetchLocations = async () => {
    console.log('Fetching locations...')
    try {
      locations.value = await api.get('lieux/hierarchy/')
    } catch (error) {
      console.error(error)
    }
    console.log('Locations fetched:', locations.value)
  }

  onMounted(async () => {
    await fetchLocations()
  })

  // Modification d'un lieu
  const editLieu = (item) => {
    editData.value = {
      id: item.id,
      nomLieu: item.nomLieu || '',
      typeLieu: item.typeLieu || '',
      lienPlan: item.lienPlan || '',
      lieuParent: item.lieuParent?.id || item.lieuParent || null,
    }
    showEditDialog.value = true
  }

  const onLieuUpdated = async () => {
    showEditDialog.value = false
    await fetchLocations()
  }

  // Création d'un nouveau lieu
  const createLieu = (parentItemId) => {
    console.log('Creating location with parent:', parentItemId) // Debug

    // Dans LocationList
    router.push({
      name: 'CreateLocation',
      query: { parentId: parentItemId ? parentItemId : null },
    })
  }
</script>
