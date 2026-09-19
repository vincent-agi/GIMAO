<template>
  <v-dialog v-model="dialogVisible" max-width="450" :persistent="persistent">
    <v-card class="rounded-xl confirmation-modal-card">
      <v-card-title class="confirmation-modal-header pa-4">
        <span class="confirmation-modal-icon" :class="toneClass">
          <v-icon :color="iconColor" size="24">{{ modalIcon }}</v-icon>
        </span>
        <span class="modal-title">{{ title }}</span>
      </v-card-title>

      <v-divider class="confirmation-modal-divider"></v-divider>

      <v-card-text class="confirmation-modal-body pa-4">
        <p class="modal-message mb-0">{{ formattedMessage }}</p>
        <slot name="content"></slot>
      </v-card-text>

      <v-divider class="confirmation-modal-divider"></v-divider>

      <v-card-actions class="confirmation-modal-actions pa-4 d-flex justify-end">
        <v-btn
          variant="outlined"
          class="confirmation-modal-cancel mr-2"
          :disabled="loading"
          @click="handleCancel"
        >
          {{ cancelText }}
        </v-btn>
        <v-btn
          variant="flat"
          :color="confirmButtonColor"
          :loading="loading"
          :disabled="loading"
          @click="handleConfirm"
        >
          <v-icon left class="mr-1" size="20">{{ confirmIcon }}</v-icon>
          {{ confirmText }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
  /**
   * ConfirmationModal — dialogue de confirmation générique.
   *
   * Utilisé avant toute action destructive (suppression, archivage, réinitialisation).
   * Supporte quatre tons visuels (`danger`, `warning`, `info`, `success`) qui adaptent
   * l'icône et la couleur de l'en-tête.
   *
   * Slots :
   *   content — contenu additionnel sous le message principal.
   *
   * Évènements émis :
   *   confirm — clic sur le bouton de confirmation.
   *   cancel  — clic sur Annuler ou fermeture du dialog.
   */
  import { computed } from 'vue'

  const props = defineProps({
    // Contrôle de la visibilité
    modelValue: {
      type: Boolean,
      default: false,
    },
    // Type de modale (success, warning, error, info)
    type: {
      type: String,
      default: 'warning',
      validator: (value) => ['success', 'warning', 'error', 'info'].includes(value),
    },
    // Contenu
    title: {
      type: String,
      default: 'Confirmation requise',
    },
    message: {
      type: String,
      default: 'Êtes-vous sûr de vouloir effectuer cette action ?',
    },
    // Personnalisation des boutons
    confirmText: {
      type: String,
      default: 'Confirmer',
    },
    cancelText: {
      type: String,
      default: 'Annuler',
    },
    confirmIcon: {
      type: String,
      default: 'mdi-check',
    },
    // Couleur personnalisée (optionnel)
    confirmColor: {
      type: String,
      default: '',
    },
    // État de chargement perrmet de désactiver les boutons pendant les requêtes ou chargements
    loading: {
      type: Boolean,
      default: false,
    },
    // Allow closing by clicking outside when false
    persistent: {
      type: Boolean,
      default: false,
    },
  })

  const emit = defineEmits(['update:modelValue', 'confirm', 'cancel'])

  const dialogVisible = computed({
    get: () => props.modelValue,
    set: (value) => emit('update:modelValue', value),
  })

  // Configuration par type
  const typeConfig = {
    success: {
      icon: 'mdi-check-circle-outline',
      color: 'success',
      iconColor: 'success',
    },
    warning: {
      icon: 'mdi-alert-circle-outline',
      color: 'primary',
      iconColor: 'primary',
    },
    error: {
      icon: 'mdi-close-circle-outline',
      color: 'error',
      iconColor: 'error',
    },
    info: {
      icon: 'mdi-information-outline',
      color: 'primary',
      iconColor: 'primary',
    },
  }

  const modalIcon = computed(() => typeConfig[props.type]?.icon || typeConfig.warning.icon)
  const iconColor = computed(() => typeConfig[props.type]?.iconColor || 'warning')
  const toneClass = computed(() => `confirmation-modal-icon--${props.type}`)

  const confirmButtonColor = computed(() => {
    if (props.confirmColor) return props.confirmColor
    return typeConfig[props.type]?.color || 'warning'
  })

  // Remplace les \n en vrais retours à la ligne
  const formattedMessage = computed(() => {
    return props.message.replace(/\\n/g, '\n')
  })

  const handleConfirm = () => {
    emit('confirm')
  }

  const handleCancel = () => {
    emit('cancel')
    dialogVisible.value = false
  }
</script>

<style scoped>
  .confirmation-modal-card {
    border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
    box-shadow: 0 22px 50px rgba(10, 15, 30, 0.18);
    overflow: hidden;
  }

  .confirmation-modal-header {
    align-items: center;
    background: rgba(var(--v-theme-on-surface), 0.02);
    display: flex;
    gap: 14px;
  }

  .confirmation-modal-icon {
    align-items: center;
    border-radius: 14px;
    display: inline-flex;
    flex: 0 0 auto;
    height: 44px;
    justify-content: center;
    width: 44px;
  }

  .confirmation-modal-icon--success {
    background: rgba(var(--v-theme-success), 0.14);
  }

  .confirmation-modal-icon--warning {
    background: rgba(var(--v-theme-primary), 0.12);
  }

  .confirmation-modal-icon--error {
    background: rgba(var(--v-theme-error), 0.14);
  }

  .confirmation-modal-icon--info {
    background: rgba(var(--v-theme-info), 0.14);
  }

  .confirmation-modal-divider {
    opacity: 0.7;
  }

  .modal-title {
    font-weight: 600;
    font-size: 1.125rem;
    color: rgba(var(--v-theme-on-surface), 0.96);
  }

  .confirmation-modal-body {
    color: rgba(var(--v-theme-on-surface), 0.76);
  }

  .modal-message {
    font-size: 0.95rem;
    color: inherit;
    line-height: 1.5;
    white-space: pre-line;
  }

  .confirmation-modal-actions {
    gap: 12px;
  }

  .confirmation-modal-cancel {
    color: rgba(var(--v-theme-on-surface), 0.8);
  }
</style>
