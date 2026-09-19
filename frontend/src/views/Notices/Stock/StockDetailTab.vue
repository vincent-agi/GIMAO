<template>
  <v-container class="doc-page">
    <h4>Détails et traçabilité d'un consommable</h4>

    <div class="text-body-2 mb-4 mt-2">
      En cliquant sur une pièce spécifique depuis la liste des stocks, vous accédez à sa
      <strong>fiche détaillée</strong>. Cette fiche centralise les informations essentielles à la
      gestion de la pièce. <br /><br />

      <strong>Contenu de la fiche d'un consommable :</strong>
      <ul class="ml-4 mt-2 mb-4">
        <li>
          <strong>Section Informations :</strong> récapitule les données globales comme le nom du
          consommable, le seuil de stock faible pour les alertes, ainsi que la quantité totale
          disponible.
        </li>
        <li>
          <strong>Section Stocks en magasin :</strong> présente sous forme de tableau la répartition
          du matériel, détaillant pour chaque magasin concerné la quantité présente physiquement.
        </li>
        <li>
          <strong>Section Historique des achats :</strong> permet de retracer les approvisionnements
          via un tableau indiquant la date, le fournisseur, le nom du fabriquant, la quantité
          commandée, le prix unitaire et le prix total.
        </li>
      </ul>
    </div>

    <ZoomImage v-if="detailStockImg" :src="detailStockImg" alt="Détail des stocks" />
  </v-container>
</template>

<script setup>
  import ZoomImage from '../common/ZoomImage.vue'

  const props = defineProps({
    role: {
      type: String,
      default: 'Technicien prod',
    },
  })

  const getStockImg = (name) => {
    try {
      return require(`@/assets/images/notices/stocks/${name}`)
    } catch {
      return null
    }
  }

  const detailStockImg = (() => {
    if (props.role === 'Responsable GMAO')
      return (
        getStockImg('detail-stock-responsable.png') || getStockImg('detail-stock-technicien.png')
      )
    if (props.role === 'Magasinier')
      return (
        getStockImg('detail-stock-magasinier.png') || getStockImg('detail-stock-technicien.png')
      )
    return getStockImg('detail-stock-technicien.png')
  })()
</script>

<style scoped>
  .doc-page {
    padding: 0;
  }
  ul li {
    margin-bottom: 8px;
  }
</style>
