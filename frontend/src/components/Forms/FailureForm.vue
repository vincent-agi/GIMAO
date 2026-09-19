<template>
  <BaseForm
    v-model="formData"
    :title="title"
    :validation-schema="validationSchema"
    :loading="loading"
    :error-message="errorMessage"
    :success-message="successMessage"
    :handle-submit="save"
    :custom-cancel-action="close"
    :submit-button-text="submitButtonText"
    elevation="0"
  >
    <v-row dense>
      <v-col cols="12">
        <v-text-field
          :model-value="numeroDI"
          label="Numéro de Demande d'intervention"
          variant="outlined"
          density="comfortable"
          readonly
          :loading="loadingNumeroDI"
          prepend-inner-icon="mdi-identifier"
        />
      </v-col>

      <v-col cols="12">
        <FormSelect
          v-model="formData.equipement_id"
          field-name="equipement_id"
          label="Équipement"
          :items="equipments"
          item-title="designation"
          item-value="id"
          placeholder="Sélectionner un équipement"
          :disabled="isEdit"
        />
      </v-col>

      <v-col cols="12">
        <FormSelect
          v-model="formData.statut_suppose"
          field-name="statut_suppose"
          label="Statut supposé de l'équipement"
          :items="statutOptions"
          item-title="title"
          item-value="value"
          placeholder="Sélectionner le statut supposé de l'équipement"
        />
      </v-col>

      <v-col cols="12">
        <FormTextarea
          v-model="formData.commentaire"
          field-name="commentaire"
          label="Commentaires"
          placeholder="Ajouter des détails ou une description..."
          rows="5"
          counter="300"
        />
      </v-col>

      <!-- Documents -->
      <v-col cols="12">
        <v-divider class="my-4"></v-divider>
        <div class="pb-2" style="font-size: 20px">Documents (optionnels)</div>

        <DocumentForm v-model="formData.documents" :type-documents="typesDocuments" />
      </v-col>
    </v-row>
  </BaseForm>
</template>

<script setup>
  import { ref, computed, watch, onMounted } from 'vue'
  import { BaseForm, FormSelect, FormTextarea } from '@/components/common'
  import DocumentForm from '@/components/Forms/DocumentForm.vue'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL, EQUIPMENT_STATUS } from '@/utils/constants'

  const statutOptions = Object.entries(EQUIPMENT_STATUS).map(([key, value]) => ({
    title: value,
    value: key,
  }))

  const props = defineProps({
    title: {
      type: String,
      default: "Ajouter une demande d'intervention",
    },
    submitButtonText: {
      type: String,
      default: 'Créer',
    },
    isEdit: {
      type: Boolean,
      default: false,
    },
    initialData: {
      type: Object,
      default: () => ({}),
    },
    equipments: {
      type: Array,
      default: () => [],
    },
    typesDocuments: {
      type: Array,
      default: () => [],
    },
    connectedUserId: {
      type: Number,
      default: null,
    },
  })

  const emit = defineEmits(['created', 'updated', 'close'])

  const formData = ref({
    nom: '',
    equipement_id: null,
    statut_suppose: '',
    commentaire: '',
    documents: [{ document_id: null, nomDocument: '', typeDocument_id: null, file: null }],
  })

  const validationSchema = computed(() => {
    const schema = {
      statut_suppose: ['required'],
    }

    if (!props.isEdit) {
      schema.equipement_id = ['required']
    }

    return schema
  })

  const loading = ref(false)
  const errorMessage = ref('')
  const successMessage = ref('')
  const originalFormData = ref(null)
  const numeroDI = ref('')
  const loadingNumeroDI = ref(false)

  const fetchNumeroDI = async () => {
    if (props.isEdit) {
      numeroDI.value = props.initialData?.nom || ''
      return
    }
    loadingNumeroDI.value = true
    try {
      const apiInstance = useApi(API_BASE_URL)
      const response = await apiInstance.get('demandes-intervention/')
      const count = response?.count ?? (Array.isArray(response) ? response.length : 0)
      numeroDI.value = `DI-${String(count + 1).padStart(4, '0')}`
    } catch {
      numeroDI.value = 'DI-????'
    } finally {
      loadingNumeroDI.value = false
    }
  }

  onMounted(fetchNumeroDI)

  // Initialiser les données
  watch(
    () => props.initialData,
    (newData) => {
      if (newData && Object.keys(newData).length > 0) {
        const initialDocuments = Array.isArray(newData.documents)
          ? newData.documents.map((d) => ({ ...d }))
          : []
        formData.value = {
          nom: newData.nom || '',
          equipement_id: newData.equipement_id || null,
          statut_suppose: newData.statut_suppose,
          commentaire: newData.commentaire || '',
          documents: initialDocuments.length
            ? initialDocuments
            : [{ document_id: null, nomDocument: '', typeDocument_id: null, file: null }],
        }
        // Sauvegarder l'état original pour comparaison
        if (props.isEdit) {
          originalFormData.value = JSON.parse(JSON.stringify(formData.value))
        }
      }
    },
    { immediate: true }
  )

  const close = () => {
    emit('close')
  }

  const validateDocumentsBeforeSubmit = (documents, originalDocuments = []) => {
    const docs = Array.isArray(documents) ? documents : []
    const errors = []

    for (const doc of docs) {
      if (!doc) continue

      const isEmpty = !doc.file && !doc.typeDocument_id && !(doc.nomDocument || '').trim()
      if (isEmpty) continue

      const label = (doc.nomDocument || doc.file?.name || 'Document').toString()

      // Document existant: si on tente une modif, il faut au minimum un type
      if (doc.document_id) {
        const original = Array.isArray(originalDocuments)
          ? originalDocuments.find((o) => o.document_id === doc.document_id)
          : null
        const hasChanges =
          (original && doc.nomDocument !== original.nomDocument) ||
          (original && doc.typeDocument_id !== original.typeDocument_id) ||
          doc.file

        if (hasChanges && !doc.typeDocument_id) {
          errors.push(label)
        }
        continue
      }

      // Nouveau document: fichier + type obligatoires si la ligne n'est pas vide
      if (!doc.file || !doc.typeDocument_id) {
        errors.push(label)
      }
    }

    return errors
  }

  const buildDocumentsMetaAndFiles = (documents) => {
    const docs = Array.isArray(documents) ? documents : []
    const documentsMeta = []
    const files = []

    for (const doc of docs) {
      if (!doc) continue
      if (!doc.file && !doc.typeDocument_id && !(doc.nomDocument || '').trim() && !doc.document_id)
        continue
      documentsMeta.push({
        document_id: doc.document_id || null,
        nomDocument: (doc.nomDocument || doc.file?.name || '').toString(),
        typeDocument_id: doc.typeDocument_id || null,
      })
      files.push(doc.file || null)
    }
    return { documentsMeta, files }
  }

  const haveDocumentsChanged = (payload) => {
    const originalDocs = Array.isArray(originalFormData.value?.documents)
      ? originalFormData.value.documents
      : []
    const currentDocs = Array.isArray(payload?.documents) ? payload.documents : []

    const hasNewDocuments = currentDocs.some((doc) => {
      if (!doc) return false
      const existingId = Number(doc.document_id)
      if (Number.isInteger(existingId) && existingId > 0) return false
      return doc.file || doc.typeDocument_id || (doc.nomDocument || '').trim()
    })
    if (hasNewDocuments) return true

    for (const doc of currentDocs) {
      if (!doc?.document_id) continue
      const original = originalDocs.find((o) => o.document_id === doc.document_id)
      if (!original) continue
      const hasChanges =
        doc.nomDocument !== original.nomDocument ||
        doc.typeDocument_id !== original.typeDocument_id ||
        doc.file
      if (hasChanges) return true
    }
    return false
  }

  const save = async () => {
    loading.value = true
    errorMessage.value = ''
    successMessage.value = ''

    const api = useApi(API_BASE_URL)

    try {
      if (props.isEdit) {
        // Mode édition
        const original = originalFormData.value
        const patch = {}
        if (!original || (formData.value.commentaire ?? '') !== (original.commentaire ?? ''))
          patch.commentaire = formData.value.commentaire || ''
        if (!original || formData.value.statut_suppose !== original.statut_suppose)
          patch.statut_suppose = formData.value.statut_suppose

        const documentsChanged = haveDocumentsChanged(formData.value)
        if (Object.keys(patch).length === 0 && !documentsChanged) {
          successMessage.value = 'Aucune modification à enregistrer'
          loading.value = false
          return
        }

        const docValidationErrors = validateDocumentsBeforeSubmit(
          formData.value.documents,
          originalFormData.value?.documents
        )
        if (docValidationErrors.length) {
          errorMessage.value = `Documents invalides: ${docValidationErrors.join(', ')}`
          loading.value = false
          return
        }

        const form = new FormData()
        if (patch.commentaire !== undefined)
          form.append('commentaire', (patch.commentaire || '').toString())
        if (patch.statut_suppose !== undefined) form.append('statut_suppose', patch.statut_suppose)
        if (documentsChanged) {
          const { documentsMeta, files } = buildDocumentsMetaAndFiles(formData.value.documents)
          form.append('documents', JSON.stringify(documentsMeta))
          files.forEach((file, i) => {
            if (file) form.append(`document_${i}`, file)
          })
        }

        const response = await api.patch(`demandes-intervention/${props.initialData.id}/`, form)

        successMessage.value = "Demande d'intervention modifiée avec succès"
        emit('updated', response)
      } else {
        // Mode création
        if (!props.connectedUserId) {
          errorMessage.value = 'Erreur: Utilisateur non connecté'
          loading.value = false
          return
        }

        const docValidationErrors = validateDocumentsBeforeSubmit(formData.value.documents)
        if (docValidationErrors.length) {
          errorMessage.value = `Documents invalides: ${docValidationErrors.join(', ')}`
          loading.value = false
          return
        }

        const form = new FormData()
        form.append('utilisateur_id', String(props.connectedUserId))
        form.append('equipement_id', String(formData.value.equipement_id))
        form.append('nom', numeroDI.value)
        form.append('commentaire', (formData.value.commentaire || '').toString())
        form.append('statut_suppose', formData.value.statut_suppose)

        const { documentsMeta, files } = buildDocumentsMetaAndFiles(formData.value.documents)
        form.append(
          'documents',
          JSON.stringify(documentsMeta.map(({ document_id: _document_id, ...rest }) => rest))
        )
        files.forEach((file, i) => {
          if (file) form.append(`document_${i}`, file)
        })

        const response = await api.post('demandes-intervention/', form)

        successMessage.value = "Demande d'intervention créée avec succès"
        emit('created', response)
      }

      setTimeout(() => {
        emit('close')
      }, 1500)
    } catch (error) {
      console.error("Erreur lors de l'enregistrement:", error)
      errorMessage.value =
        error.message ||
        "Une erreur est survenue lors de l'enregistrement de la demande d'intervention"
    } finally {
      loading.value = false
    }
  }
</script>
