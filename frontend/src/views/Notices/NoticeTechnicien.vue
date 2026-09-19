<template>
  <div class="py-2">
    <!-- Intro -->
    <div class="text-body-2 mb-4">
      En tant que technicien, vous réalisez les interventions sur les équipements. Vous pouvez
      signaler des pannes, gérer vos bons de travail et consulter les équipements et les stocks.
      <br /><br />
      L'application distingue deux profils de technicien : le <strong>Technicien prod</strong>, qui
      traite les bons de travail qui lui sont assignés, et le
      <strong>Technicien maintenance</strong>, qui dispose en plus de l'accès au calendrier des
      maintenances et à la création des plans de maintenance préventive.
    </div>

    <!-- Sélecteur de sous-profil -->
    <v-btn-toggle v-model="subRole" mandatory color="primary" class="mb-4" density="comfortable">
      <v-btn value="Technicien prod">Technicien prod</v-btn>
      <v-btn value="Technicien maintenance">Technicien maintenance</v-btn>
    </v-btn-toggle>

    <!-- Onglets -->
    <v-tabs v-model="tab" class="mb-4" show-arrows="always">
      <v-tab value="connexion">Connexion</v-tab>
      <v-tab value="dashboard">Tableau de bord</v-tab>
      <v-tab value="di">Demandes d'intervention</v-tab>
      <v-tab value="bt">Bons de travail</v-tab>
      <v-tab value="equipements">Équipements</v-tab>
      <v-tab value="stock">Stocks</v-tab>
    </v-tabs>

    <v-window v-model="tab">
      <v-window-item value="connexion">
        <ConnexionTab :has-menu="true" role="technicien" />
      </v-window-item>

      <v-window-item value="dashboard">
        <DashboardTab :role="subRole" />
      </v-window-item>

      <v-window-item value="di">
        <DIGeneralTab :role="subRole" />
      </v-window-item>

      <v-window-item value="bt">
        <BTGeneralTab :role="subRole" />
      </v-window-item>

      <v-window-item value="equipements">
        <EquipementsTab :role="subRole" />
      </v-window-item>

      <v-window-item value="stock">
        <StockGeneralTab :role="subRole" />
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
  import BTGeneralTab from './BT/BTGeneralTab.vue'
  import StockGeneralTab from './Stock/StockGeneralTab.vue'

  const subRole = ref('Technicien prod')
  const tab = ref('dashboard')
</script>
