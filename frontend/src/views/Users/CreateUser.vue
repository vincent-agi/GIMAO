<template>
  <v-app>
    <v-main>
      <v-container>
        <v-alert v-if="loadingData" type="info" variant="tonal" class="mb-4">
          <v-progress-circular indeterminate size="20" class="mr-2"></v-progress-circular>
          Chargement des données...
        </v-alert>

        <UserForm
          v-if="!loadingData"
          title="Créer un utilisateur"
          submit-button-text="Créer l'utilisateur"
          submit-button-color="success"
          :roles="roles"
          @created="handleCreated"
          @close="handleClose"
        />
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
  import { onMounted, ref } from 'vue'
  import { useRouter } from 'vue-router'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'
  import UserForm from '@/components/Forms/UserForm.vue'

  const router = useRouter()
  const api = useApi(API_BASE_URL)

  const loadingData = ref(false)
  const roles = ref([])

  const fetchData = async () => {
    loadingData.value = true
    try {
      const rolesResponse = await api.get('roles/')
      roles.value = Array.isArray(rolesResponse) ? rolesResponse : []
    } catch (error) {
      console.error('Erreur lors du chargement des rôles:', error)
    } finally {
      loadingData.value = false
    }
  }

  const handleCreated = (newUser) => {
    if (newUser?.id) {
      router.push({ name: 'UserDetail', params: { id: newUser.id } })
    } else {
      router.push({ name: 'UserList' })
    }
  }

  const handleClose = () => {
    router.push({ name: 'UserList' })
  }

  onMounted(() => {
    fetchData()
  })
</script>
