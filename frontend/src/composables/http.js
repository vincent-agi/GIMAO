/**
 * Instance Axios préconfigurée pour l'API GIMAO.
 *
 * Comportements automatiques :
 *  - Ajoute l'en-tête `Authorization: Bearer <token>` si un token est présent dans localStorage.
 *  - Redirige vers `/login` et purge le localStorage en cas de réponse 401.
 *
 * Ne pas utiliser cette instance directement dans les composants : passer par `useApi`.
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/',
})

// 🔐 Ajout automatique du token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

// Gestion des erreurs globales
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('authTimestamp')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
