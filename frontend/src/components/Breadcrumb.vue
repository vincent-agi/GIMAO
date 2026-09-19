<template>
  <v-breadcrumbs class="breadcrumb" divider="›">
    <v-breadcrumbs-item
      v-for="(crumb, index) in breadcrumbs"
      :key="index"
      @click="crumb.route && $router.push(crumb.route)"
    >
      {{ makeBreadcrumbLabel(crumb, index) }}
    </v-breadcrumbs-item>
  </v-breadcrumbs>
</template>

<script setup>
  import { BREADCRUMBS, HEADERS } from '@/utils/breadcrumbs'
  import { ref, watch } from 'vue'
  import { useRoute, useRouter } from 'vue-router'

  const route = useRoute()
  const router = useRouter()

  const breadcrumbs = ref([])
  const isInitialized = ref(false)

  watch(
    route,
    () => {
      if (!route.name) return

      if (!isInitialized.value) {
        if (localStorage.getItem('breadcrumb')) {
          const inBreadcrumbs = JSON.parse(localStorage.getItem('breadcrumb'))
          const matchIndex = inBreadcrumbs.findIndex((crumb) => crumb.route === route.path)

          if (matchIndex !== -1) {
            breadcrumbs.value = inBreadcrumbs.slice(0, matchIndex)
          } else {
            if (route.name !== 'Dashboard' && !HEADERS.includes(route.name)) {
              router.push({ name: 'Dashboard' })
              return
            }
          }
        }
        isInitialized.value = true
      }

      if (breadcrumbs.value.find((crumb) => crumb.name === route.name)) {
        breadcrumbs.value = breadcrumbs.value.slice(
          0,
          breadcrumbs.value.findIndex((crumb) => crumb.name === route.name)
        )
      }
      if (HEADERS.includes(route.name)) {
        breadcrumbs.value.length = 0
      }

      const lastMatch = route.matched[route.matched.length - 1]
      const showId = lastMatch?.path.endsWith('/:id')

      breadcrumbs.value.push({
        name: route.name,
        route: route.path,
        id: showId ? (route.params.id ?? null) : null,
      })

      localStorage.setItem('breadcrumb', JSON.stringify(breadcrumbs.value))
    },
    { immediate: true }
  )

  function makeBreadcrumbLabel(crumb, index) {
    return `${BREADCRUMBS[crumb.name]} ${crumb.id ? `#${crumb.id}` : ''} ${index === breadcrumbs.value.length - 1 ? '' : '>'}`
  }
</script>

<style scoped>
  .breadcrumb {
    padding: 0 0 8px 0;
    font-size: 0.85rem;
    color: var(--text-color);
    opacity: 0.7;
    margin: 10px 0px 10px 15px;
  }

  .breadcrumb .v-breadcrumbs-item {
    cursor: pointer;
    transition: color 0.2s ease;
  }

  .breadcrumb .v-breadcrumbs-item:not(.v-breadcrumbs-item--disabled):hover {
    color: rgb(var(--v-theme-primary));
    text-decoration: underline;
  }

  .breadcrumb .v-breadcrumbs-item--disabled {
    color: var(--text-color);
    opacity: 1;
    font-weight: 600;
    cursor: default;
  }
</style>
