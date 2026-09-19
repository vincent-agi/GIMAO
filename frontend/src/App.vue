<template>
  <v-app>
    <!-- Navigation (si page privée ET utilisateur a menu) -->
    <template v-if="!isPublicPage && userHasMenu && !isNoticePage">
      <!-- Sidebar desktop -->
      <Sidebar v-if="!isMobile && userHasMenu" />

      <!-- TopBar mobile (hamburger) -->
      <TopBar v-if="isMobile && userHasMenu" />

      <!-- AppBar desktop -->
      <v-app-bar v-if="!isMobile" app :color="isDarkTheme ? 'surface' : 'white'" elevation="1">
        <v-toolbar-title class="font-weight-bold ml-4">
          {{ pageTitle }}
        </v-toolbar-title>

        <v-spacer />

        <v-btn
          icon
          variant="text"
          class="mr-4"
          :title="themeToggleLabel"
          @click="handleThemeToggle"
        >
          <v-icon>{{ themeToggleIcon }}</v-icon>
        </v-btn>
      </v-app-bar>
    </template>

    <v-main>
      <Breadcrumb v-if="!isPublicPage" />
      <router-view />
    </v-main>

    <v-btn
      v-if="isNoticePage"
      :style="{ position: 'fixed', top: '72px', right: '16px', zIndex: 2500 }"
      color="secondary"
      icon="mdi-arrow-left"
      elevation="6"
      aria-label="Retour"
      @click="router.back()"
    />
    <v-btn
      v-else
      :style="{ position: 'fixed', top: '72px', right: '16px', zIndex: 2500 }"
      color="primary"
      icon="mdi-help"
      elevation="6"
      aria-label="Ouvrir les notices d'utilisation"
      @click="goToNotices"
    />
  </v-app>
</template>

<script setup>
  import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
  import { useStore } from 'vuex'
  import { useRoute, useRouter } from 'vue-router'

  import Sidebar from '@/components/SideBar.vue'
  import TopBar from '@/components/TopBar.vue'
  import Breadcrumb from '@/components/Breadcrumb.vue'
  import vuetify from '@/plugins/vuetify'
  import { toggleTheme } from '@/utils/theme'

  const store = useStore()
  const route = useRoute()
  const router = useRouter()

  /**
   * Mobile
   */
  const isMobile = ref(false)

  const checkIfMobile = () => {
    isMobile.value = window.innerWidth < 960 // breakpoint md Vuetify
  }

  const userHasMenu = computed(() => {
    return (
      store.getters.hasPermission('menu:view') || store.getters.hasPermission('menu:dataManagement')
    )
  })

  /**
   * Pages publiques
   */
  const isPublicPage = computed(() => route.meta?.public === true)

  /**
   * Titre page
   */
  const pageTitle = computed(() => route.meta?.title || 'GIMAO')
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

  const isNoticePage = computed(() => route.name === 'Notice')

  const goToNotices = () => {
    router.push('/Notice')
  }

  /**
   * Lifecycle
   */
  onMounted(() => {
    store.dispatch('initAuth')

    checkIfMobile()
    window.addEventListener('resize', checkIfMobile)
  })

  onBeforeUnmount(() => {
    window.removeEventListener('resize', checkIfMobile)
  })
</script>
