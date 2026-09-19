<template>
  <v-container :fluid="fluid">
    <!-- Header avec titre et actions -->
    <v-row class="mb-4" align="center" justify="space-between">
      <!-- Titre -->
      <v-col cols="12" md="5">
        <h1 v-if="title" :class="titleClass">{{ title }}</h1>
        <p v-if="subtitle" :class="subtitleClass">{{ subtitle }}</p>
      </v-col>

      <!-- Filtres + Recherche ensemble -->
      <v-col cols="12" md="7">
        <div class="d-flex align-center justify-end flex-wrap ga-3" style="row-gap: 12px">
          <!-- Slot filtres (maintenant à côté de la recherche) -->
          <slot name="filters"></slot>

          <!-- Barre de recherche -->
          <v-text-field
            v-if="showSearch"
            v-model="searchQuery"
            :label="searchLabel"
            :placeholder="searchPlaceholder"
            prepend-inner-icon="mdi-magnify"
            clearable
            variant="outlined"
            density="compact"
            hide-details
            style="max-width: 350px; min-width: 180px; flex: 1 1 180px"
            @keydown.enter.prevent
          />
        </div>
      </v-col>

      <!-- Actions (si besoin) -->
      <v-col v-if="showCreateButton || $slots.actions" cols="12" md="auto">
        <div class="d-flex justify-end flex-wrap" style="gap: 8px; row-gap: 12px">
          <slot name="actions">
            <v-btn
              v-if="showCreateButton"
              :color="createButtonColor"
              :prepend-icon="createButtonIcon"
              @click="$emit('create')"
            >
              {{ createButtonText }}
            </v-btn>
          </slot>
        </div>
      </v-col>
    </v-row>

    <!-- Alerts -->
    <FormAlert
      v-if="errorMessage"
      :message="errorMessage"
      type="error"
      dismissible
      class="mb-4"
      @close="$emit('clear-error')"
    />

    <FormAlert
      v-if="loading && loadingMessage"
      :message="loadingMessage"
      type="info"
      class="mb-4"
    />

    <!-- Slot avant le tableau pour contenu personnalisé -->
    <slot name="before-table"></slot>

    <!-- Skeleton loader — premier chargement (aucune donnée encore reçue) -->
    <!-- Utilise des div flex plutôt que tr/td pour éviter les erreurs de DOM Vue -->
    <v-card v-if="isInitialLoading" :elevation="elevation" :class="cardClass">
      <!-- En-tête skeleton -->
      <div class="d-flex align-center px-4 py-3 skeleton-header">
        <div v-for="header in headers" :key="header.key" class="flex-1 px-2">
          <v-skeleton-loader type="text" width="60%" />
        </div>
      </div>
      <v-divider />
      <!-- Lignes skeleton -->
      <div
        v-for="i in skeletonRowCount"
        :key="i"
        class="d-flex align-center px-4 py-3"
        :class="i < skeletonRowCount ? 'border-b' : ''"
      >
        <div v-for="header in headers" :key="header.key" class="flex-1 px-2">
          <v-skeleton-loader type="text" />
        </div>
      </div>
    </v-card>

    <!-- Tableau de données — données disponibles ou rechargement -->
    <v-card v-else :elevation="elevation" :class="cardClass">
      <!-- Barre de progression fine lors d'un rechargement (données déjà visibles) -->
      <v-progress-linear v-if="loading" indeterminate color="primary" height="2" />

      <v-data-table
        :headers="headers"
        :items="computedItems"
        :items-per-page="itemsPerPage"
        :items-per-page-options="itemsPerPageOptions"
        :search="internalSearch ? searchQuery : undefined"
        :sort-by="sortBy"
        :class="tableClass"
        :hide-default-footer="hideDefaultFooter"
        @click:row="handleRowClick"
      >
        <!-- Pass through all item slots -->
        <template v-for="(_, slot) in $slots" #[slot]="scope">
          <slot :name="slot" v-bind="scope"></slot>
        </template>

        <!-- Default no-data template -->
        <template #no-data>
          <div class="text-center pa-4">
            <v-icon size="64" color="grey">{{ noDataIcon }}</v-icon>
            <p class="text-h6 mt-2">{{ noDataText }}</p>
          </div>
        </template>
      </v-data-table>
    </v-card>

    <!-- Slot après le tableau -->
    <slot name="after-table"></slot>
  </v-container>
</template>

<script setup>
  /**
   * BaseListView — mise en page standard pour les pages de liste.
   *
   * Fournit un en-tête avec titre, barre de recherche et bouton de création,
   * une zone d'alerte, un tableau de données Vuetify et les contrôles de pagination serveur.
   *
   * Comportement de chargement :
   *   - Premier chargement (loading=true, aucune donnée) : affiche un skeleton table qui
   *     reproduit la structure du tableau (colonnes × lignes) pour éviter le saut de mise en page.
   *   - Rechargement (loading=true, données déjà présentes) : affiche une barre de progression
   *     fine (2 px) en haut du tableau ; les données restent visibles.
   *
   * Slots :
   *   filters       — filtres additionnels affichés à côté de la barre de recherche.
   *   actions       — surcharge du bouton de création.
   *   before-table  — contenu inséré avant le tableau.
   *   after-table   — contenu inséré après le tableau.
   *   item.<clé>    — surcharge d'une cellule de la table (transmis à v-data-table).
   *
   * Évènements émis :
   *   create             — clic sur le bouton de création.
   *   row-click          — clic sur une ligne du tableau.
   *   search             — saisie dans la barre de recherche.
   *   clear-error        — fermeture de l'alerte d'erreur.
   *   update:searchValue — mise à jour de la valeur de recherche (v-model support).
   */
  import { computed, ref } from 'vue'
  import FormAlert from './FormAlert.vue'

  const props = defineProps({
    // Données
    items: {
      type: Array,
      default: () => [],
    },
    headers: {
      type: Array,
      required: true,
    },

    // Titre et sous-titre
    title: {
      type: String,
      default: '',
    },
    subtitle: {
      type: String,
      default: '',
    },
    titleClass: {
      type: String,
      default: 'text-h4 text-primary',
    },
    subtitleClass: {
      type: String,
      default: 'text-subtitle-1 text-grey',
    },

    // Bouton de création
    showCreateButton: {
      type: Boolean,
      default: true,
    },
    createButtonText: {
      type: String,
      default: 'Créer',
    },
    createButtonColor: {
      type: String,
      default: 'primary',
    },
    createButtonIcon: {
      type: String,
      default: 'mdi-plus',
    },

    // Recherche
    showSearch: {
      type: Boolean,
      default: true,
    },
    searchLabel: {
      type: String,
      default: 'Rechercher',
    },
    searchPlaceholder: {
      type: String,
      default: 'Tapez pour rechercher...',
    },
    searchValue: {
      type: String,
      default: undefined,
    },
    searchCols: {
      type: [Number, String],
      default: 12,
    },
    searchMd: {
      type: [Number, String],
      default: 6,
    },
    internalSearch: {
      type: Boolean,
      default: false,
    },

    // Messages
    loading: {
      type: Boolean,
      default: false,
    },
    loadingMessage: {
      type: String,
      default: 'Chargement des données...',
    },
    errorMessage: {
      type: String,
      default: '',
    },

    // Configuration du tableau
    itemsPerPage: {
      type: Number,
      default: 10,
    },
    itemsPerPageOptions: {
      type: Array,
      default: () => [5, 10, 25, 50, 100],
    },
    sortBy: {
      type: Array,
      default: () => [],
    },

    // Messages vides
    noDataText: {
      type: String,
      default: 'Aucune donnée disponible',
    },
    noDataIcon: {
      type: String,
      default: 'mdi-database-off',
    },

    // Styles
    fluid: {
      type: Boolean,
      default: false,
    },
    elevation: {
      type: [Number, String],
      default: 1,
    },
    cardClass: {
      type: String,
      default: 'rounded-lg',
    },
    tableClass: {
      type: String,
      default: '',
    },
    hideDefaultFooter: {
      type: Boolean,
      default: false,
    },
  })

  const emit = defineEmits(['create', 'row-click', 'search', 'clear-error', 'update:searchValue'])

  const localSearchQuery = ref('')

  const computedItems = computed(() => props.items || [])

  // Skeleton loaders — affiché uniquement au premier chargement (aucune donnée encore reçue).
  // Lors d'un rechargement, les données restent visibles avec une barre de progression fine.
  const isInitialLoading = computed(() => props.loading && computedItems.value.length === 0)
  const skeletonRowCount = computed(() => {
    const n = props.itemsPerPage
    // itemsPerPage peut valoir -1 (Vuetify = "tout afficher") — garantir un entier positif
    return n > 0 ? Math.min(n, 8) : 5
  })

  const normalizeSearchValue = (value) => {
    if (typeof value === 'string') {
      return value
    }

    if (value && typeof value === 'object' && typeof value.target?.value === 'string') {
      return value.target.value
    }

    return ''
  }

  const isSearchControlled = computed(() => props.searchValue !== undefined)

  const searchQuery = computed({
    get: () => (isSearchControlled.value ? (props.searchValue ?? '') : localSearchQuery.value),
    set: (value) => {
      const normalizedValue = normalizeSearchValue(value)

      if (!isSearchControlled.value) {
        localSearchQuery.value = normalizedValue
      }

      emit('update:searchValue', normalizedValue)
      emit('search', normalizedValue)
    },
  })

  const handleRowClick = (event, { item }) => {
    emit('row-click', item)
  }
</script>

<style scoped>
  .gap-2 {
    gap: 8px;
  }
</style>
