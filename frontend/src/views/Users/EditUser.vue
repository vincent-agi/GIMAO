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

        <UserForm
          v-if="!loading && userData"
          :title="`Modifier l'utilisateur #${userId}`"
          submit-button-text="Enregistrer les modifications"
          submit-button-color="primary"
          :is-edit="true"
          :user-id="userId"
          :initial-data="userData"
          :roles="roles"
          :current-user-id="currentUserId"
          @updated="handleUpdated"
          @close="handleClose"
          @user-sync="syncCurrentUserIfNeeded"
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
  import UserForm from '@/components/Forms/UserForm.vue'

  const route = useRoute()
  const router = useRouter()
  const store = useStore()
  const api = useApi(API_BASE_URL)

  const userId = route.params.id

  const loading = ref(false)
  const errorLoading = ref('')
  const userData = ref(null)
  const roles = ref([])

  // ID de l'utilisateur connecté
  const currentUserId = computed(() => {
    const user = store.getters.currentUser || JSON.parse(localStorage.getItem('user') || 'null')
    return user?.id ?? null
  })

  // Synchronisation avec l'utilisateur courant si c'est le même
  const syncCurrentUserIfNeeded = (updatedUser) => {
    if (!updatedUser || typeof updatedUser !== 'object') return

    const currentFromStore = store.getters.currentUser
    let currentFromStorage = null
    try {
      currentFromStorage = JSON.parse(localStorage.getItem('user') || 'null')
    } catch {
      currentFromStorage = null
    }

    const currentUser = currentFromStore || currentFromStorage
    if (!currentUser?.id || !updatedUser?.id) return

    if (String(currentUser.id) !== String(updatedUser.id)) return

    store.commit('setUser', updatedUser)
    localStorage.setItem('user', JSON.stringify(updatedUser))
  }

  const fetchUser = async () => {
    if (!userId) {
      errorLoading.value = "Impossible de modifier l'utilisateur : id manquant dans l'URL."
      return
    }

    try {
      const data = await api.get(`utilisateurs/${userId}/`)
      userData.value = {
        nomUtilisateur: data?.nomUtilisateur ?? '',
        prenom: data?.prenom ?? '',
        nomFamille: data?.nomFamille ?? '',
        email: data?.email ?? '',
        actif: !!data?.actif,
        role_id: data?.role?.id ?? null,
        photoProfil: data?.photoProfil ?? '',
      }
    } catch (error) {
      console.error("Erreur lors du chargement de l'utilisateur:", error)
      errorLoading.value = "Erreur lors du chargement de l'utilisateur."
    }
  }

  const handleUpdated = () => {
    router.push({ name: 'UserDetail', params: { id: userId } })
  }

  const handleClose = () => {
    if (!userId) {
      router.push({ name: 'UserList' })
      return
    }
    router.push({ name: 'UserDetail', params: { id: userId } })
  }

  onMounted(async () => {
    loading.value = true
    try {
      await Promise.all([
        api.get('roles/').then((data) => (roles.value = Array.isArray(data) ? data : [])),
        fetchUser(),
      ])
    } catch (error) {
      console.error('Erreur lors du chargement:', error)
      errorLoading.value = 'Erreur lors du chargement des données'
    } finally {
      loading.value = false
    }
  })
</script>
