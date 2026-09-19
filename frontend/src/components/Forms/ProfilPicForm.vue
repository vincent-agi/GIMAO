<template>
  <v-sheet
    class="pa-4 profil-pic-dropzone"
    elevation="1"
    rounded
    :class="{ 'profil-pic-dropzone--active': isPhotoDragActive }"
    @dragenter.prevent="onPhotoDragEnter"
    @dragover.prevent="onPhotoDragOver"
    @dragleave.prevent="onPhotoDragLeave"
    @drop.prevent="onPhotoDrop"
  >
    <div class="d-flex align-center justify-space-between profil-pic-header">
      <div class="d-flex align-center" style="min-width: 0">
        <v-avatar size="64" color="grey lighten-3" class="mr-3">
          <v-img v-if="displayPhotoUrl" :src="displayPhotoUrl" cover />
          <v-icon v-else color="grey darken-1">mdi-account</v-icon>
        </v-avatar>

        <div style="min-width: 0">
          <div class="text-body-1 font-weight-medium">Photo de profil</div>
          <div class="caption" :class="photoError ? 'error--text' : 'grey--text'">
            {{ photoError || photoFileLabel }}
          </div>
        </div>
      </div>

      <div class="d-flex align-center profil-pic-actions">
        <template v-if="hasPhoto">
          <v-btn icon size="small" title="Supprimer la photo" @click.stop="deletePhoto">
            <v-icon>mdi-delete</v-icon>
          </v-btn>

          <v-btn icon size="small" title="Télécharger la photo" @click.stop="downloadPhoto">
            <v-icon>mdi-download</v-icon>
          </v-btn>

          <v-btn icon size="small" title="Modifier la photo" @click.stop="triggerPhotoPicker">
            <v-icon>mdi-pencil</v-icon>
          </v-btn>
        </template>

        <v-btn
          v-else
          icon
          size="small"
          title="Téléverser une photo"
          @click.stop="triggerPhotoPicker"
        >
          <v-icon>mdi-upload</v-icon>
        </v-btn>
      </div>
    </div>

    <input ref="photoInput" type="file" accept="image/*" class="d-none" @change="onPhotoPicked" />
  </v-sheet>
</template>

<script setup>
  import { computed, onBeforeUnmount, ref, watch } from 'vue'
  import { BASE_URL, MEDIA_BASE_URL } from '@/utils/constants'

  const props = defineProps({
    // Pour le mode création : fichier sélectionné
    modelValue: {
      type: [File, null],
      default: null,
    },
    // Pour le mode édition : chemin de la photo existante
    existingPhotoPath: {
      type: String,
      default: '',
    },
  })

  const emit = defineEmits(['update:modelValue', 'delete-existing'])

  const photoInput = ref(null)
  const isPhotoDragActive = ref(false)
  const photoPreviewUrl = ref('')
  const photoError = ref('')
  const removeExistingPhoto = ref(false)

  // URL de la photo existante (mode édition)
  const existingPhotoUrl = computed(() => {
    if (!props.existingPhotoPath || removeExistingPhoto.value) return ''
    return `${BASE_URL}${MEDIA_BASE_URL}${props.existingPhotoPath}`
  })

  // URL à afficher (preview > existante)
  const displayPhotoUrl = computed(() => {
    if (photoPreviewUrl.value) return photoPreviewUrl.value
    return existingPhotoUrl.value
  })

  // Label du fichier
  const photoFileLabel = computed(() => {
    if (props.modelValue instanceof File) return props.modelValue.name
    if (props.existingPhotoPath && !removeExistingPhoto.value) {
      return props.existingPhotoPath.split('/').pop()
    }
    return 'Aucun fichier'
  })

  // Y a-t-il une photo affichée ?
  const hasPhoto = computed(() => {
    return !!displayPhotoUrl.value
  })

  // Libère l'URL blob si existante
  const revokePhotoPreviewUrl = () => {
    if (photoPreviewUrl.value) {
      URL.revokeObjectURL(photoPreviewUrl.value)
      photoPreviewUrl.value = ''
    }
  }

  // Sélectionne un fichier
  const setPhotoFile = (file) => {
    photoError.value = ''

    if (!file) {
      emit('update:modelValue', null)
      revokePhotoPreviewUrl()
      if (photoInput.value) photoInput.value.value = ''
      return
    }

    if (!file.type || !file.type.startsWith('image/')) {
      photoError.value = 'Le fichier doit être une image.'
      return
    }

    emit('update:modelValue', file)
    removeExistingPhoto.value = false
    revokePhotoPreviewUrl()
    photoPreviewUrl.value = URL.createObjectURL(file)
  }

  // Ouvre le sélecteur de fichier
  const triggerPhotoPicker = () => {
    photoError.value = ''
    photoInput.value?.click?.()
  }

  // Télécharge la photo
  const downloadPhoto = () => {
    const url = displayPhotoUrl.value
    if (!url) return

    const filename =
      props.modelValue instanceof File
        ? props.modelValue.name
        : props.existingPhotoPath
          ? props.existingPhotoPath.split('/').pop()
          : 'photo-profil'

    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.rel = 'noopener'
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    link.remove()
  }

  // Supprime la photo
  const deletePhoto = () => {
    // Si une nouvelle photo est sélectionnée (preview), on la retire
    if (photoPreviewUrl.value) {
      setPhotoFile(null)
      return
    }

    // Sinon on marque la suppression de la photo existante
    if (props.existingPhotoPath) {
      removeExistingPhoto.value = true
      emit('delete-existing')
    }
  }

  // Événements fichier
  const onPhotoPicked = (e) => {
    const file = e?.target?.files?.[0]
    setPhotoFile(file || null)
  }

  // Événements drag & drop
  const onPhotoDragEnter = () => {
    isPhotoDragActive.value = true
  }

  const onPhotoDragOver = () => {
    isPhotoDragActive.value = true
  }

  const onPhotoDragLeave = () => {
    isPhotoDragActive.value = false
  }

  const onPhotoDrop = (e) => {
    isPhotoDragActive.value = false
    const file = e?.dataTransfer?.files?.[0]
    setPhotoFile(file || null)
  }

  // Sync avec la prop modelValue
  watch(
    () => props.modelValue,
    (newVal) => {
      if (!newVal) {
        revokePhotoPreviewUrl()
      }
    }
  )

  // Réinitialiser quand le chemin existant change
  watch(
    () => props.existingPhotoPath,
    () => {
      removeExistingPhoto.value = false
      revokePhotoPreviewUrl()
      emit('update:modelValue', null)
    }
  )

  // Nettoyage
  onBeforeUnmount(() => {
    revokePhotoPreviewUrl()
  })

  // Exposer removeExistingPhoto pour le parent
  defineExpose({
    removeExistingPhoto,
  })
</script>

<style scoped>
  .profil-pic-dropzone {
    border: 2px dashed rgba(0, 0, 0, 0.12);
    cursor: pointer;
    transition:
      border-color 0.15s ease,
      background-color 0.15s ease;
  }

  .profil-pic-dropzone--active {
    border-color: #1976d2 !important;
    background-color: rgba(25, 118, 210, 0.05);
  }

  .profil-pic-actions {
    gap: 8px;
  }

  @media (max-width: 600px) {
    .profil-pic-header {
      flex-direction: column;
      align-items: flex-start;
    }

    .profil-pic-actions {
      width: 100%;
      justify-content: flex-end;
      margin-top: 10px;
    }
  }
</style>
