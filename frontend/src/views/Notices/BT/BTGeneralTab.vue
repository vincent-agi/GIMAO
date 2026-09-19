<template>
  <v-expansion-panels multiple variant="accordion" class="doc-page">
    <!-- LISTE BT -->
    <v-expansion-panel v-if="roleIsAbove('Opérateur prod')">
      <v-expansion-panel-title> Consulter vos bons de travail </v-expansion-panel-title>

      <v-expansion-panel-text>
        <BTConsultTab :role="props.role" />
      </v-expansion-panel-text>
    </v-expansion-panel>

    <!-- ASSIGNER / MODIFIER BT -->
    <v-expansion-panel v-if="roleIsAbove('Technicien prod')">
      <v-expansion-panel-title> Réaliser et documenter une intervention </v-expansion-panel-title>

      <v-expansion-panel-text>
        <BTRealisationTab :role="props.role" />
      </v-expansion-panel-text>
    </v-expansion-panel>

    <!-- ASSIGNER UN TECHNICIEN (Responsable GMAO uniquement) -->
    <v-expansion-panel v-if="props.role === 'Responsable GMAO'">
      <v-expansion-panel-title>
        Assigner un technicien à un bon de travail
      </v-expansion-panel-title>

      <v-expansion-panel-text>
        <div class="text-body-2 mb-4">
          Depuis le détail d'un bon de travail, sélectionnez un ou plusieurs techniciens dans la
          section
          <strong>Techniciens assignés</strong>. Seuls les comptes ayant le rôle
          <strong>Technicien maintenance</strong>
          apparaissent dans cette liste : ce sont eux qui réalisent les interventions et documentent
          les bons de travail.
        </div>
        <ZoomImage
          v-if="assignerTechnicienImg"
          :src="assignerTechnicienImg"
          alt="Assigner un technicien"
        />
      </v-expansion-panel-text>
    </v-expansion-panel>

    <!-- CALENDRIER ET PLANS DE MAINTENANCE (Technicien maintenance et Responsable GMAO) -->
    <v-expansion-panel
      v-if="props.role === 'Technicien maintenance' || props.role === 'Responsable GMAO'"
    >
      <v-expansion-panel-title>
        Calendrier et plans de maintenance préventive
      </v-expansion-panel-title>

      <v-expansion-panel-text>
        <div class="text-body-2 mb-4">
          En plus du suivi habituel des bons de travail, vous avez accès au
          <strong>Calendrier</strong>, qui affiche l'ensemble des interventions planifiées ainsi que
          les prochaines échéances de maintenance préventive.
        </div>
        <ZoomImage v-if="calendrierImg" :src="calendrierImg" alt="Calendrier des maintenances" />

        <div class="text-body-2 mt-4 mb-4">
          Vous pouvez également créer et modifier des
          <strong>plans de maintenance préventive</strong> depuis la fiche d'un équipement, onglet
          <em>Plans de maintenance</em> : nom du plan, type, habilitations requises, consommables
          nécessaires, et compteurs de déclenchement (numérique ou calendaire) avec leur seuil.
        </div>
        <ZoomImage
          v-if="plansMaintenanceImg"
          :src="plansMaintenanceImg"
          alt="Plans de maintenance préventive"
        />
      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>
</template>

<script setup>
  import ZoomImage from '../common/ZoomImage.vue'
  import BTConsultTab from './BTConsultTab.vue'
  import BTRealisationTab from './BTRealisationTab.vue'

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

  const getBtImg = (name) => {
    try {
      return require(`@/assets/images/notices/BT/${name}`)
    } catch {
      return null
    }
  }

  const assignerTechnicienImg = getBtImg('assigner-technicien-bt.png')
  const calendrierImg = getBtImg('calendrier-technicien-maintenance.png')
  const plansMaintenanceImg = getBtImg('plans-maintenance-technicien-maintenance.png')
</script>

<style scoped>
  .doc-page {
    max-width: 90%;
    margin: auto;
    margin-bottom: 2rem;
  }
  ul li {
    margin-bottom: 8px;
  }
</style>
