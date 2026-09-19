<template>
  <v-container class="doc-page">
    <!-- UTILISATEURS -->
    <h4 class="mb-2">Gestion des utilisateurs</h4>
    <div class="text-body-2 mt-2 mb-4">
      En tant que Responsable GMAO, vous pouvez créer, consulter et modifier les comptes des
      utilisateurs de l'application. Accédez à la liste via le menu <strong>Utilisateurs</strong>.
      <br /><br />

      <strong>Liste des utilisateurs :</strong>
      <ul class="ml-4 mt-2 mb-4">
        <li>
          Le tableau affiche tous les comptes : nom d'utilisateur, prénom, nom, rôle et statut.
        </li>
        <li>Utilisez la barre de recherche pour filtrer par nom ou par rôle.</li>
      </ul>

      <ZoomImage
        v-if="listUtilisateursImg"
        :src="listUtilisateursImg"
        alt="Liste des utilisateurs"
      />

      <strong>Créer un utilisateur :</strong>
      <ul class="ml-4 mt-2 mb-4">
        <li>Cliquez sur <strong>Ajouter</strong> en haut à droite de la liste.</li>

        <ZoomImage
          v-if="boutonAjouterImg"
          :src="boutonAjouterImg"
          alt="Bouton Ajouter un utilisateur"
        />

        <li>
          Renseignez le nom d'utilisateur, le prénom, le nom, l'adresse e-mail et le mot de passe
          temporaire.
        </li>
        <li>
          Sélectionnez le rôle approprié : Opérateur prod, Technicien prod, Technicien maintenance,
          Magasinier ou Responsable GMAO.
        </li>
        <li>Validez : l'utilisateur peut désormais se connecter avec ses identifiants.</li>
      </ul>

      <ZoomImage v-if="creerUtilisateurImg" :src="creerUtilisateurImg" alt="Créer un utilisateur" />

      <strong>Modifier un utilisateur :</strong>
      <ul class="ml-4 mt-2 mb-4">
        <li>Cliquez sur l'icône de modification sur la ligne d'un utilisateur.</li>

        <ZoomImage
          v-if="boutonModifierImg"
          :src="boutonModifierImg"
          alt="Bouton Modifier un utilisateur"
        />

        <li>
          Vous pouvez modifier son rôle, ses informations personnelles ou réinitialiser son mot de
          passe.
        </li>
        <li>
          Lors de la première connexion, l'utilisateur choisit lui-même son mot de passe. Par la
          suite, seul le responsable GMAO peut le réinitialiser depuis cette interface.
        </li>
      </ul>

      <ZoomImage
        v-if="modifierUtilisateurImg"
        :src="modifierUtilisateurImg"
        alt="Modifier un utilisateur"
      />
    </div>

    <!-- RÔLES -->
    <h4 class="mb-2 mt-4">Gestion des rôles</h4>
    <div class="text-body-2 mt-2 mb-4">
      Les rôles définissent les droits d'accès de chaque utilisateur dans GIMAO. Accédez à la
      gestion des rôles via le menu <strong>Rôles</strong>. <br /><br />

      <ZoomImage v-if="rubriqueRoleImg" :src="rubriqueRoleImg" alt="Rubrique Rôles dans le menu" />

      <strong>Les cinq rôles disponibles :</strong>
      <ul class="ml-4 mt-2 mb-4">
        <li>
          <strong>Opérateur prod</strong> : peut créer et suivre ses propres Demandes
          d'Intervention.
        </li>
        <li>
          <strong>Technicien prod</strong> : reçoit et réalise les Bons de Travail, consulte les
          équipements et les stocks.
        </li>
        <li>
          <strong>Technicien maintenance</strong> : dispose des mêmes droits que le Technicien prod,
          ainsi que l'accès au calendrier des maintenances et à la création des plans de maintenance
          préventive.
        </li>
        <li>
          <strong>Magasinier</strong> : gère les stocks, les magasins et valide les demandes de
          consommables.
        </li>
        <li>
          <strong>Responsable GMAO</strong> : accès complet à toutes les fonctionnalités de
          l'application.
        </li>
      </ul>

      <ZoomImage v-if="listeRolesImg" :src="listeRolesImg" alt="Liste des rôles" />

      <strong>Permissions par rôle :</strong>
      <br />
      Chaque rôle regroupe un ensemble de permissions précises (consulter, créer, modifier,
      supprimer) sur chaque module. En cliquant sur un rôle, vous visualisez le détail de ses
      permissions.
      <br /><br />
      Les cinq rôles (Responsable GMAO, Technicien prod, Technicien maintenance, Magasinier,
      Opérateur prod) sont des rôles par défaut : ils ne peuvent pas être supprimés, mais vous
      pouvez modifier leurs permissions ou les dupliquer pour créer de nouveaux rôles personnalisés
      avec plus ou moins de droits.
    </div>
  </v-container>
</template>

<script setup>
  import ZoomImage from '../common/ZoomImage.vue'

  const getImg = (name) => {
    try {
      return require(`@/assets/images/notices/admin/${name}`)
    } catch {
      return null
    }
  }

  const listUtilisateursImg = getImg('liste-utilisateurs.png')
  const boutonAjouterImg = getImg('bouton-ajouter-utilisateur.png')
  const creerUtilisateurImg = getImg('creer-utilisateur.png')
  const boutonModifierImg = getImg('bouton-modfier-utilisateur.png')
  const modifierUtilisateurImg = getImg('modifier-utilisateur.png')
  const rubriqueRoleImg = getImg('rubrique-role.png')
  const listeRolesImg = getImg('liste-roles.png')
</script>

<style scoped>
  .doc-page {
    padding: 0;
  }
  ul li {
    margin-bottom: 8px;
  }
</style>
