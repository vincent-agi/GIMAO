<template>
  <div class="py-2">
    <!-- Intro -->
    <div class="text-body-2 mb-4">
      En tant qu'opérateur, votre rôle principal est de signaler les pannes constatées sur les
      équipements et d'en suivre le traitement. Vous n'avez pas accès aux stocks ni à la gestion des
      comptes.
    </div>

    <!-- Onglets -->
    <v-tabs v-model="tab" class="mb-4" show-arrows="always">
      <v-tab value="connexion">Connexion</v-tab>
      <v-tab value="dashboard">Tableau de bord</v-tab>
      <v-tab value="di">Demandes d'intervention</v-tab>
      <v-tab value="equipements">Équipements</v-tab>
    </v-tabs>

    <v-window v-model="tab">
      <v-window-item value="connexion">
        <ConnexionTab :has-menu="false" role="operateur" />
      </v-window-item>

      <v-window-item value="dashboard">
        <DashboardTab role="Opérateur prod" />
      </v-window-item>

      <v-window-item value="di">
        <DIGeneralTab role="Opérateur prod" />
      </v-window-item>

      <v-window-item value="equipements">
        <EquipementsTab role="Opérateur prod" />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup>
  import { ref } from 'vue'

  import DashboardTab from './Dashboard/DashboardTab.vue'
  import DIGeneralTab from './DI/DIGeneralTab.vue'
  import EquipementsTab from './Equipments/EquipementsTab.vue'
  import ConnexionTab from './Auth/ConnexionTab.vue'

  const tab = ref('dashboard')
</script>
