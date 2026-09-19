<template>
  <v-container fluid>
    <v-card class="mb-4">
      <v-card-title
        class="text-h4 text-primary py-4 rounded-t"
        :class="isDarkTheme ? 'bg-grey-darken-4' : 'bg-grey-lighten-4'"
      >
        <v-icon size="large" class="mr-2" color="primary">mdi-information</v-icon>
        Notice Générale
      </v-card-title>
      <v-card-text class="pt-4">
        <p class="text-body-1">
          Bienvenue dans <strong>GIMAO</strong> (Gestion Informatique de la Maintenance Assistée par
          Ordinateur). <br />Cette documentation globale présente les concepts transverses,
          l'interface utilisateur, ainsi que les bonnes pratiques de l'application.
        </p>

        <v-alert type="info" variant="tonal" class="mt-4 mb-4">
          GIMAO est structuré autour de 4 rôles distincts, avec des droits spécifiques. Pour
          consulter le mode d'emploi de votre rôle, accédez à la documentation depuis le menu de
          gauche.
        </v-alert>

        <v-divider class="my-4"></v-divider>

        <v-tabs
          v-model="tab"
          color="primary"
          :bg-color="isDarkTheme ? 'grey-darken-4' : 'grey-lighten-4'"
          show-arrows="always"
        >
          <v-tab value="roles"> <v-icon start>mdi-account-group</v-icon> Les Rôles </v-tab>
          <v-tab value="connexion"> <v-icon start>mdi-login</v-icon> Connexion </v-tab>
          <v-tab value="navigation"> <v-icon start>mdi-compass</v-icon> Navigation & Profil </v-tab>
          <v-tab value="bonnes_pratiques">
            <v-icon start>mdi-thumb-up</v-icon> Bonnes Pratiques
          </v-tab>
        </v-tabs>

        <v-window v-model="tab" class="mt-4">
          <!-- ONGLET : LES RÔLES -->
          <v-window-item value="roles">
            <v-expansion-panels multiple variant="accordion" class="doc-page">
              <v-expansion-panel>
                <v-expansion-panel-title> Comprendre les niveaux d'accès </v-expansion-panel-title>
                <v-expansion-panel-text class="pa-4">
                  <p class="mb-3">
                    Le fonctionnement de GIMAO repose sur des rôles spécifiques. Chaque rôle vous
                    donne accès aux menus et vues qui correspondent à vos tâches.
                  </p>

                  <v-list lines="two">
                    <v-list-item>
                      <v-list-item-title class="font-weight-bold">Opérateur</v-list-item-title>
                      <v-list-item-subtitle>
                        Le rôle d'entrée. L'utilisateur peut consulter ses propres Demandes
                        d'Intervention (DI) et en créer de nouvelles. Il est limité à un rôle de
                        signalement.
                      </v-list-item-subtitle>
                    </v-list-item>

                    <v-list-item>
                      <v-list-item-title class="font-weight-bold">Technicien</v-list-item-title>
                      <v-list-item-subtitle>
                        Le moteur de l'activité. Il a les droits de l'opérateur, mais surtout, il
                        reçoit les Bons de Travail (BT) qui lui sont assignés, réalise les tâches de
                        maintenance, et consigne ses heures et rapports d'intervention.
                      </v-list-item-subtitle>
                    </v-list-item>

                    <v-list-item>
                      <v-list-item-title class="font-weight-bold">Magasinier</v-list-item-title>
                      <v-list-item-subtitle>
                        Le magasinier est à part, il ne dispose que des droits sur les stocks et les
                        magasins. Il gère les inventaires, pièces, entrées/sorties et réservations
                        liées aux BT.
                      </v-list-item-subtitle>
                    </v-list-item>

                    <v-list-item>
                      <v-list-item-title class="font-weight-bold"
                        >Responsable GMAO (Administrateur global)</v-list-item-title
                      >
                      <v-list-item-subtitle>
                        Le superviseur. Il possède tous les droits de consultation et
                        d'administration, dont la configuration globale, la création des BT, la
                        gestion du stock et la validation des interventions.
                      </v-list-item-subtitle>
                    </v-list-item>
                  </v-list>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-window-item>

          <!-- ONGLET : CONNEXION -->
          <v-window-item value="connexion">
            <ConnexionTab :has-menu="true" />
          </v-window-item>

          <!-- ONGLET : NAVIGATION -->
          <v-window-item value="navigation">
            <v-expansion-panels multiple variant="accordion" class="doc-page">
              <v-expansion-panel>
                <v-expansion-panel-title> Tableau de bord et Menu </v-expansion-panel-title>
                <v-expansion-panel-text class="pa-4">
                  <p>
                    Le <strong>Tableau de Bord (Dashboard)</strong> centralise les accès essentiels
                    dès votre connexion :
                  </p>
                  <ul class="ml-4 mb-4">
                    <li>
                      Raccourcis vers vos tâches prioritaires (selon votre rôle : DI en attente, BT
                      assignés, Réservations à valider...).
                    </li>
                    <li>
                      Navigation simplifiée via un système de "tuiles" ou de liste de points clés.
                    </li>
                  </ul>
                  <p>
                    Le <strong>Menu latéral</strong>, présent sur la gauche, s'adapte à votre rôle.
                    Il contient la liste exhaustive des vues auxquelles vous avez accès (Demandes,
                    Bons de Travail, Stock, Equipement...).
                  </p>
                </v-expansion-panel-text>
              </v-expansion-panel>

              <v-expansion-panel>
                <v-expansion-panel-title>
                  Barre supérieure, Profil et Documentation
                </v-expansion-panel-title>
                <v-expansion-panel-text class="pa-4">
                  <p>En haut de l'écran, vous retrouvez constamment :</p>
                  <ul class="ml-4 mb-4">
                    <li>
                      <strong>Le fil d'Ariane</strong> : situé en haut à gauche, il indique la
                      hiérarchie de l'écran actuel (ex. : "GIMAO / Équipement / Détail").
                    </li>
                    <li>
                      <strong>Bouton Mode Sombre</strong> : icône de soleil/lune pour adapter le
                      thème d'affichage.
                    </li>
                    <li>
                      <strong>Bouton Documentation</strong> : l'icône de point d'interrogation
                      (<v-icon size="small">mdi-help-circle</v-icon>) ouvre directement la notice
                      correspondante.
                    </li>
                    <li>
                      <strong>Menu Profil / Avatar</strong> : situé en haut à droite, il permet
                      d'accéder à la gestion de vos informations.
                    </li>
                  </ul>

                  <h4 class="text-primary mt-4 mb-2">Accès au réglages du Compte</h4>
                  <p>
                    Depuis votre avatar > <v-icon size="small">mdi-account</v-icon>
                    <strong>Mon Profil</strong>, vous pouvez :
                  </p>
                  <ul class="ml-4">
                    <li>Consulter vos informations personnelles.</li>
                    <li>Changer votre mot de passe pour des questions de sécurité.</li>
                  </ul>
                </v-expansion-panel-text>
              </v-expansion-panel>

              <v-expansion-panel>
                <v-expansion-panel-title> Gestion des documents </v-expansion-panel-title>
                <v-expansion-panel-text class="pa-4">
                  <p class="mb-2">
                    GIMAO permet d'attacher des documents à plusieurs entités (Équipements, Demandes
                    d'Intervention, Bons de Travail...).
                  </p>
                  <ul class="ml-4">
                    <li>
                      <strong>Consultation</strong> : Vous pouvez visualiser et télécharger les
                      pièces jointes existantes (images, manuels, rapports PDF).
                    </li>
                    <li>
                      <strong>Ajout / Modification</strong> : Si votre rôle le permet, des menus
                      dédiés permettent le téléversement (upload) de nouveaux fichiers pour enrichir
                      la base de connaissances et l'historique de l'équipement.
                    </li>
                  </ul>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-window-item>

          <!-- ONGLET : BONNES PRATIQUES -->
          <v-window-item value="bonnes_pratiques">
            <v-expansion-panels multiple variant="accordion" class="doc-page">
              <v-expansion-panel>
                <v-expansion-panel-title class="text-success">
                  Directives et conseils d'utilisation
                </v-expansion-panel-title>
                <v-expansion-panel-text class="pa-4">
                  <ul class="ml-4">
                    <li class="mb-2">
                      <strong>Qualité de l'information :</strong> Rédigez des descriptions précises
                      (titres et corps) dans vos Demandes d'Intervention ou comptes-rendus. Cela
                      aide le Responsable à qualifier le travail et fait gagner un temps précieux
                      aux Techniciens.
                    </li>
                    <li class="mb-2">
                      <strong>Gestion des Sessions :</strong> Si vous utilisez GIMAO sur un poste
                      partagé (atelier, magasin), pensez toujours à
                      <strong>vous déconnecter</strong> à la fin de votre session pour éviter qu'une
                      action ne soit réalisée en votre nom.
                    </li>
                    <li class="mb-2">
                      <strong>Temps réel :</strong> Renseignez vos actions au plus près de leur
                      réalisation (saisie des temps, utilisation d'articles) pour conserver une
                      exactitude dans le stock et dans l'historique d'intervention.
                    </li>
                    <li class="mb-2">
                      <strong>Mots de passe sécurisés :</strong> Modifiez votre mot de passe
                      temporaire dès votre première connexion, et ne le communiquez pas.
                    </li>
                  </ul>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-window-item>
        </v-window>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
  import { ref, computed } from 'vue'
  import ConnexionTab from './Auth/ConnexionTab.vue'
  import vuetify from '@/plugins/vuetify'

  const tab = ref('roles')

  const isDarkTheme = computed(() => vuetify.theme.global.current.value.dark)
</script>

<style scoped>
  .v-list-item-title {
    font-size: 1.1rem !important;
  }
  .doc-page {
    max-width: 80%;
    margin: auto;
    margin-bottom: 2rem;
  }
</style>
