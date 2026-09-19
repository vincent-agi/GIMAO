<template>
  <BaseForm
    v-model="formData"
    title="Ajouter des documents au bon de travail"
    :loading="loading"
    :error-message="errorMessage"
    :success-message="successMessage"
    submit-button-text="Ajouter les documents"
    submit-button-color="success"
    @submit="handleSubmit"
    @cancel="goBack"
    @clear-error="errorMessage = ''"
    @clear-success="successMessage = ''"
  >
    <template #default="{ formData: innerFormData }">
      <DocumentForm
        v-model="innerFormData.documents"
        :type-documents="typeDocuments"
        :exclude-document-ids="alreadyLinkedDocumentIds"
      />
    </template>
  </BaseForm>
</template>

<script setup>
  import { computed, onMounted, ref } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import { useStore } from 'vuex'
  import BaseForm from '@/components/common/BaseForm.vue'
  import DocumentForm from '@/components/Forms/DocumentForm.vue'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'

  const route = useRoute()
  const router = useRouter()
  const store = useStore()
  const api = useApi(API_BASE_URL)

  const loading = ref(false)
  const errorMessage = ref('')
  const successMessage = ref('')

  const connectedUser = computed(() => store.getters.currentUser)

  const bonTravailId = computed(() => Number(route.params.id))

  const typeDocuments = ref([])
  const alreadyLinkedDocumentIds = ref([])

  const formData = ref({
    documents: [{ document_id: null, nomDocument: '', typeDocument_id: null, file: null }],
  })

  const loadTypeDocuments = async () => {
    try {
      typeDocuments.value = await api.get('types-documents/')
    } catch {
      typeDocuments.value = []
    }
  }

  const loadAlreadyLinkedDocuments = async () => {
    try {
      const bonId = bonTravailId.value
      if (!Number.isInteger(bonId) || bonId <= 0) {
        alreadyLinkedDocumentIds.value = []
        return
      }
      const bon = await api.get(`bons-travail/${bonId}/`)
      const ids = Array.isArray(bon?.documentsBT)
        ? bon.documentsBT.map((d) => Number(d?.id)).filter((x) => Number.isInteger(x) && x > 0)
        : []
      alreadyLinkedDocumentIds.value = ids
    } catch {
      alreadyLinkedDocumentIds.value = []
    }
  }

  const linkExistingDocumentsToBonTravail = async (bonId, payload) => {
    const docs = Array.isArray(payload?.documents) ? payload.documents : []
    const ids = docs.map((d) => Number(d?.document_id)).filter((x) => Number.isInteger(x) && x > 0)

    const errors = []
    for (const id of ids) {
      try {
        await api.post(`bons-travail/${bonId}/ajouter_document/`, {
          document_id: id,
          user: connectedUser.value?.id,
        })
      } catch {
        errors.push(`Document #${id}`)
      }
    }
    return errors
  }

  const createNewDocumentsThenLinkToBonTravail = async (bonId, payload) => {
    const docs = Array.isArray(payload?.documents) ? payload.documents : []
    const errors = []

    for (const doc of docs) {
      if (!doc) continue
      const existingId = Number(doc.document_id)
      if (Number.isInteger(existingId) && existingId > 0) continue
      if (!doc.file && !doc.typeDocument_id && !(doc.nomDocument || '').trim()) continue
      if (!doc.file || !doc.typeDocument_id) {
        errors.push(doc.nomDocument || doc.file?.name || 'Document')
        continue
      }

      try {
        const form = new FormData()
        form.append('nomDocument', (doc.nomDocument || doc.file.name || '').toString())
        form.append('typeDocument_id', String(doc.typeDocument_id))
        form.append('cheminAcces', doc.file)

        const created = await api.post('documents/', form)
        const newId = Number(created?.id)
        if (!Number.isInteger(newId) || newId <= 0) {
          errors.push(doc.nomDocument || doc.file?.name || 'Document')
          continue
        }

        try {
          await api.post(`bons-travail/${bonId}/ajouter_document/`, {
            document_id: newId,
            user: connectedUser.value?.id,
          })
        } catch {
          try {
            await api.delete(`documents/${newId}/`)
          } catch {
            // ignore
          }
          errors.push(doc.nomDocument || doc.file?.name || 'Document')
        }
      } catch {
        errors.push(doc.nomDocument || doc.file?.name || 'Document')
      }
    }

    return errors
  }

  const handleSubmit = async (payload) => {
    loading.value = true
    errorMessage.value = ''
    successMessage.value = ''

    try {
      const bonId = bonTravailId.value
      if (!Number.isInteger(bonId) || bonId <= 0) {
        errorMessage.value = 'Bon de travail invalide.'
        return
      }

      const docs = Array.isArray(payload?.documents) ? payload.documents : []
      const hasAnyDoc = docs.some((d) => {
        const id = Number(d?.document_id)
        if (Number.isInteger(id) && id > 0) return true
        return Boolean(d?.file || d?.typeDocument_id || (d?.nomDocument || '').trim())
      })
      if (!hasAnyDoc) {
        errorMessage.value = 'Ajoute au moins un document.'
        return
      }

      const linkErrors = await linkExistingDocumentsToBonTravail(bonId, payload)
      const createErrors = await createNewDocumentsThenLinkToBonTravail(bonId, payload)
      const docErrors = [...linkErrors, ...createErrors]
      if (docErrors.length) {
        errorMessage.value = `Certains documents n'ont pas pu être ajoutés: ${docErrors.join(', ')}`
        return
      }

      successMessage.value = 'Documents ajoutés avec succès.'
      setTimeout(() => {
        router.push({ name: 'InterventionDetail', params: { id: bonId } })
      }, 600)
    } catch (e) {
      console.error("Erreur lors de l'ajout des documents:", e)
      errorMessage.value = "Erreur lors de l'ajout des documents."
    } finally {
      loading.value = false
    }
  }

  const goBack = () => {
    const bonId = bonTravailId.value
    router.push({ name: 'InterventionDetail', params: { id: bonId } })
  }

  onMounted(async () => {
    await Promise.all([loadTypeDocuments(), loadAlreadyLinkedDocuments()])
  })
</script>
