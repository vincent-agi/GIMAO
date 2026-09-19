<template>
  <v-expansion-panels multiple variant="accordion" class="doc-page">
    <!-- CONSULTER STOCKS -->
    <v-expansion-panel>
      <v-expansion-panel-title> Consulter les stocks </v-expansion-panel-title>

      <v-expansion-panel-text>
        <StockListTab :role="role" />
      </v-expansion-panel-text>
    </v-expansion-panel>

    <!-- DETAIL CONSOMMABLE -->
    <v-expansion-panel>
      <v-expansion-panel-title> Détail d'un consommable </v-expansion-panel-title>

      <v-expansion-panel-text>
        <StockDetailTab />
      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>
</template>

<script setup>
  import StockListTab from './StockListTab.vue'
  import StockDetailTab from './StockDetailTab.vue'

  defineProps({
    role: {
      type: String,
      default: 'Technicien prod',
    },
  })
</script>

<style scoped>
  .doc-page {
    max-width: 90%;
    margin: auto;
    margin-bottom: 2rem;
  }
</style>
