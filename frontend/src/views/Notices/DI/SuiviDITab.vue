<template>
  <v-container class="doc-page">
    <h4 v-if="role === 'Opérateur prod'">Consulter vos demandes d'intervention</h4>
    <h4 v-else>Consulter les demandes d'intervention</h4>

    <div class="text-body-2 mb-4 mt-2">
      <template v-if="role === 'Opérateur prod'">
        Dans la liste « Vos DI », vous retrouvez l'ensemble des Demandes d'Intervention que vous
        avez créées. Elle regroupe toutes les défaillances que vous avez signalées par le passé et
        vous permet de les consulter à tout moment. Cette liste vous aide également à suivre l'état
        d'avancement de vos demandes afin, si nécessaire, de les compléter ou de les modifier.
      </template>
      <template v-else>
        Dans la liste des DI, vous retrouvez l'ensemble des Demandes d'Intervention. Elle regroupe
        toutes les défaillances signalées. Vous pouvez y consulter les détails de chaque demande et
        suivre leur état d'avancement afin de procéder aux réparations ou diagnostics nécessaires.
      </template>

      <ZoomImage v-if="listeDiImg" :src="listeDiImg" />

      <br /><br />

      Les Demandes d'Intervention peuvent apparaître sous différents statuts.

      <br />

      - <strong>En attente</strong> : la DI n'a pas encore été traitée par votre Responsable GMAO.

      <br />

      - <strong>Acceptée</strong> : la DI a été validée par votre responsable et est en attente d'un
      diagnostic par un technicien.

      <br />

      - <strong>Transformée</strong> : un technicien est intervenu et a estimé qu'une réparation
      était nécessaire. La DI a alors été transformée en Bon de Travail afin de permettre la prise
      en charge de l'intervention.

      <br />

      - <strong>Refusée</strong> : la DI a été examinée par votre responsable, qui a estimé que la
      défaillance ne nécessitait pas d'intervention.
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

  const listeDiImg =
    props.role === 'Opérateur prod'
      ? getDIImg('liste-di.png')
      : props.role === 'Responsable GMAO'
        ? getDIImg('liste-di-responsable.png') || getDIImg('liste-di-technicien.png')
        : getDIImg('liste-di-technicien.png')
</script>
