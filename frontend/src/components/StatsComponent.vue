<template>
  <v-row dense>
    <v-col v-for="(stat, index) in stats" :key="index" cols="12" md="4">
      <v-card elevation="2" class="pa-4">
        <v-row align="center" justify="space-between">
          <v-col cols="8">
            <span class="font-weight-bold">
              {{ stat.label }}
            </span>
          </v-col>

          <v-col cols="4" class="text-right">
            <span class="text-h4 font-weight-bold">
              {{ stat.value }}
            </span>
          </v-col>
        </v-row>
      </v-card>
    </v-col>
  </v-row>
</template>

<script setup>
  import { ref, onMounted } from 'vue'
  import { useStore } from 'vuex'
  import { useApi } from '@/composables/useApi.js'
  import { API_BASE_URL } from '../utils/constants'

  const store = useStore()
  const api = useApi(API_BASE_URL)

  // données dynamiques
  const stats = ref([])

  // Loading / error
  const loading = ref(false)
  const error = ref(null)

  const buildUrl = () => {
    const params = new URLSearchParams()

    const userId = store.getters.currentUser.id
    params.append('userId', userId)

    return `stats/?${params.toString()}`
  }

  const fetchStats = async () => {
    loading.value = true
    error.value = null

    try {
      const url = buildUrl()
      const response = await api.get(url)

      stats.value = response.stats
    } catch (err) {
      error.value = err
      console.error(err)
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    fetchStats()
  })
</script>
