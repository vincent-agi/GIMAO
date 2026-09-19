<template>
  <div class="notices-layout">
    <!-- Sidebar notice -->
    <v-navigation-drawer
      v-model="drawerOpen"
      :permanent="!isMobile"
      :temporary="isMobile"
      :width="drawerWidth"
      class="notices-sidebar"
      @mouseenter="isHovered = true"
      @mouseleave="isHovered = false"
    >
      <!-- Logo -->
      <v-list-item class="text-center py-4 logo-item" @click="goBack">
        <v-img :src="logo" contain max-width="80" class="mx-auto mb-2" />
        <v-list-item-title v-if="displayTitles" class="font-weight-bold text-h6">
          GIMAO
        </v-list-item-title>
        <v-list-item-subtitle v-if="displayTitles" class="text-caption text-medium-emphasis">
          Notices d'utilisation
        </v-list-item-subtitle>
      </v-list-item>

      <v-divider class="mb-2" />

      <!-- Navigation -->
      <v-list dense nav>
        <v-list-item
          v-for="item in noticeItems"
          :key="item.value"
          :class="['my-1', { 'active-item': tab === item.value }]"
          @click="selectTab(item.value)"
        >
          <template #prepend>
            <v-icon class="ml-3">{{ item.icon }}</v-icon>
          </template>
          <v-list-item-title :class="[{ hoverable: isMini }, { normal: !isMini }]">{{
            item.label
          }}</v-list-item-title>
        </v-list-item>
      </v-list>

      <!-- Toggle + Retour -->
      <template #append>
        <div v-if="!isMobile" class="menu-toggle-wrapper">
          <v-btn variant="tonal" color="primary" class="menu-toggle-btn" @click="toggleMini">
            <v-icon>{{ isMini ? 'mdi-menu-open' : 'mdi-menu' }}</v-icon>
            <span v-if="!isMini" class="ml-2">Réduire le menu</span>
            <span v-else-if="isHovered" class="ml-2">Agrandir le menu</span>
          </v-btn>
        </div>
        <v-divider />
        <v-list dense>
          <v-list-item class="py-2 logout-item" @click="goBack">
            <template #prepend>
              <v-icon class="ml-3">mdi-arrow-left</v-icon>
            </template>
            <v-list-item-title v-if="displayTitles">Retour</v-list-item-title>
          </v-list-item>
        </v-list>
      </template>
    </v-navigation-drawer>

    <!-- Contenu -->
    <div class="notices-content">
      <div class="notices-topbar">
        <!-- Hamburger sur mobile -->
        <v-btn v-if="isMobile" icon class="mr-2" @click="drawerOpen = !drawerOpen">
          <v-icon>mdi-menu</v-icon>
        </v-btn>
        <span>{{ currentNotice.label }}</span>
        <v-spacer></v-spacer>
        <v-btn icon :title="themeToggleLabel" @click="handleThemeToggle">
          <v-icon>{{ themeToggleIcon }}</v-icon>
        </v-btn>
      </div>
      <v-container fluid>
        <v-window v-model="tab">
          <v-window-item value="global"><NoticeGlobale /></v-window-item>
          <v-window-item value="operateur"><NoticeOperateur /></v-window-item>
          <v-window-item value="technicien"><NoticeTechnicien /></v-window-item>
          <v-window-item value="magasinier"><NoticeMagasinier /></v-window-item>
          <v-window-item value="responsable"><NoticeResponsable /></v-window-item>
        </v-window>
      </v-container>
    </div>
  </div>
</template>

<script setup>
  import { ref, computed, onMounted, onUnmounted } from 'vue'
  import { useRouter } from 'vue-router'

  import NoticeGlobale from '@/views/Notices/NoticeGlobale.vue'
  import NoticeOperateur from '@/views/Notices/NoticeOperateur.vue'
  import NoticeTechnicien from '@/views/Notices/NoticeTechnicien.vue'
  import NoticeMagasinier from '@/views/Notices/NoticeMagasinier.vue'
  import NoticeResponsable from '@/views/Notices/NoticeResponsable.vue'

  import vuetify from '@/plugins/vuetify'
  import { toggleTheme } from '@/utils/theme'

  import logo from '@/assets/images/LogoGIMAO.png'

  const noticeItems = [
    { value: 'global', label: 'Générale', icon: 'mdi-book-open-variant' },
    { value: 'operateur', label: 'Opérateur', icon: 'mdi-account-hard-hat' },
    { value: 'technicien', label: 'Technicien', icon: 'mdi-wrench' },
    { value: 'magasinier', label: 'Magasinier', icon: 'mdi-package-variant-closed' },
    { value: 'responsable', label: 'Responsable', icon: 'mdi-shield-account' },
  ]

  const tab = ref('global')
  const isMini = ref(false)
  const isHovered = ref(false)
  const isMobile = ref(window.innerWidth < 960)
  const drawerOpen = ref(!isMobile.value)

  const checkMobile = () => {
    isMobile.value = window.innerWidth < 960
    if (!isMobile.value) drawerOpen.value = true
    else drawerOpen.value = false
  }

  onMounted(() => window.addEventListener('resize', checkMobile))
  onUnmounted(() => window.removeEventListener('resize', checkMobile))

  const displayTitles = computed(() => !isMini.value || isHovered.value || isMobile.value)
  const drawerWidth = computed(() => (isMobile.value || displayTitles.value ? 280 : 80))

  const currentNotice = computed(
    () => noticeItems.find((n) => n.value === tab.value) || noticeItems[0]
  )

  const toggleMini = () => {
    isMini.value = !isMini.value
  }

  const selectTab = (value) => {
    tab.value = value
    if (isMobile.value) drawerOpen.value = false
  }

  const isDarkTheme = computed(() => vuetify.theme.global.current.value.dark)
  const themeToggleIcon = computed(() =>
    isDarkTheme.value ? 'mdi-weather-sunny' : 'mdi-weather-night'
  )
  const themeToggleLabel = computed(() =>
    isDarkTheme.value ? 'Activer le mode clair' : 'Activer le mode sombre'
  )

  const handleThemeToggle = () => {
    toggleTheme()
  }

  const router = useRouter()
  const goBack = () => {
    if (window.history.length > 1) {
      router.back()
      return
    }
    router.push('/')
  }
</script>

<style scoped>
  .notices-layout {
    display: flex;
    min-height: 100vh;
  }

  .notices-sidebar {
    transition: width 0.25s ease;
  }

  .logo-item {
    cursor: pointer;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
  }

  .notices-content {
    flex: 1;
    min-width: 0;
    overflow-x: hidden;
    display: flex;
    flex-direction: column;
  }

  .notices-topbar {
    background: rgb(var(--v-theme-surface));
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
    height: 64px;
    display: flex;
    align-items: center;
    padding: 0 20px;
    font-size: 1.1rem;
    font-weight: 600;
    color: rgb(var(--v-theme-primary));
    flex-shrink: 0;
    position: sticky;
    top: 0;
    z-index: 10;
  }

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

  .menu-toggle-wrapper {
    display: flex;
    justify-content: center;
    padding: 8px;
  }
  .menu-toggle-btn {
    width: 100%;
    max-width: 240px;
    font-weight: 600;
  }
</style>
