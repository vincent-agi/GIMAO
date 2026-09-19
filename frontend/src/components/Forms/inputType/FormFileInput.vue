<template>
  <div>
    <label v-if="label" class="field-label">
      {{ label }}
      <span v-if="isRequired" class="required-star">*</span>
    </label>
    <v-file-input
      :model-value="modelValue"
      :placeholder="placeholder"
      :accept="accept"
      :multiple="multiple"
      :show-size="showSize"
      :clearable="clearable"
      :disabled="disabled"
      :readonly="readonly"
      :prepend-icon="prependIcon"
      :prepend-inner-icon="prependInnerIcon"
      :append-icon="appendIcon"
      :append-inner-icon="appendInnerIcon"
      :hint="hint"
      :persistent-hint="persistentHint"
      :error-messages="errorMessages"
      :rules="rules"
      variant="outlined"
      density="comfortable"
      hide-details="auto"
      v-bind="$attrs"
      @update:model-value="handleFileChange"
    >
      <template v-if="$slots.selection" #selection>
        <slot name="selection"></slot>
      </template>
    </v-file-input>

    <!-- Prévisualisation de l'image -->
    <v-card v-if="previewUrl || defaultPreviewImage" class="mt-3" elevation="2" max-width="300">
      <v-img
        :src="previewUrl ? previewUrl : defaultPreviewImage ? BASE_URL + defaultPreviewImage : null"
        aspect-ratio="16/9"
        cover
      >
        <template #placeholder>
          <v-row class="fill-height ma-0" align="center" justify="center">
            <v-progress-circular indeterminate color="primary"></v-progress-circular>
          </v-row>
        </template>
      </v-img>
      <v-card-subtitle class="text-caption">Aperçu de l'image</v-card-subtitle>
    </v-card>
  </div>
</template>

<script setup>
  import { ref, watch, onBeforeUnmount, inject, computed } from 'vue'
  import { BASE_URL } from '@/utils/constants'

  defineOptions({
    inheritAttrs: false,
  })

  // Inject validation context from parent
  const isFieldRequired = inject('isFieldRequired', null)

  const props = defineProps({
    modelValue: {
      type: [File, Array],
      default: null,
    },
    label: {
      type: String,
      default: '',
    },
    placeholder: {
      type: String,
      default: 'Sélectionner un fichier',
    },
    accept: {
      type: String,
      default: undefined,
    },
    multiple: {
      type: Boolean,
      default: false,
    },
    showSize: {
      type: Boolean,
      default: true,
    },
    clearable: {
      type: Boolean,
      default: true,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
    prependIcon: {
      type: String,
      default: '',
    },
    prependInnerIcon: {
      type: String,
      default: 'mdi-paperclip',
    },
    appendIcon: {
      type: String,
      default: undefined,
    },
    appendInnerIcon: {
      type: String,
      default: undefined,
    },
    hint: {
      type: String,
      default: undefined,
    },
    persistentHint: {
      type: Boolean,
      default: false,
    },
    errorMessages: {
      type: [String, Array],
      default: undefined,
    },
    rules: {
      type: Array,
      default: () => [],
    },
    name: {
      type: String,
      default: '',
    },
    defaultPreviewImage: {
      type: String,
      default: '',
    },
  })

  const emit = defineEmits(['update:modelValue'])

  // Determine if field is required
  const isRequired = computed(() => {
    if (!props.name || !isFieldRequired) return false
    return isFieldRequired(props.name)
  })

  const previewUrl = ref(null)

  const isImageFile = (file) => {
    if (!file) return false
    return file.type && file.type.startsWith('image/')
  }

  const createPreview = (file) => {
    // Nettoyer l'ancienne URL si elle existe
    if (previewUrl.value) {
      URL.revokeObjectURL(previewUrl.value)
      previewUrl.value = null
    }

    // Créer une nouvelle URL de prévisualisation pour les images
    if (file && isImageFile(file)) {
      previewUrl.value = URL.createObjectURL(file)
    }
  }

  const normalizeFile = (value) => {
    // Vuetify 3 peut renvoyer un tableau [File] même sans multiple.
    if (Array.isArray(value)) {
      return value.length > 0 ? value[0] : null
    }
    return value || null
  }

  const handleFileChange = (value) => {
    const file = props.multiple ? value : normalizeFile(value)
    emit('update:modelValue', file)
    createPreview(props.multiple ? null : file)
  }

  // Watcher pour gérer les changements de fichier externes
  watch(
    () => props.modelValue,
    (newFile) => {
      if (!newFile) {
        // Si le fichier est supprimé, nettoyer la prévisualisation
        if (previewUrl.value) {
          URL.revokeObjectURL(previewUrl.value)
          previewUrl.value = null
        }
      } else if (newFile instanceof File) {
        createPreview(newFile)
      }
    }
  )

  // Nettoyer l'URL lors de la destruction du composant
  onBeforeUnmount(() => {
    if (previewUrl.value) {
      URL.revokeObjectURL(previewUrl.value)
    }
  })
</script>

<style scoped>
  .field-label {
    display: block;
    margin-bottom: 0px;
    font-size: 1rem;
    font-weight: 500;
    color: var(--text-color);
  }
</style>
