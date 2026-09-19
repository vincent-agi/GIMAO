<template>
  <div class="py-2">
    <!-- Intro -->
    <div class="text-body-2 mb-4">
      En tant que magasinier, vous gérez les stocks de pièces détachées et consommables de
      l'entreprise.
    </div>

    <!-- Onglets -->
    <v-tabs v-model="tab" class="mb-4" show-arrows="always">
      <v-tab value="connexion">Connexion</v-tab>
      <v-tab value="dashboard">Tableau de bord</v-tab>
      <v-tab value="stock">Consommables</v-tab>
    </v-tabs>

    <v-window v-model="tab">
      <v-window-item value="connexion">
        <ConnexionTab :has-menu="true" role="magasinier" />
      </v-window-item>

      <v-window-item value="dashboard">
        <v-container class="doc-page">
          <div class="text-body-2 mt-2">
            Après la connexion, votre tableau de bord s'affiche automatiquement. Il centralise les
            informations liées à la gestion des stocks et des consommables.
            <br /><br />

            <ZoomImage
              v-if="dashboardMagasinierImg"
              :src="dashboardMagasinierImg"
              alt="Tableau de bord magasinier"
            />
          </div>
        </v-container>
      </v-window-item>

      <v-window-item value="stock">
        <StockGeneralTab role="Magasinier" />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup>
  import { ref } from 'vue'

  import ConnexionTab from './Auth/ConnexionTab.vue'
  import StockGeneralTab from './Stock/StockGeneralTab.vue'
  import ZoomImage from './common/ZoomImage.vue'

  const tab = ref('dashboard')

  const getImg = (name) => {
    try {
      return require(`@/assets/images/notices/magasinier/${name}`)
    } catch {
      return null
    }
  }

  const dashboardMagasinierImg = getImg('dashboard-magasinier.png')
</script>
