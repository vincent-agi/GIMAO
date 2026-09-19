<template>
  <ConsommableForm
    v-if="consumable"
    :initial-data="consumable"
    @updated="handleConsommableUpdate"
    @close="handleClose"
  />
  <div v-else class="d-flex justify-center align-center fill-height">
    <v-progress-circular indeterminate color="primary"></v-progress-circular>
  </div>
</template>

<script setup>
  import ConsommableForm from '@/components/Forms/ConsommableForm.vue'
  import { ref, onMounted } from 'vue'
  import { useRouter, useRoute } from 'vue-router'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'

  const router = useRouter()
  const route = useRoute()
  const api = useApi(API_BASE_URL)

  const consumable = ref(null)

  const fetchConsumable = async () => {
    try {
      const response = await api.get(`consommables/${route.params.id}/`)
      consumable.value = response
    } catch (error) {
      console.error('Erreur chargement consommable', error)
      // Redirect or show error?
      // router.push('/stocks/consommables');
    }
  }

  const handleConsommableUpdate = () => {
    router.go(-1)
  }

  const handleClose = () => {
    router.go(-1)
  }

  onMounted(() => {
    fetchConsumable()
  })
</script>
