<template>
  <v-expansion-panels multiple variant="accordion" class="doc-page">
    <!-- CONSULTER DI -->
    <v-expansion-panel v-if="roleIsAbove('Opérateur prod')">
      <v-expansion-panel-title v-if="role === 'Opérateur prod'">
        Consulter vos demandes d'intervention
      </v-expansion-panel-title>

      <v-expansion-panel-title v-if="roleIsAbove('Technicien prod')">
        Consulter les demandes d'intervention
      </v-expansion-panel-title>

      <v-expansion-panel-text>
        <SuiviDITab :role="props.role" />
      </v-expansion-panel-text>
    </v-expansion-panel>

    <!-- CRÉER DI -->
    <v-expansion-panel v-if="roleIsAbove('Opérateur prod')">
      <v-expansion-panel-title> Créer une demande d'intervention </v-expansion-panel-title>

      <v-expansion-panel-text>
        <CreationDITab :role="role" />
      </v-expansion-panel-text>
    </v-expansion-panel>

    <!-- MODIFIER DI -->
    <v-expansion-panel v-if="roleIsAbove('Opérateur prod')">
      <v-expansion-panel-title> Modifier une demande d'intervention </v-expansion-panel-title>

      <v-expansion-panel-text>
        <ModificationDITab :role="role" />
      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>
</template>

<script setup>
  import CreationDITab from './CreationDITab.vue'
  import SuiviDITab from './SuiviDITab.vue'
  import ModificationDITab from './ModificationDITab.vue'

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
    max-width: 90%;
    margin: auto;
    margin-bottom: 2rem;
  }

  p {
    margin-bottom: 16px;
  }
</style>
