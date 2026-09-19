<template>
  <div>
    <v-row v-for="(doc, index) in documents" :key="index" dense class="mb-2">
      <v-col cols="12" md="3">
        <FormField
          :model-value="doc.nomDocument"
          :field-name="`document_nom_${index}`"
          label="Nom"
          placeholder="Nom du document"
          clearable
          @update:model-value="(value) => updateDocument(index, { nomDocument: value })"
        />
      </v-col>

      <v-col cols="12" md="3">
        <FormSelect
          :model-value="doc.typeDocument_id"
          :field-name="`document_type_${index}`"
          label="Type"
          :items="typeDocuments"
          item-title="nomTypeDocument"
          item-value="id"
          placeholder="Sélectionner un type"
          :rules="[(v) => !!v || 'Le type est requis']"
          @update:model-value="(value) => updateDocument(index, { typeDocument_id: value })"
        />
      </v-col>

      <v-col cols="12" md="5">
        <FormFileInput
          :model-value="doc.file"
          :name="`document_file_${index}`"
          label="Fichier"
          @update:model-value="(value) => updateDocument(index, { file: value })"
        />
        <div v-if="doc.existingFileName" class="mt-1 text-caption text-grey">
          Fichier actuel: {{ doc.existingFileName }}
        </div>
      </v-col>

      <v-col cols="12" md="1" class="d-flex align-center justify-center">
        <v-btn icon="mdi-delete" size="small" color="error" @click="openDeleteModal(index)" />
      </v-col>
    </v-row>

    <v-row dense>
      <v-col cols="12">
        <v-btn variant="outlined" color="primary" size="small" @click="addDocument">
          <v-icon left>mdi-plus</v-icon>
          Ajouter un document
        </v-btn>
      </v-col>
    </v-row>

    <!-- Modale de confirmation de suppression -->
    <ConfirmationModal
      v-model="showDeleteModal"
      type="error"
      title="Supprimer le document"
      message="Êtes-vous sûr de vouloir supprimer ce document ?\n\nCette action est irréversible."
      confirm-text="Supprimer"
      cancel-text="Annuler"
      confirm-icon="mdi-delete"
      :loading="deletingDoc"
      @confirm="confirmDelete"
      @cancel="cancelDelete"
    />
  </div>
</template>

<script setup>
  import { computed, provide, ref } from 'vue'
  import { FormField, FormSelect, FormFileInput } from '@/components/common'
  import ConfirmationModal from '@/components/common/ConfirmationModal.vue'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'

  const props = defineProps({
    modelValue: {
      type: Array,
      default: () => [],
    },
    typeDocuments: {
      type: Array,
      default: () => [],
    },
  })

  const emit = defineEmits(['update:modelValue'])

  const EMPTY_ROW = {
    document_id: null,
    nomDocument: '',
    typeDocument_id: null,
    file: null,
    existingFileName: null,
  }

  const documents = computed(() => (Array.isArray(props.modelValue) ? props.modelValue : []))

  // Fonction isFieldRequired personnalisée pour gérer les fichiers existants
  const isFieldRequired = (fieldName) => {
    // Extraire l'index du nom du champ
    const match = fieldName.match(/document_(\w+)_(\d+)/)
    if (!match) return false

    const [, fieldType, indexStr] = match
    const index = parseInt(indexStr)

    // Type est toujours requis
    if (fieldType === 'type') return true

    // Fichier requis seulement si pas de fichier existant
    if (fieldType === 'file') {
      return !documents.value[index]?.existingFileName
    }

    return false
  }

  // Fournir isFieldRequired aux composants enfants
  provide('isFieldRequired', isFieldRequired)

  const updateDocument = (index, patch) => {
    const current = Array.isArray(props.modelValue) ? props.modelValue : []
    if (index < 0 || index >= current.length) return
    const next = current.map((doc, i) => (i === index ? { ...doc, ...patch } : doc))
    emit('update:modelValue', next)
  }

  const addDocument = () => {
    const current = Array.isArray(props.modelValue) ? props.modelValue : []
    emit('update:modelValue', [...current, { ...EMPTY_ROW }])
  }

  const showDeleteModal = ref(false)
  const deletingDoc = ref(false)
  const indexToDelete = ref(null)

  const openDeleteModal = (index) => {
    const current = Array.isArray(props.modelValue) ? props.modelValue : []
    if (index < 0 || index >= current.length) return
    const doc = current[index]

    // Si c'est un document existant (avec ID), on ouvre la modale
    if (
      doc?.document_id &&
      Number.isInteger(Number(doc.document_id)) &&
      Number(doc.document_id) > 0
    ) {
      indexToDelete.value = index
      showDeleteModal.value = true
    } else {
      // Sinon, on supprime directement la ligne vide
      const next = current.filter((_, i) => i !== index)
      emit('update:modelValue', next)
    }
  }

  const cancelDelete = () => {
    showDeleteModal.value = false
    indexToDelete.value = null
  }

  const confirmDelete = async () => {
    if (indexToDelete.value === null) return

    const current = Array.isArray(props.modelValue) ? props.modelValue : []
    if (indexToDelete.value < 0 || indexToDelete.value >= current.length) {
      showDeleteModal.value = false
      indexToDelete.value = null
      return
    }
    const doc = current[indexToDelete.value]

    // Si le document a un ID (document existant), on le supprime du backend
    if (
      doc?.document_id &&
      Number.isInteger(Number(doc.document_id)) &&
      Number(doc.document_id) > 0
    ) {
      deletingDoc.value = true
      try {
        const api = useApi(API_BASE_URL)
        await api.remove(`documents/${doc.document_id}/`)
      } catch (error) {
        console.error('Erreur lors de la suppression du document:', error)
      } finally {
        deletingDoc.value = false
      }
    }

    const next = current.filter((_, i) => i !== indexToDelete.value)
    emit('update:modelValue', next)

    showDeleteModal.value = false
    indexToDelete.value = null
  }
</script>
