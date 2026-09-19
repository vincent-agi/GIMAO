<template>
  <v-container fluid class="fill-height" style="background: var(--background-color)">
    <v-row justify="center" align="center">
      <v-col cols="12" sm="6" md="4">
        <v-card class="pa-6">
          <v-card-title class="text-center text-h5 mb-4"> Définir votre mot de passe </v-card-title>

          <v-card-text>
            <v-alert type="info" class="mb-4">
              Bienvenue <strong>{{ username }}</strong
              >, définissez votre mot de passe.
            </v-alert>

            <v-form @submit.prevent="setPassword">
              <v-text-field
                v-model="nouveau_motDePasse"
                label="Nouveau mot de passe"
                type="password"
                variant="outlined"
                class="mb-3"
              />

              <v-text-field
                v-model="confirmation"
                label="Confirmer le mot de passe"
                type="password"
                variant="outlined"
                class="mb-3"
              />

              <v-alert v-if="error" type="error" class="mb-3">
                {{ error }}
              </v-alert>

              <v-btn type="submit" color="primary" block size="large" :loading="loading">
                Confirmer
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'

  export default {
    name: 'SetPassword',

    data() {
      return {
        username: this.$route.query.username || '',
        nouveau_motDePasse: '',
        confirmation: '',
        error: '',
        loading: false,
        api: useApi(API_BASE_URL),
      }
    },

    methods: {
      async setPassword() {
        this.error = ''

        if (!this.nouveau_motDePasse) {
          this.error = 'Le mot de passe est requis'
          return
        }

        if (this.nouveau_motDePasse !== this.confirmation) {
          this.error = 'Les mots de passe ne correspondent pas'
          return
        }

        if (this.nouveau_motDePasse.length < 8) {
          this.error = 'Le mot de passe doit contenir au moins 8 caractères'
          return
        }

        this.loading = true

        try {
          const response = await this.api.post('utilisateurs/definir_mot_de_passe/', {
            nomUtilisateur: this.username,
            nouveau_motDePasse: this.nouveau_motDePasse,
            nouveau_motDePasse_confirmation: this.confirmation,
          })

          // Stocker l'utilisateur et rediriger
          this.$store.commit('setUser', response.utilisateur)
          this.$store.commit('setToken', response.token)
          this.$router.push('/')
        } catch (err) {
          if (err.response?.detail) {
            this.error = err.response.detail
          } else {
            this.error = 'Erreur lors de la définition du mot de passe'
          }
        } finally {
          this.loading = false
        }
      },
    },
  }
</script>
