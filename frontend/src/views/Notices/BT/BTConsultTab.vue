<template>
  <v-container class="doc-page">
    <h4>Consulter et suivre les bons de travail</h4>

    <div class="text-body-2 mb-4 mt-2">
      Vous avez deux façons de consulter vos bons de travail :
      <ul class="ml-4 mt-2 mb-4">
        <li>
          <strong>Vos BT assignés :</strong> directement depuis la page d'accueil de votre tableau
          de bord, vous avez une vue synthétique des interventions qui vous sont confiées.
        </li>

        <ZoomImage v-if="dashboardImg" :src="dashboardImg" alt="Tableau de bord" />

        <li>
          <strong>Tous les BT :</strong> via le menu "Bons de travail" correspondant, où vous
          accédez à l'ensemble des interventions.
        </li>
      </ul>

      <ZoomImage v-if="listeBtImg" :src="listeBtImg" alt="Liste des Bons de Travail" />

      <strong>Informations visibles dans le tableau des Bons de Travail :</strong>
      <ul class="ml-4 mt-2 mb-4">
        <li><strong>Nom :</strong> le nom de l'intervention.</li>
        <li><strong>Équipement :</strong> l'équipement associé à l'intervention.</li>
        <li><strong>Diagnostic :</strong> le diagnostic initial formulé.</li>
        <li>
          <strong>Dates :</strong> la date d'assignation et la date prévue pour l'intervention.
        </li>
        <li><strong>Statut :</strong> l'état actuel de l'intervention (voir liste ci-dessous).</li>
        <li>
          <strong>Responsable :</strong> le responsable en charge de la supervision du Bon de
          Travail.
        </li>
      </ul>

      <strong>Les différents statuts d'un Bon de Travail :</strong>
      <ul class="ml-4 mt-2 mb-4 list-unstyled">
        <li>
          - <strong>En attente</strong> : l'intervention est planifiée et assignée, mais le
          technicien n'a pas encore débuté le travail.
        </li>
        <li>
          - <strong>En cours</strong> : le technicien a signifié le démarrage de l'intervention
          (date de début enregistrée).
        </li>
        <li>
          - <strong>En retard</strong> : la date d'échéance prévue initialement a été dépassée sans
          que l'intervention ne soit terminée.
        </li>
        <li>
          - <strong>Terminé</strong> : le technicien a fini son intervention et rempli son
          compte-rendu.
        </li>
        <li>
          - <strong>Clôturé</strong> : le responsable a vérifié les travaux, mis à jour les stocks
          si nécessaire et fermé définitivement le BT.
        </li>
      </ul>

      <em>Note :</em> Un BT préventif est généré de manière automatique lorsqu'un compteur
      d'équipement (heures, kilomètres, cycles) atteint un seuil défini. Ces BT préventifs vous sont
      confiés de la même façon que les BT correctifs habituels.
    </div>
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

  const getBtImg = (name) => {
    try {
      return require(`@/assets/images/notices/BT/${name}`)
    } catch {
      return null
    }
  }
  const getDashImg = (name) => {
    try {
      return require(`@/assets/images/notices/Dashboard/${name}`)
    } catch {
      return null
    }
  }

  const isResponsable = props.role === 'Responsable GMAO'

  const dashboardImg = isResponsable
    ? getDashImg('responsable.png') || getDashImg('technicien.png')
    : getDashImg('technicien.png')

  const listeBtImg = isResponsable
    ? getBtImg('liste-bt-responsable.png') || getBtImg('liste-bt-technicien.png')
    : getBtImg('liste-bt-technicien.png')
</script>

<style scoped>
  .doc-page {
    padding: 0;
  }
  ul.list-unstyled li {
    list-style-type: none;
    margin-bottom: 8px;
  }
  ul li {
    margin-bottom: 8px;
  }
</style>
