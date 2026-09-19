<template>
  <v-expansion-panels multiple variant="accordion" class="doc-page">
    <!-- LISTE -->
    <v-expansion-panel v-if="roleIsAbove('Opérateur prod')">
      <v-expansion-panel-title> Liste des équipements </v-expansion-panel-title>

      <v-expansion-panel-text>
        <EquipmentsListTab :role="props.role" />
      </v-expansion-panel-text>
    </v-expansion-panel>

    <!-- DÉTAIL -->
    <v-expansion-panel v-if="roleIsAbove('Opérateur prod')">
      <v-expansion-panel-title> Détails d'un équipement </v-expansion-panel-title>

      <v-expansion-panel-text>
        <EquipmentDetailTab :role="role" />
      </v-expansion-panel-text>
    </v-expansion-panel>

    <!-- DÉFAILLANCE -->
    <v-expansion-panel v-if="roleIsAbove('Opérateur prod')">
      <v-expansion-panel-title> Signaler une défaillance </v-expansion-panel-title>

      <v-expansion-panel-text>
        <SignalFailureTab :role="role" />
      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>
</template>

<script setup>
  import EquipmentsListTab from './EquipmentsListTab.vue'
  import EquipmentDetailTab from './EquipmentDetailTab.vue'
  import SignalFailureTab from './SignalFailureTab.vue'

  const props = defineProps({
    role: {
      type: String,
      default: 'Opérateur prod',
    },
  })

  const roles = ['Opérateur prod', 'Technicien prod', 'Technicien maintenance', 'Responsable GMAO']

  const roleIsAbove = (minRole) => {
    return roles.indexOf(props.role) >= roles.indexOf(minRole)
  }
</script>

<style scoped>
  .doc-page {
    max-width: 80%;
    margin: auto;
    margin-bottom: 2rem;
  }
</style>
