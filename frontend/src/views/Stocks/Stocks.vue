<template>
  <ConsommableList
    title="Stock de consommables"
    create-button-text="Ajouter un consommable"
    @create="handleCreate"
    @row-click="handleRowClick"
  />
</template>

<script setup>
  import { useRouter } from 'vue-router'
  import ConsommableList from '@/components/ConsommableList.vue'

  const router = useRouter()

  const handleCreate = () => {
    router.push({
      name: 'CreateConsumable',
      query: { from: 'stocks' },
    })
  }

  const handleRowClick = (item) => {
    router.push({ name: 'ConsumableDetail', params: { id: item.id } })
  }
</script>
