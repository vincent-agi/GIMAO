<template>
  <v-navigation-drawer
    app
    permanent
    :width="drawerWidth"
    class="sidebar"
    @mouseenter="isHovered = true"
    @mouseleave="isHovered = false"
  >
    <!-- Logo -->
    <v-list-item class="text-center py-4 logo-item" @click="showAuthorsDialog = true">
      <v-img :src="logo" contain max-width="80" class="mx-auto mb-2" />

      <v-list-item-title v-if="displayTitles" class="font-weight-bold text-h6">
        {{ appTitle }}
      </v-list-item-title>
    </v-list-item>

    <v-divider class="mb-2" />

    <!-- Navigation -->
    <v-list dense nav>
      <v-list-item
        v-for="item in filteredNavigationItems"
        :key="item.name"
        :to="!item.disabled ? { name: item.name } : null"
        :class="[
          'my-1',
          { 'active-item': isActive(item.name) },
          { 'disabled-item': item.disabled },
        ]"
        @click="item.disabled ? $event.preventDefault() : null"
      >
        <template #prepend>
          <v-icon class="ml-3">{{ item.icon }}</v-icon>
        </template>

        <v-list-item-title :class="[{ hoverable: isMini }, { normal: !isMini }]">{{
          item.title
        }}</v-list-item-title>
      </v-list-item>
    </v-list>

    <!-- User / Logout -->
    <template #append>
      <div class="menu-toggle-wrapper">
        <v-btn variant="tonal" color="primary" class="menu-toggle-btn" @click="toggleMini">
          <v-icon>
            {{ isMini ? 'mdi-menu-open' : 'mdi-menu' }}
          </v-icon>

          <span v-if="!isMini" class="ml-2"> Réduire le menu </span>
          <span v-if="isHovered && isMini" class="ml-2">
            {{ isMini ? 'Agrandir le menu' : 'Réduire le menu' }}
          </span>
        </v-btn>
      </div>
      <v-divider />

      <v-list dense>
        <v-list-item class="py-2 user-info-item" @click="goToMyUserDetail">
          <template #prepend>
            <v-avatar size="36" :color="userPhotoUrl ? 'grey-lighten-3' : 'primary'">
              <v-img v-if="userPhotoUrl" :src="userPhotoUrl" cover />
              <span v-else class="text-white">{{ userInitials }}</span>
            </v-avatar>
          </template>

          <template v-if="displayTitles">
            <v-list-item-title>{{ user.name }}</v-list-item-title>
            <v-list-item-subtitle>{{ user.role }}</v-list-item-subtitle>
          </template>
        </v-list-item>

        <v-list-item class="logout-item" @click="showLogoutDialog">
          <template #prepend>
            <v-icon class="ml-3">mdi-logout</v-icon>
          </template>

          <v-list-item-title v-if="displayTitles"> Déconnexion </v-list-item-title>
        </v-list-item>
      </v-list>
    </template>
  </v-navigation-drawer>

  <ConfirmationModal
    v-model="showLogoutConfirm"
    type="warning"
    title="Déconnexion"
    message="Êtes-vous sûr de vouloir vous déconnecter ?"
    confirm-text="Se déconnecter"
    cancel-text="Annuler"
    confirm-icon="mdi-logout"
    @confirm="confirmLogout"
  />

  <!-- Dialog des auteurs / participants -->
  <v-dialog v-model="showAuthorsDialog" max-width="640" scrollable>
    <v-card class="authors-card">
      <!-- En-tête -->
      <div class="authors-header">
        <v-img :src="logo" contain max-width="64" class="mx-auto mb-3 authors-logo" />
        <div class="text-h5 font-weight-bold text-white">GIMAO</div>
        <div class="text-subtitle-2 text-white-70 mt-1">
          Gestion Informatisée de la Maintenance Assistée par Ordinateur
        </div>
      </div>

      <v-card-text class="pa-6">
        <div class="text-center mb-5">
          <div class="text-overline text-medium-emphasis">Réalisé par</div>
          <div class="authors-divider mx-auto my-2"></div>
        </div>

        <v-row dense>
          <v-col v-for="(author, index) in authors" :key="index" cols="12" sm="6">
            <div class="author-item">
              <v-avatar :color="authorColor(index)" size="40" class="author-avatar">
                <span class="text-white font-weight-bold">{{ authorInitials(author.nom) }}</span>
              </v-avatar>
              <div class="author-text">
                <div class="author-name">{{ author.nom }}</div>
                <div class="author-affiliation">{{ author.affiliation }}</div>
              </div>
            </div>
          </v-col>
        </v-row>

        <!-- Pied institution -->
        <div class="authors-footer text-center mt-6">
          <v-icon size="18" color="primary" class="mb-1">mdi-school</v-icon>
          <div class="text-body-2 font-weight-medium">
            Université de Pau et des Pays de l'Adour (UPPA)
          </div>
          <div class="text-caption text-medium-emphasis">
            IUT de Bayonne et du Pays Basque &amp; SIGLIS
          </div>
          <div class="text-caption text-medium-emphasis">2026</div>
        </div>

        <!-- Licence + code source (clause réseau AGPL) -->
        <div class="text-center mt-4">
          <v-chip
            :href="sourceCodeUrl"
            target="_blank"
            rel="noopener"
            color="primary"
            variant="tonal"
            size="small"
            prepend-icon="mdi-source-branch"
          >
            Code source
          </v-chip>
          <div class="text-caption text-medium-emphasis mt-2">
            Logiciel libre sous licence GNU AGPL v3
          </div>
        </div>
      </v-card-text>

      <v-divider />
      <v-card-actions class="justify-end pa-3">
        <v-btn variant="text" color="primary" @click="showAuthorsDialog = false">Fermer</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
  import { MEDIA_BASE_URL, BASE_URL } from '@/utils/constants'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'
  import api from '../composables/http'
  import ConfirmationModal from '@/components/common/ConfirmationModal.vue'

  export default {
    name: 'Sidebar',

    components: { ConfirmationModal },

    data() {
      return {
        appTitle: 'GIMAO',
        logo: require('@/assets/images/LogoGIMAO.png'),

        isMini: false, // choix utilisateur
        isHovered: false, // hover temporaire
        showLogoutConfirm: false,
        showAuthorsDialog: false,
        sourceCodeUrl: 'https://github.com/Aminata11052000/GIMAO',

        authors: [
          { nom: 'Iban ARANDIA', affiliation: 'IUT de Bayonne-UPPA' },
          { nom: 'Eneko ARBELBIDE', affiliation: 'IUT de Bayonne-UPPA' },
          { nom: 'Aminata BA', affiliation: 'SIGLIS-UPPA' },
          { nom: 'François BARLIC', affiliation: 'IUT de Bayonne-UPPA' },
          { nom: 'Gabriel BELTZER', affiliation: 'IUT de Bayonne-UPPA' },
          { nom: 'Andoni BERHO', affiliation: 'IUT de Bayonne-UPPA' },
          { nom: 'Maxime BOURCIEZ', affiliation: 'IUT de Bayonne-UPPA' },
          { nom: 'Rafael DUCASSE', affiliation: 'IUT de Bayonne-UPPA' },
          { nom: 'Rafael MASSON', affiliation: 'IUT de Bayonne-UPPA' },
          { nom: 'Alexandre PICOULET-SONDER', affiliation: 'IUT de Bayonne-UPPA' },
          { nom: 'Juan David RODRIGUEZ SINCLAIR', affiliation: 'IUT de Bayonne-UPPA' },
        ],

        api: useApi(API_BASE_URL),

        navigationItems: [
          {
            name: 'Dashboard',
            icon: 'mdi-view-dashboard',
            title: 'Tableau de bord',
            requiresPermission: null,
          },
          {
            name: 'EquipmentList',
            icon: 'mdi-tools',
            title: 'Équipements',
            requiresPermission: 'eq:viewList',
          },
          {
            name: 'FailureList',
            icon: 'mdi-alert',
            title: "Demandes d'interventions (DI)",
            requiresPermission: 'di:viewList',
          },
          {
            name: 'InterventionList',
            icon: 'mdi-wrench',
            title: 'Bons de travail (BT)',
            requiresPermission: 'bt:viewList',
          },
          {
            name: 'PreventiveMaintenance',
            icon: 'mdi-cog-clockwise',
            title: 'Maintenance préventive',
            requiresPermission: 'mp:viewList',
          },
          {
            name: 'Calendar',
            icon: 'mdi-calendar-month',
            title: 'Calendrier',
            requiresPermission: 'menu:calendar',
          },
          {
            name: 'UserList',
            icon: 'mdi-account-cog',
            title: 'Gestion des comptes',
            requiresPermission: 'user:viewList',
          },
          {
            name: 'Stocks',
            icon: 'mdi-package-variant-closed',
            title: 'Stocks',
            requiresPermission: 'stock:view',
          },
          {
            name: 'DataManagement',
            icon: 'mdi-database-cog',
            title: 'Gestion des données',
            requiresPermission: 'menu:dataManagement',
          },
        ],
      }
    },

    computed: {
      displayTitles() {
        return !this.isMini || this.isHovered
      },

      drawerWidth() {
        return this.displayTitles ? 280 : 80
      },

      currentUserRaw() {
        const currentUser = this.$store.getters.currentUser
        if (currentUser) return currentUser

        const userFromStorage = localStorage.getItem('user')
        if (!userFromStorage) return null
        try {
          return JSON.parse(userFromStorage)
        } catch (e) {
          console.error('Error parsing user from localStorage:', e)
          return null
        }
      },

      user() {
        const raw = this.currentUserRaw
        if (!raw) {
          return { name: 'Utilisateur', role: 'Non défini' }
        }

        const prenom = raw?.prenom ?? ''
        const nomFamille = raw?.nomFamille ?? ''
        const displayName = `${prenom} ${nomFamille}`.trim() || raw?.nomUtilisateur || 'Utilisateur'
        return {
          name: displayName,
          role: raw?.role?.nomRole || 'Utilisateur',
        }
      },

      userPhotoUrl() {
        const raw = this.currentUserRaw
        const path = raw?.photoProfil
        if (!path || typeof path !== 'string' || path.trim() === '') return ''
        return `${BASE_URL}${MEDIA_BASE_URL}${path}`
      },

      userInitials() {
        return this.user.name
          .split(' ')
          .map((w) => w[0])
          .join('')
          .slice(0, 2)
          .toUpperCase()
      },

      filteredNavigationItems() {
        return this.navigationItems.filter(
          (item) =>
            item.requiresPermission === null ||
            this.$store.getters.hasPermission(item.requiresPermission)
        )
      },
    },

    methods: {
      isActive(routeName) {
        return this.$route.name === routeName
      },

      authorInitials(name) {
        return name
          .split(' ')
          .filter(Boolean)
          .map((w) => w[0])
          .join('')
          .slice(0, 2)
          .toUpperCase()
      },

      authorColor(index) {
        const palette = [
          '#5d5fef',
          '#7c4dff',
          '#2196f3',
          '#00bcd4',
          '#009688',
          '#4caf50',
          '#ff9800',
          '#ff5722',
          '#e91e63',
          '#9c27b0',
          '#3f51b5',
        ]
        return palette[index % palette.length]
      },

      toggleMini() {
        this.isMini = !this.isMini
      },

      showLogoutDialog() {
        this.showLogoutConfirm = true
      },

      confirmLogout() {
        api
          .post('utilisateurs/logout/')
          .catch((err) => {
            console.error('Erreur lors du logout API :', err)
          })
          .finally(() => {
            this.$store.dispatch('logout')
            window.location.href = '/login'
          })
      },

      goToMyUserDetail() {
        const id = this.currentUserRaw?.id
        if (!id) return
        this.$router.push({ name: 'UserDetail', params: { id } })
      },
    },
  }
</script>

<style scoped>
  .sidebar {
    transition: width 0.25s ease;
  }

  .logo-item {
    cursor: pointer;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    transition: transform 0.2s ease;
  }

  .logo-item:hover {
    transform: scale(1.04);
  }

  /* =========================
   DIALOG AUTEURS
========================= */
  .authors-card {
    border-radius: 18px;
    overflow: hidden;
  }

  .authors-header {
    background: linear-gradient(135deg, #5d5fef 0%, #7c4dff 50%, #9c27b0 100%);
    padding: 32px 24px 28px;
    text-align: center;
    position: relative;
  }

  .authors-header::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    right: 0;
    height: 24px;
    background: inherit;
    clip-path: ellipse(70% 100% at 50% 0%);
    opacity: 0.35;
  }

  .authors-logo {
    filter: drop-shadow(0 4px 10px rgba(0, 0, 0, 0.25));
  }

  .text-white-70 {
    color: rgba(255, 255, 255, 0.8) !important;
  }

  .authors-divider {
    width: 60px;
    height: 3px;
    border-radius: 3px;
    background: linear-gradient(90deg, #5d5fef, #9c27b0);
  }

  .author-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 12px;
    border-radius: 12px;
    transition:
      background 0.2s ease,
      transform 0.2s ease;
  }

  .author-item:hover {
    background: rgba(93, 95, 239, 0.08);
    transform: translateX(4px);
  }

  .author-avatar {
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
    flex-shrink: 0;
  }

  .author-text {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .author-name {
    font-size: 0.95rem;
    font-weight: 500;
    color: var(--text-color);
    line-height: 1.2;
  }

  .author-affiliation {
    font-size: 0.72rem;
    color: rgb(var(--v-theme-primary));
    opacity: 0.8;
  }

  .authors-footer {
    padding-top: 16px;
    border-top: 1px dashed rgba(0, 0, 0, 0.12);
  }

  /* =========================
   ITEM ACTIF
========================= */
  .active-item {
    background-color: #5d5fef;
  }

  .active-item .v-list-item-title,
  .active-item .v-icon {
    color: white !important;
  }

  .active-item:hover {
    background-color: #5d5fef !important;
  }

  /* =========================
   ITEM NORMAL
========================= */
  .v-list-item-title {
    color: var(--text-color) !important;
  }

  /* Icônes des items normaux */
  .v-list-item:not(.active-item) .v-icon {
    color: var(--text-color) !important;
  }

  /* Sous-titre (rôle utilisateur) */
  .v-list-item-subtitle {
    color: var(--text-color) !important;
    opacity: 0.7;
  }

  /* Hover item NON actif */
  .v-list-item:not(.active-item):hover {
    background-color: var(--hover-color);
  }

  /* Forcer couleur texte au hover (mini ou normal) */
  .v-list-item:not(.active-item):hover .v-list-item-title,
  .v-list-item:not(.active-item):hover .v-icon {
    color: var(--text-color) !important;
  }

  /* =========================
   DISABLED
========================= */
  .disabled-item {
    pointer-events: none;
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* =========================
   LOGOUT
========================= */
  .logout-item:hover {
    background-color: var(--hover-color);
  }

  .user-info-item {
    cursor: pointer;
  }

  /* =========================
   TOGGLE DRAWER BUTTON
========================= */
  .menu-toggle-wrapper {
    display: flex;
    justify-content: center;
    padding: 8px;
  }

  .menu-toggle-btn {
    width: 100%;
    max-width: 240px;
    /* ne dépasse jamais */
    font-weight: 600;
  }

  /* En mode mini → bouton carré centré */
  .sidebar[style*='width: 80px'] .menu-toggle-btn {
    width: 48px;
    min-width: 48px;
    padding: 0;
  }
</style>
