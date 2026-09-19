<template>
  <div class="py-2">
    <!-- Intro -->
    <div class="text-body-2 mb-4">
      En tant que responsable GMAO, vous avez un accès complet à l'application : gestion des
      demandes d'intervention, planification des bons de travail, supervision des équipements et des
      stocks, administration des utilisateurs et autres paramètres.
    </div>

    <!-- Onglets -->
    <v-tabs v-model="tab" class="mb-4" show-arrows="always">
      <v-tab value="connexion">Connexion</v-tab>
      <v-tab value="dashboard">Tableau de bord</v-tab>
      <v-tab value="di">Demandes d'intervention</v-tab>
      <v-tab value="bt">Bons de travail</v-tab>
      <v-tab value="equipements">Équipements</v-tab>
      <v-tab value="stock">Stocks</v-tab>
      <v-tab value="roles">Gestion des rôles</v-tab>
      <v-tab value="donnees">Données secondaires</v-tab>
    </v-tabs>

    <v-window v-model="tab">
      <v-window-item value="connexion">
        <ConnexionTab :has-menu="true" role="responsable" />
      </v-window-item>

      <v-window-item value="dashboard">
        <DashboardTab role="Responsable GMAO" />
      </v-window-item>

      <v-window-item value="di">
        <DIGeneralTab role="Responsable GMAO" />
      </v-window-item>

      <v-window-item value="bt">
        <BTGeneralTab role="Responsable GMAO" />
      </v-window-item>

      <v-window-item value="equipements">
        <EquipementsTab role="Responsable GMAO" />
      </v-window-item>

      <v-window-item value="stock">
        <StockGeneralTab role="Responsable GMAO" />
      </v-window-item>

      <v-window-item value="roles">
        <RolesManagementTab />
      </v-window-item>

      <v-window-item value="donnees">
        <SecondaryDataTab />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup>
  import { ref } from 'vue'

  import ConnexionTab from './Auth/ConnexionTab.vue'
  import DashboardTab from './Dashboard/DashboardTab.vue'
  import DIGeneralTab from './DI/DIGeneralTab.vue'
  import EquipementsTab from './Equipments/EquipementsTab.vue'
  import BTGeneralTab from './BT/BTGeneralTab.vue'
  import StockGeneralTab from './Stock/StockGeneralTab.vue'
  import RolesManagementTab from './Admin/RolesManagementTab.vue'
  import SecondaryDataTab from './Admin/SecondaryDataTab.vue'

  const tab = ref('dashboard')
</script>
