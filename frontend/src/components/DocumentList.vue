<template>
  <div>
    <v-data-table
      :headers="headers"
      :items="documents"
      class="elevation-1 document-table"
      hide-default-footer
      :items-per-page="-1"
    >
      <template #[`item.name`]="{ item }">
        <div style="word-wrap: break-word; white-space: normal">
          {{ item.titre }}
        </div>
      </template>

      <template #[`item.type`]="{ item }">
        <div style="word-wrap: break-word; white-space: normal">
          {{ item.type_nom }}
        </div>
      </template>

      <template #[`item.actions`]="{ item }">
        <div class="text-no-wrap">
          <v-btn
            icon
            size="small"
            color="primary"
            :class="{ 'mr-1': showDelete }"
            :disabled="downloadingDoc"
            @click="handleDownload(item)"
          >
            <v-icon>mdi-download</v-icon>
          </v-btn>

          <v-btn
            v-if="showDelete"
            icon
            size="small"
            color="error"
            :disabled="deletingDoc"
            @click="openDeleteModal(item)"
          >
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </div>
      </template>

      <template #no-data>
        <div class="text-center pa-4">
          <v-icon size="48" color="grey-lighten-1">mdi-file-document-outline</v-icon>
          <p class="text-grey mt-2">Aucun document</p>
        </div>
      </template>
    </v-data-table>

    <!-- Modale de confirmation de suppression -->
    <ConfirmationModal
      v-model="showDeleteModal"
      type="error"
      title="Supprimer le document"
      :message="deleteMessage"
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
  import { computed, ref } from 'vue'
  import { useApi } from '@/composables/useApi'
  import { BASE_URL, MEDIA_BASE_URL, API_BASE_URL, TABLE_HEADERS } from '@/utils/constants'
  import ConfirmationModal from '@/components/common/ConfirmationModal.vue'

  const props = defineProps({
    documents: {
      type: Array,
      default: () => [],
    },
    showType: {
      type: Boolean,
      default: false,
    },
    showDelete: {
      type: Boolean,
      default: true,
    },
  })

  const emit = defineEmits(['delete-success', 'delete-error', 'download-error', 'download-success'])

  const api = useApi(API_BASE_URL)

  const downloadingDoc = ref(false)
  const deletingDoc = ref(false)
  const showDeleteModal = ref(false)
  const docToDelete = ref(null)

  const deleteMessage = computed(() => {
    const name = docToDelete.value?.titre || 'ce document'
    return `Êtes-vous sûr de vouloir supprimer le document "${name}" ?\n\nCette action est irréversible.`
  })

  const openDeleteModal = (item) => {
    docToDelete.value = item
    showDeleteModal.value = true
  }

  const cancelDelete = () => {
    showDeleteModal.value = false
    docToDelete.value = null
  }

  const confirmDelete = async () => {
    if (!docToDelete.value?.id) {
      emit('delete-error', 'ID du document introuvable')
      showDeleteModal.value = false
      docToDelete.value = null
      return
    }

    deletingDoc.value = true
    try {
      await api.remove(`documents/${docToDelete.value.id}/`)
      showDeleteModal.value = false
      docToDelete.value = null
      emit('delete-success')
    } catch {
      emit('delete-error', 'Erreur lors de la suppression du document')
    } finally {
      deletingDoc.value = false
    }
  }

  const handleDownload = async (item) => {
    downloadingDoc.value = true
    try {
      const raw = item?.path || item?.lienDocumentIntervention || item?.cheminAcces
      if (!raw) {
        emit('download-error', 'Chemin du document introuvable')
        return
      }

      const path = String(raw).replace(/^\/+/, '').split('/media/').pop()
      const response = await fetch(`${BASE_URL}${MEDIA_BASE_URL}${path}`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.style.display = 'none'
      a.href = url
      a.download = path.split('/').pop() || 'document'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      emit('download-success')
    } catch {
      emit('download-error', 'Erreur lors du téléchargement du document')
    } finally {
      downloadingDoc.value = false
    }
  }

  const headers = computed(() => {
    // Mapper les headers de constants.js au format Vuetify 3
    const baseHeaders = TABLE_HEADERS.DOCUMENTS.map((h) => ({
      title: h.title,
      key:
        h.value === 'nomDocument'
          ? 'name'
          : h.value === 'typeDocument'
            ? 'type'
            : h.value === 'action'
              ? 'actions'
              : h.value,
      align: h.align,
      sortable: h.sortable,
    }))

    if (!props.showType) {
      // Filtrer la colonne Type si showType est false
      return baseHeaders.filter((h) => h.key !== 'type')
    }

    return baseHeaders
  })
</script>

<style scoped>
  .document-table :deep(table) {
    table-layout: fixed;
    width: 100%;
  }

  .document-table :deep(.v-data-table__wrapper) {
    overflow-x: hidden !important;
  }

  .document-table :deep(td:first-child),
  .document-table :deep(th:first-child) {
    width: auto !important;
  }

  .document-table :deep(td:nth-child(2)),
  .document-table :deep(th:nth-child(2)) {
    width: auto !important;
  }

  .document-table :deep(td:last-child),
  .document-table :deep(th:last-child) {
    width: 110px !important;
    text-align: center;
  }
</style>
