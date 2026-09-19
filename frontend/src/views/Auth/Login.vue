<template>
  <v-container fluid class="fill-height" style="background: var(--background-color)">
    <v-row justify="center" align="center">
      <v-col cols="12" sm="6" md="4">
        <v-card class="pa-6">
          <v-alert v-if="message" type="warning" class="mb-3">
            {{ message }}
          </v-alert>

          <v-card-title class="text-center text-h5 mb-4"> Connexion GIMAO </v-card-title>

          <v-card-text>
            <v-form @submit.prevent="login">
              <FormField
                v-model="nomUtilisateur"
                class="mb-4"
                label="Nom d'utilisateur"
                type="text"
                required
              />

              <FormField
                v-if="showPasswordField"
                ref="passwordFieldRef"
                v-model="motDePasse"
                class="mb-4"
                label="Mot de passe"
                type="password"
                required
              />

              <v-alert v-if="error" type="error" class="mb-3">
                {{ error }}
              </v-alert>

              <v-btn type="submit" color="primary" block size="large" :loading="loading">
                Se connecter
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
  import { ref, nextTick } from 'vue'
  import { useRouter } from 'vue-router'
  import { useStore } from 'vuex'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'
  import FormField from '@/components/Forms/inputType/FormField.vue'

  const router = useRouter()
  const store = useStore()
  const api = useApi(API_BASE_URL)

  const showPasswordField = ref(false)

  const nomUtilisateur = ref('')
  const motDePasse = ref('')
  const error = ref('')
  const loading = ref(false)
  const passwordFieldRef = ref(null)

  const message = ref(history.state?.message || null)

  const focusPasswordField = async () => {
    await nextTick()
    const input = passwordFieldRef.value?.$el?.querySelector('input')
    input?.focus()
  }

  const login = async () => {
    error.value = ''
    loading.value = true
    message.value = null

    if (showPasswordField.value) {
      await loginWithPassword()
    } else {
      // Vérifier l'existence de l'utilisateur
      await checkUserExistence()
    }
  }

  const loginWithPassword = async () => {
    try {
      const response = await api.post('utilisateurs/login/', {
        nomUtilisateur: nomUtilisateur.value,
        motDePasse: motDePasse.value,
      })

      // Si besoin de définir le mot de passe
      if (response.besoinDefinirMotDePasse) {
        router.push({
          name: 'SetPassword',
          query: { username: nomUtilisateur.value },
        })
        return
      }

      // Connexion réussie
      store.commit('setUser', response.utilisateur)
      store.commit('setToken', response.token)

      localStorage.setItem('token', response.token)

      router.push('/')
    } catch (err) {
      if (err.response?.detail) {
        error.value = err.response.detail
      } else {
        error.value = 'Mot de passe incorrect'
      }
    } finally {
      loading.value = false
    }
  }

  const checkUserExistence = async () => {
    try {
      const response = await api.post('utilisateurs/exists/', {
        nomUtilisateur: nomUtilisateur.value,
      })

      if (response.existe) {
        showPasswordField.value = true
        loading.value = false
        await focusPasswordField()
      } else {
        if (response.message && response.message.length > 0) {
          error.value = response.message
          loading.value = false
        } else {
          router.push({
            name: 'SetPassword',
            query: { username: nomUtilisateur.value },
          })
        }
      }
    } catch {
      error.value = 'Erreur de connexion'
      loading.value = false
    }
  }
</script>
