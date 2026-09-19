<template>
  <v-container class="doc-page">
    <h4>Consulter la liste des stocks</h4>

    <div class="text-body-2 mb-4 mt-2">
      La rubrique <strong>Stocks</strong> offre une vue globale sur l'ensemble des pièces détachées
      et consommables. Cette liste vous permet d'anticiper vos besoins ou de vérifier les
      disponibilités. <br /><br />

      <strong>Informations disponibles dans la liste :</strong>
      <ul class="ml-4 mt-2 mb-4">
        <li>
          <strong>Statistiques :</strong> des indicateurs visuels du niveau global affichant les
          consommables hors stock, sous le seuil critique, et ceux avec un stock suffisant.
        </li>
        <li>
          <strong>Détails par consommable :</strong> pour chaque élément de la liste, vous retrouvez
          directement le nom du consommable, le magasin où il est localisé, ainsi que la quantité
          disponible.
        </li>
      </ul>

      <strong>Droits et permissions :</strong>
      <ul class="ml-4 mt-2 mb-4">
        <li>
          <strong>Consultation :</strong> vous pouvez à tout moment vérifier la présence d'une pièce
          et son niveau de stock en lisant simplement cette liste.
        </li>
        <li v-if="!roleIsAbove('Magasinier')">
          <strong>Modification :</strong> en tant que technicien, toute modification manuelle des
          quantités du stock vous est impossible. L'entrée de nouvelles quantités en stock ou
          l'ajustement manuel ne peuvent être effectués que par le magasinier ou le responsable. Le
          technicien n'influence le stock que par l'utilisation de consommables lors d'une
          intervention.
        </li>
        <li v-else>
          <strong>Modification :</strong> en tant que Magasinier ou Responsable, vous avez les
          permissions nécessaires pour ajouter manuellement des pièces ou ajuster les niveaux d'un
          produit (entrée, sortie, erreur d'inventaire).
        </li>
      </ul>
    </div>

    <ZoomImage v-if="listeStockImg" :src="listeStockImg" alt="Liste des stocks" />
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

  const roles = ['Technicien prod', 'Technicien maintenance', 'Magasinier', 'Responsable GMAO']

  const roleIsAbove = (minRole) => {
    return roles.indexOf(props.role) >= roles.indexOf(minRole)
  }

  const getStockImg = (name) => {
    try {
      return require(`@/assets/images/notices/stocks/${name}`)
    } catch {
      return null
    }
  }

  const listeStockImg = (() => {
    if (props.role === 'Responsable GMAO')
      return getStockImg('liste-stock-responsable.png') || getStockImg('liste-stock-technicien.png')
    if (props.role === 'Magasinier')
      return getStockImg('liste-stock-magasinier.png') || getStockImg('liste-stock-technicien.png')
    return getStockImg('liste-stock-technicien.png')
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
