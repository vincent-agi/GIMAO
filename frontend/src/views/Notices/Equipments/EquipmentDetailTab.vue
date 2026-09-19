<template>
  <div>
    <div class="text-body-1 font-weight-bold mb-2">Détails d'un équipement</div>

    <div class="text-body-2 mb-4">
      Lorsque vous cliquez sur un équipement, vous accédez à sa page de détails. Cette page vous
      présente une vue d'ensemble des informations disponibles concernant l'équipement. Vous pouvez
      y consulter ses caractéristiques ainsi que les documents associés, si ceux-ci ont été
      renseignés par vos supérieurs. Ces documents peuvent notamment contenir des notices ou des
      manuels d'utilisation utiles.
    </div>

    <ZoomImage v-if="detailEqImg" :src="detailEqImg" alt="Détail équipement" />

    <div class="text-body-1 font-weight-bold mb-2">
      En bas de la colonne gauche, vous pourrez trouver les dits documents associés à l'équipement,
      s'ils ont été renseignés par vos supérieurs.
    </div>

    <ZoomImage v-if="detailEqDocsImg" :src="detailEqDocsImg" alt="Documents équipement" />

    <div class="text-body-2 mb-4">
      Depuis cette page, vous pouvez également signaler une défaillance en cliquant sur le bouton
      <strong>Créer une DI</strong>. Le formulaire de création de DI s'ouvre alors avec l'équipement
      déjà sélectionné, ce qui facilite le signalement.
    </div>

    <ZoomImage
      v-if="detailEqCreerDiImg"
      :src="detailEqCreerDiImg"
      alt="Signalement depuis détail équipement"
    />

    <div v-if="roleIsAbove('Technicien prod')" class="mt-4">
      <div class="text-body-1 font-weight-bold mb-2">Modification et compteurs</div>
      <div class="text-body-2 mb-4">
        - Vous avez accès aux <strong>compteurs</strong> de chaque équipement : consultez et
        modifiez les valeurs (heures, km, cycles…).
      </div>
    </div>
  </div>
</template>

<script setup>
  import ZoomImage from '../common/ZoomImage.vue'

  const props = defineProps({
    role: {
      type: String,
      default: 'Opérateur prod',
    },
  })

  const roles = ['Opérateur prod', 'Technicien prod', 'Technicien maintenance', 'Responsable GMAO']

  const roleIsAbove = (minRole) => {
    return roles.indexOf(props.role) >= roles.indexOf(minRole)
  }

  const getEquipImg = (name) => {
    try {
      return require(`@/assets/images/notices/equips/${name}`)
    } catch {
      return null
    }
  }

  const detailEqImg =
    props.role === 'Opérateur prod'
      ? getEquipImg('detail-eq-operateur.png')
      : props.role === 'Responsable GMAO'
        ? getEquipImg('detail-eq-responsable.png') || getEquipImg('detail-eq-technicien.png')
        : getEquipImg('detail-eq-technicien.png')

  const detailEqDocsImg =
    props.role === 'Opérateur prod'
      ? getEquipImg('detail-eq-docs-operateur.png')
      : props.role === 'Responsable GMAO'
        ? getEquipImg('detail-eq-docs-responsable.png') ||
          getEquipImg('detail-eq-docs-technicien.png')
        : getEquipImg('detail-eq-docs-technicien.png')

  const detailEqCreerDiImg =
    props.role === 'Opérateur prod'
      ? getEquipImg('detail-eq-creer-di-operateur.png')
      : props.role === 'Responsable GMAO'
        ? getEquipImg('detail-eq-creer-di-responsable.png') ||
          getEquipImg('detail-eq-creer-di-technicien.png')
        : getEquipImg('detail-eq-creer-di-technicien.png')
</script>
