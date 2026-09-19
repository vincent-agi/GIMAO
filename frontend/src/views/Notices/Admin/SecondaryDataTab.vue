<template>
  <v-container class="doc-page">
    <div class="text-body-2 mt-2">
      Les données secondaires sont les référentiels de base utilisés dans GIMAO : lieux,
      fournisseurs, fabricants et modèles d'équipement. Elles sont accessibles depuis le menu
      correspondant et doivent être renseignées avant de créer des équipements.
      <br /><br />

      <!-- LIEUX -->
      <h4 class="mb-2">Lieux</h4>
      Les lieux représentent l'arborescence physique de votre entreprise (bâtiments, ateliers,
      zones). Ils permettent de localiser précisément chaque équipement.
      <ul class="ml-4 mt-2 mb-4">
        <li>Cliquez sur <strong>Lieux</strong> dans le menu pour afficher la liste.</li>
        <li>
          Vous pouvez créer un lieu en cliquant sur <strong>Ajouter</strong>, en saisissant son nom
          et en lui associant éventuellement un lieu parent pour construire l'arborescence.
        </li>
        <li>Les lieux sont utilisés lors de la création ou modification d'un équipement.</li>
      </ul>

      <ZoomImage v-if="rubriqueLieuImg" :src="rubriqueLieuImg" alt="Rubrique Lieux dans le menu" />
      <ZoomImage v-if="listeLieuxImg" :src="listeLieuxImg" alt="Liste des lieux" />

      <!-- FOURNISSEURS -->
      <h4 class="mb-2 mt-4">Fournisseurs</h4>
      Les fournisseurs correspondent aux entreprises auprès desquelles vous achetez vos équipements
      ou pièces détachées.
      <ul class="ml-4 mt-2 mb-4">
        <li>Accédez à la liste via le menu <strong>Fournisseurs</strong>.</li>
        <li>Ajoutez un fournisseur en renseignant son nom et ses coordonnées.</li>
        <li>Les fournisseurs sont associés aux consommables dans la gestion des stocks.</li>
      </ul>

      <ZoomImage
        v-if="rubriqueFournisseursImg"
        :src="rubriqueFournisseursImg"
        alt="Rubrique Fournisseurs dans le menu"
      />
      <ZoomImage
        v-if="listeFournisseursImg"
        :src="listeFournisseursImg"
        alt="Liste des fournisseurs"
      />

      <!-- FABRICANTS -->
      <h4 class="mb-2 mt-4">Fabricants</h4>
      Les fabricants désignent les constructeurs des équipements de votre parc.
      <ul class="ml-4 mt-2 mb-4">
        <li>Accédez à la liste via le menu <strong>Fabricants</strong>.</li>
        <li>Chaque fabricant peut être associé à un ou plusieurs modèles d'équipement.</li>
      </ul>

      <ZoomImage
        v-if="rubriqueFabricantsImg"
        :src="rubriqueFabricantsImg"
        alt="Rubrique Fabricants dans le menu"
      />
      <ZoomImage v-if="listeFabricantsImg" :src="listeFabricantsImg" alt="Liste des fabricants" />

      <!-- MODÈLES D'ÉQUIPEMENT -->
      <h4 class="mb-2 mt-4">Modèles d'équipement</h4>
      Les modèles regroupent les caractéristiques communes à plusieurs équipements du même type
      (référence constructeur, fabricant associé).
      <ul class="ml-4 mt-2 mb-4">
        <li>Accédez à la liste via le menu <strong>Modèles d'équipement</strong>.</li>
        <li>
          Créez un modèle en indiquant sa désignation, sa référence et le fabricant correspondant.
        </li>
        <li>Lors de la création d'un équipement, vous pouvez le rattacher à un modèle existant.</li>
      </ul>

      <ZoomImage
        v-if="rubriqueModeleImg"
        :src="rubriqueModeleImg"
        alt="Rubrique Modèles dans le menu"
      />
      <ZoomImage
        v-if="listeModelesImg"
        :src="listeModelesImg"
        alt="Liste des modèles d'équipement"
      />
    </div>
  </v-container>
</template>

<script setup>
  import ZoomImage from '../common/ZoomImage.vue'

  const getImg = (name) => {
    try {
      return require(`@/assets/images/notices/admin/${name}`)
    } catch {
      return null
    }
  }

  const rubriqueLieuImg = getImg('rubrique-lieu.png')
  const listeLieuxImg = getImg('liste-lieux.png')
  const rubriqueFournisseursImg = getImg('rubrique-fournisseurs.png')
  const listeFournisseursImg = getImg('liste-fournisseurs.png')
  const rubriqueFabricantsImg = getImg('rubrique-fabricants.png')
  const listeFabricantsImg = getImg('liste-fabricants.png')
  const rubriqueModeleImg = getImg('rubrique-modele-equipement.png')
  const listeModelesImg = getImg('liste-modeles.png')
</script>

<style scoped>
  .doc-page {
    padding: 0;
  }
  ul li {
    margin-bottom: 8px;
  }
</style>
