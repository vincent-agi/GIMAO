<template>
  <ConsommableForm @created="handleConsommableCreate" @close="handleClose" />
</template>

<script setup>
  import ConsommableForm from '@/components/Forms/ConsommableForm.vue'
  import { useRouter } from 'vue-router'

  const router = useRouter()

  // Handling des events émis par le formulaire
  const handleConsommableCreate = () => {
    router.go(-1)
  }

  const handleClose = () => {
    router.go(-1)
  }
</script>
