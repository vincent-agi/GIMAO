import { createStore } from 'vuex'
import http from '@/composables/http'

export default createStore({
  state: {
    user: null,
    token: null,
    isAuthenticated: false,
    authTimestamp: null,
  },

  mutations: {
    setUser(state, user) {
      state.user = user
      state.isAuthenticated = !!user
      state.authTimestamp = Math.floor(Date.now() / 1000)

      localStorage.setItem('user', JSON.stringify(user))
      localStorage.setItem('authTimestamp', state.authTimestamp)
    },

    setToken(state, token) {
      state.token = token
      localStorage.setItem('token', token)
    },

    restoreAuth(state, { user, timestamp }) {
      state.user = user
      state.isAuthenticated = true
      state.authTimestamp = timestamp
    },

    logout(state) {
      state.user = null
      state.token = null
      state.isAuthenticated = false
      state.authTimestamp = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('authTimestamp')
    },
  },

  actions: {
    initAuth({ commit }) {
      const user = localStorage.getItem('user')
      const token = localStorage.getItem('token')
      const timestamp = localStorage.getItem('authTimestamp')

      if (user && token) {
        try {
          const parsedTimestamp = Number.parseInt(timestamp || '', 10)
          const parsedUser = JSON.parse(user)
          commit('restoreAuth', {
            user: parsedUser,
            timestamp: Number.isFinite(parsedTimestamp) ? parsedTimestamp : null,
          })

          // Le rôle/les permissions affichés au login peuvent avoir été modifiés
          // entre-temps par un responsable : on rafraîchit depuis le serveur plutôt
          // que de garder indéfiniment la version mise en cache dans le navigateur.
          if (parsedUser?.id) {
            http
              .get(`utilisateurs/${parsedUser.id}/`)
              .then((response) => {
                commit('setUser', response.data)
              })
              .catch(() => {
                // Pas de connexion / erreur réseau : on garde la version en cache.
              })
          }
        } catch (e) {
          console.error("Erreur lors du chargement de l'utilisateur:", e)
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          localStorage.removeItem('authTimestamp')
        }
      }
    },

    logout({ commit }) {
      commit('logout')
    },
  },

  getters: {
    isAuthenticated: (state) => state.isAuthenticated,
    currentUser: (state) => state.user,
    userRole: (state) => state.user?.role?.nomRole || null,
    authenticationDate: (state) =>
      state.authTimestamp ? new Date(state.authTimestamp * 1000) : null,
    hasValidAuthentication: (state) => {
      return state.isAuthenticated && !!localStorage.getItem('token')
    },
    userPermissions: (state) => state.user?.permissions_names || [],
    hasPermission: (state, getters) => (perm) => {
      if (!state.isAuthenticated) return false
      return getters.userPermissions.includes(perm)
    },
  },

  modules: {},
})

export function checkAuthValidity(_store) {
  return !!localStorage.getItem('token')
}
