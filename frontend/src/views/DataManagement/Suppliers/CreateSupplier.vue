<template>
  <v-container>
    <FournisseurForm
      title="Créer un fournisseur"
      submit-button-text="Créer le fournisseur"
      @created="handleCreated"
      @close="handleClose"
    />
  </v-container>
</template>

<script setup>
  import { useRouter } from 'vue-router'
  import FournisseurForm from '@/components/Forms/FournisseurForm.vue'

  const router = useRouter()

  const handleCreated = (newFournisseur) => {
    router.push({
      name: 'SupplierDetail',
      params: { id: newFournisseur.id },
    })
  }

  const handleClose = () => {
    router.back()
  }
</script>
