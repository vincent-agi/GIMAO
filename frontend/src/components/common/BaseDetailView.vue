<template>
  <v-container :fluid="fluid">
    <!-- Breadcrumbs -->
    <v-row v-if="showBreadcrumbs && breadcrumbs.length > 0" class="mb-4">
      <v-col>
        <v-breadcrumbs :items="breadcrumbs" class="pa-0">
          <template #divider>
            <v-icon>mdi-chevron-right</v-icon>
          </template>
        </v-breadcrumbs>
      </v-col>
    </v-row>

    <!-- Header avec titre et actions -->
    <v-row class="mb-4">
      <v-col>
        <div class="d-flex align-center justify-space-between">
          <div>
            <h1 v-if="title" :class="titleClass">{{ title }}</h1>
            <p v-if="subtitle" :class="subtitleClass">{{ subtitle }}</p>
          </div>
          <div class="d-flex gap-2">
            <slot name="actions">
              <v-btn
                v-if="showBackButton"
                :color="backButtonColor"
                :variant="backButtonVariant"
                :prepend-icon="backButtonIcon"
                @click="handleBack"
              >
                {{ backButtonText }}
              </v-btn>
              <v-btn
                v-if="showEditButton"
                :color="editButtonColor"
                :prepend-icon="editButtonIcon"
                @click="$emit('edit')"
              >
                {{ editButtonText }}
              </v-btn>
              <v-btn
                v-if="showDeleteButton"
                :color="deleteButtonColor"
                :prepend-icon="deleteButtonIcon"
                @click="$emit('delete')"
              >
                {{ deleteButtonText }}
              </v-btn>
            </slot>
          </div>
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
      v-if="successMessage"
      :message="successMessage"
      type="success"
      dismissible
      class="mb-4"
      @close="$emit('clear-success')"
    />

    <FormAlert
      v-if="loading && loadingMessage"
      :message="loadingMessage"
      type="info"
      class="mb-4"
    />

    <!-- Contenu principal -->
    <v-card v-if="!loading || data" :elevation="elevation" :class="cardClass">
      <v-card-text :class="contentClass">
        <slot :data="data">
          <!-- Affichage par défaut des données sous forme de liste -->
          <v-row v-if="data && autoDisplay">
            <v-col
              v-for="(value, key) in displayData"
              :key="key"
              :cols="fieldCols"
              :md="fieldMd"
              :lg="fieldLg"
            >
              <div class="detail-field">
                <label class="detail-label">{{ formatLabel(key) }}</label>
                <div class="detail-value">
                  <slot :key="key" :name="`field.${key}`" :value="value">
                    {{ formatValue(value) }}
                  </slot>
                </div>
              </div>
            </v-col>
          </v-row>
        </slot>
      </v-card-text>
    </v-card>

    <!-- Skeleton loader pendant le chargement -->
    <v-card v-else :elevation="elevation" :class="cardClass">
      <v-card-text>
        <v-skeleton-loader type="article, actions"></v-skeleton-loader>
      </v-card-text>
    </v-card>

    <!-- Slots supplémentaires -->
    <slot name="additional-content"></slot>
  </v-container>
</template>

<script setup>
  /**
   * BaseDetailView — mise en page standard pour les pages de détail d'une entité.
   *
   * Fournit un en-tête avec titre, breadcrumbs optionnels, boutons Retour/Modifier/Supprimer,
   * une zone d'alerte, et un affichage automatique des champs de l'objet (`autoDisplay`).
   *
   * Slots :
   *   actions        — surcharge des boutons d'en-tête.
   *   default        — contenu principal (affiché sous l'en-tête).
   *   extra-sections — sections supplémentaires sous le contenu principal.
   *
   * Évènements émis :
   *   edit          — clic sur Modifier.
   *   delete        — clic sur Supprimer.
   *   back          — clic sur Retour (navigue aussi via router si `backRoute` est fourni).
   *   clear-error   — fermeture de l'alerte d'erreur.
   *   clear-success — fermeture de l'alerte de succès.
   */
  import { computed, watch } from 'vue'
  import { useRouter } from 'vue-router'
  import FormAlert from './FormAlert.vue'

  const props = defineProps({
    // Données
    data: {
      type: Object,
      default: null,
    },
    excludeFields: {
      type: Array,
      default: () => [],
    },
    includeFields: {
      type: Array,
      default: () => [],
    },
    autoDisplay: {
      type: Boolean,
      default: true,
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

    // Breadcrumbs
    showBreadcrumbs: {
      type: Boolean,
      default: false,
    },
    breadcrumbs: {
      type: Array,
      default: () => [],
    },

    // Bouton retour
    showBackButton: {
      type: Boolean,
      default: true,
    },
    backButtonText: {
      type: String,
      default: 'Retour',
    },
    backButtonColor: {
      type: String,
      default: 'secondary',
    },
    backButtonVariant: {
      type: String,
      default: 'text',
    },
    backButtonIcon: {
      type: String,
      default: 'mdi-arrow-left',
    },

    // Bouton édition
    showEditButton: {
      type: Boolean,
      default: false,
    },
    editButtonText: {
      type: String,
      default: 'Modifier',
    },
    editButtonColor: {
      type: String,
      default: 'primary',
    },
    editButtonIcon: {
      type: String,
      default: 'mdi-pencil',
    },

    // Bouton suppression
    showDeleteButton: {
      type: Boolean,
      default: false,
    },
    deleteButtonText: {
      type: String,
      default: 'Supprimer',
    },
    deleteButtonColor: {
      type: String,
      default: 'error',
    },
    deleteButtonIcon: {
      type: String,
      default: 'mdi-delete',
    },

    // Messages
    loading: {
      type: Boolean,
      default: false,
    },
    loadingMessage: {
      type: String,
      default: 'Chargement...',
    },
    errorMessage: {
      type: String,
      default: '',
    },
    successMessage: {
      type: String,
      default: '',
    },

    // Layout des champs
    fieldCols: {
      type: [Number, String],
      default: 12,
    },
    fieldMd: {
      type: [Number, String],
      default: 6,
    },
    fieldLg: {
      type: [Number, String],
      default: 4,
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
      default: 'rounded-lg pa-4',
    },
    contentClass: {
      type: String,
      default: '',
    },
  })

  const emit = defineEmits(['edit', 'delete', 'back', 'clear-error', 'clear-success'])

  const router = useRouter()

  let successTimer = null
  watch(
    () => props.successMessage,
    (val) => {
      if (successTimer) clearTimeout(successTimer)
      if (val) successTimer = setTimeout(() => emit('clear-success'), 4000)
    }
  )

  const displayData = computed(() => {
    if (!props.data) return {}

    let fields = { ...props.data }

    // Filtrer les champs à inclure
    if (props.includeFields.length > 0) {
      fields = Object.keys(fields)
        .filter((key) => props.includeFields.includes(key))
        .reduce((obj, key) => {
          obj[key] = fields[key]
          return obj
        }, {})
    }

    // Exclure les champs
    if (props.excludeFields.length > 0) {
      props.excludeFields.forEach((field) => {
        delete fields[field]
      })
    }

    return fields
  })

  const formatLabel = (key) => {
    // Convertir camelCase et snake_case en espaces avec majuscules
    return key
      .replace(/([A-Z])/g, ' $1')
      .replace(/_/g, ' ')
      .replace(/^./, (str) => str.toUpperCase())
      .trim()
  }

  const formatValue = (value) => {
    if (value === null || value === undefined) return '-'
    if (typeof value === 'boolean') return value ? 'Oui' : 'Non'
    if (typeof value === 'object') return JSON.stringify(value)
    if (value === '') return '-'
    return value
  }

  const handleBack = () => {
    emit('back')
    router.go(-1)
  }
</script>

<style scoped>
  .gap-2 {
    gap: 8px;
  }

  .detail-field {
    margin-bottom: 16px;
  }

  .detail-label {
    display: block;
    font-weight: 600;
    font-size: 0.875rem;
    color: var(--text-color);
    opacity: 0.7;
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .detail-value {
    font-size: 1rem;
    color: var(--text-color);
    padding: 8px 0;
    border-bottom: 1px solid rgba(128, 128, 128, 0.25);
  }
</style>
