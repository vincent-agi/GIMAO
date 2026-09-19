<template>
  <div>
    <div class="text-body-1 font-weight-bold mb-2">Liste des équipements</div>

    <div class="text-body-2 mb-4">
      La liste des équipements est consultable dans le menu correspondant ainsi que dans votre
      tableau de bord. Elle vous permet de consulter l'ensemble des équipements de votre entreprise.
      Elle donne accès aux informations détaillées de chaque équipement et peut également servir à
      signaler une défaillance directement depuis celui-ci. Si vous devez modifier l'état d'un
      équipement, cette action s'effectue via la création d'une Demande d'Intervention (DI). Lors du
      signalement, vous pourrez sélectionner le nouvel état correspondant à la situation.
    </div>

    <ZoomImage v-if="listeEqImg" :src="listeEqImg" alt="Liste des équipements" />

    <div v-if="props.role === 'Responsable GMAO'" class="mt-4">
      <div class="text-body-1 font-weight-bold mb-2">Importer des équipements depuis Excel</div>
      <div class="text-body-2 mb-4">
        Pour charger plusieurs équipements en une seule fois (par exemple lors d'un déploiement chez
        un nouveau client), utilisez les boutons <strong>Modèle Excel</strong> et
        <strong>Importer depuis Excel</strong> en haut de la liste des équipements.
        <ul class="ml-4 mt-2 mb-4">
          <li>
            Téléchargez d'abord le modèle : il contient un onglet par type de donnée (lieux,
            fabricants, fournisseurs, familles, modèles, équipements) avec une ligne d'exemple.
          </li>
          <li>Remplissez le fichier avec vos données, puis importez-le depuis le même écran.</li>
          <li>
            Les lieux, fabricants, fournisseurs et familles indiqués sont créés automatiquement
            s'ils n'existent pas encore.
          </li>
        </ul>
      </div>
      <ZoomImage v-if="importExcelImg" :src="importExcelImg" alt="Fenêtre d'import Excel" />

      <div class="text-body-2 mt-4 mb-4">
        Un compte-rendu s'affiche après l'import, détaillant pour chaque onglet le nombre de lignes
        créées, déjà existantes, et les éventuelles erreurs avec leur numéro de ligne. Réimporter le
        même fichier ne crée pas de doublons : les équipements déjà présents (identifiés par leur
        Code GMAO) sont simplement ignorés.
      </div>
      <ZoomImage
        v-if="importResultatImg"
        :src="importResultatImg"
        alt="Résultat de l'import Excel"
      />
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

  const getEquipImg = (name) => {
    try {
      return require(`@/assets/images/notices/equips/${name}`)
    } catch {
      return null
    }
  }

  const listeEqImg =
    props.role === 'Opérateur prod'
      ? getEquipImg('list-eq-operateur.png')
      : props.role === 'Responsable GMAO'
        ? getEquipImg('list-eq-responsable.png') || getEquipImg('list-eq-technicien.png')
        : getEquipImg('list-eq-technicien.png')

  const importExcelImg = getEquipImg('import-excel-equipements.png')
  const importResultatImg = getEquipImg('import-excel-resultat.png')
</script>
