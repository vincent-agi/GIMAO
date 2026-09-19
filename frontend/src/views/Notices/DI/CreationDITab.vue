<template>
  <v-container class="doc-page">
    <h4>Créer une DI</h4>

    <div v-if="role === 'Opérateur prod'" class="text-body-2 mb-4">
      Si vous souhaitez signaler une nouvelle défaillance sur un équipement, vous pouvez le faire
      directement depuis le tableau de bord. En effet, vous disposez d'un bouton
      <strong>"Créer une DI"</strong>
      qui permet le signalement de la défaillance.
    </div>
    <div v-else class="text-body-2 mb-4">
      Si vous souhaitez signaler une nouvelle défaillance, vous pouvez le faire depuis la page des
      demandes d'interventions. Pour cela, rendez-vous sur la page des demandes d'interventions et
      cliquez sur le bouton "+" en bas à droite.
    </div>

    <ZoomImage v-if="listeCreerDiImg" :src="listeCreerDiImg" alt="Bouton créer DI" />

    <div class="text-body-2 mb-4">
      En cliquant dessus, vous serez redirigé vers un formulaire à remplir afin que vous puissiez
      fournir toutes les informations en votre possession au Responsable de la maintenance.
    </div>

    <ZoomImage v-if="creerDiImg" :src="creerDiImg" alt="Formulaire DI" />

    <div class="text-body-2 mb-4">
      Les différents champs du formulaire ont la signification suivante :<br />
      <strong>Nom</strong> : description synthétique de la panne ou du problème constaté.<br />
      <strong>Équipement</strong> : équipement concerné par la défaillance.<br />
      <strong>Statut supposé</strong> : nouvel état proposé pour l'équipement à la suite du
      signalement.<br />
      <strong>Commentaires</strong> : espace permettant d'apporter des précisions sur l'incident,
      par exemple les circonstances ou les éléments observés.<br />
      <strong>Documents</strong> : possibilité d'ajouter des fichiers (par exemple des photos).
      Veillez à sélectionner le type de document approprié et à lui attribuer un nom explicite.
    </div>

    <div class="text-body-2 mb-4">
      Pour lui donner ces informations, il vous suffit de remplir les champs demandés, puis de
      cliquer sur <strong>"Valider"</strong>.
    </div>
  </v-container>
</template>

<script setup>
  import ZoomImage from '../common/ZoomImage.vue'

  const props = defineProps({
    role: {
      type: String,
      default: 'Opérateur prod',
    },
  })

  const getDIImg = (name) => {
    try {
      return require(`@/assets/images/notices/DI/${name}`)
    } catch {
      return null
    }
  }

  const listeCreerDiImg =
    props.role === 'Opérateur prod'
      ? getDIImg('liste-creer-di.png')
      : props.role === 'Responsable GMAO'
        ? getDIImg('liste-creer-di-responsable.png') || getDIImg('liste-creer-di-technicien.png')
        : getDIImg('liste-creer-di-technicien.png')

  const creerDiImg =
    props.role === 'Opérateur prod'
      ? getDIImg('creer-di.png')
      : props.role === 'Responsable GMAO'
        ? getDIImg('creer-di-responsable.png') || getDIImg('creer-di-technicien.png')
        : getDIImg('creer-di-technicien.png')
</script>

<style scoped>
  .doc-page {
    max-width: 900px;
    line-height: 1.6;
  }
  p {
    margin-bottom: 20px;
  }
</style>
