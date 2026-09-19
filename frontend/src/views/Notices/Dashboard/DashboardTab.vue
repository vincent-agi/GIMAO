<template>
  <div class="doc-page">
    <div class="text-body-1 font-weight-bold mb-2">Tableau de bord</div>

    <div class="text-body-2 mb-4">
      Après la connexion, votre tableau de bord s'affiche automatiquement. Il centralise les
      informations essentielles liées à votre activité.
      <br /><br />

      <template v-if="role === 'Opérateur prod'">
        En haut de l'écran, vous trouverez plusieurs indicateurs :
        <br /><br />

        - <strong>Vos DI</strong> : nombre total de Demandes d'Intervention que vous avez créées.<br />
        - <strong>Vos DI en attente</strong> : demandes qui n'ont pas encore été traitées par le
        Responsable GMAO.<br />
        - <strong>Vos DI acceptées</strong> : demandes validées et en attente d'un diagnostic ou
        d'une prise en charge.<br /><br />

        Le tableau de bord donne également accès aux principales fonctionnalités directement sous
        forme de sections :
        <br /><br />

        - Un panneau dédié à vos Demandes d'Intervention, détaillé dans l'onglet
        <em>Demande d'Intervention &gt; Consulter vos DI</em>.<br />

        - Une liste des équipements de l'entreprise, décrite dans l'onglet
        <em>Équipements &gt; Liste des équipements</em>.<br /><br />
      </template>

      <template v-else>
        En haut de l'écran, vous trouverez vos statistiques :
        <br /><br />

        - <strong>Vos BT</strong> : bons de travail qui vous sont assignés.<br />
        - <strong>Vos BT en cours</strong> : bons de travail que vous avez démarrés.<br />
        - <strong>Vos BT terminés</strong> : interventions achevées.<br /><br />

        Le tableau de bord donne également accès à vos outils de travail via un menu latéral :
        <br /><br />

        - <strong>Tableau de bord</strong> : retour à l'accueil.<br />
        - <strong>Équipements</strong> : accès à tous les équipements.<br />
        - <strong>Demandes d'interventions (DI)</strong> : accès à toutes les demandes
        d'interventions.<br />
        - <strong>Bons de travail (BT)</strong> : accès à tous les bons de travail.<br />
        - <strong>Stocks</strong> : accès à la gestion/consultation des pièces.<br /><br />

        Sur la page principale se trouve la liste de <strong>Vos BT</strong> qui vous sont assignés,
        ainsi que la liste des équipements.<br /><br />
      </template>

      Le contenu affiché dépend des droits attribués à votre compte.
    </div>

    <ZoomImage
      v-if="role === 'Opérateur prod'"
      :src="require('@/assets/images/notices/Dashboard/operateur.png')"
      alt="Tableau de bord"
    />
    <ZoomImage
      v-if="role === 'Technicien prod'"
      :src="require('@/assets/images/notices/Dashboard/technicien-prod.png')"
      alt="Tableau de bord"
    />
    <ZoomImage
      v-if="role === 'Technicien maintenance'"
      :src="require('@/assets/images/notices/Dashboard/technicien-maintenance.png')"
      alt="Tableau de bord"
    />
    <ZoomImage
      v-if="role === 'Responsable GMAO'"
      :src="require('@/assets/images/notices/Dashboard/responsable.png')"
      alt="Tableau de bord"
    />
  </div>
</template>

<script setup>
  import ZoomImage from '../common/ZoomImage.vue'

  defineProps({
    role: {
      type: String,
      default: 'Opérateur prod',
    },
  })
</script>

<style scoped>
  .doc-page {
    max-width: 80%;
    margin: auto;
    margin-bottom: 2rem;
  }
</style>
