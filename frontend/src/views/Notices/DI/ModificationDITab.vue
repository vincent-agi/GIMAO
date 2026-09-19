<template>
  <v-container class="doc-page">
    <h4>Modifier une demande d'intervention</h4>

    <div v-if="role === 'Opérateur prod'" class="text-body-2 mb-4">
      Une fois votre Demande d'Intervention créée, elle apparaît sur votre tableau de bord. Si vous
      souhaitez la modifier, il vous suffit de cliquer dessus afin d'accéder à sa page de détails.
      Depuis cette page, vous pouvez modifier les informations de votre demande à l'aide du bouton «
      Stylo », situé en bas à droite de l'écran.
    </div>
    <div v-else class="text-body-2 mb-4">
      Les Demandes d'Intervention sont consultables dans le menu correspondant. Si vous souhaitez en
      modifier une pour compléter les informations (statut, priorité, etc.), cliquez sur la ligne
      souhaitée pour accéder à sa page de détails. Depuis cette page, vous pouvez modifier les
      informations de la demande à l'aide du bouton « Stylo », situé en bas à droite de l'écran.
    </div>

    <ZoomImage v-if="detailDiEditImg" :src="detailDiEditImg" alt="Modification DI" />

    <div class="text-body-2 mb-4">
      Après avoir effectué vos modifications, cliquez sur « Enregistrer les modifications ». Vous
      serez alors redirigé vers la page de détails mise à jour de votre DI.
    </div>

    <ZoomImage v-if="modifDiImg" :src="modifDiImg" alt="Validation modification DI" />
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

  const detailDiEditImg =
    props.role === 'Opérateur prod'
      ? getDIImg('detail-di-edit.png')
      : props.role === 'Responsable GMAO'
        ? getDIImg('detail-di-responsable-edit.png') || getDIImg('detail-di-technicien-edit.png')
        : getDIImg('detail-di-technicien-edit.png')

  const modifDiImg =
    props.role === 'Opérateur prod'
      ? getDIImg('modif-di.png')
      : props.role === 'Responsable GMAO'
        ? getDIImg('modif-di-responsable.png') || getDIImg('modif-di-technicien.png')
        : getDIImg('modif-di-technicien.png')
</script>
