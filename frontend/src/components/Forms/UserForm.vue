<template>
  <BaseForm
    v-model="formData"
    :title="title"
    :loading="loading"
    :validation-schema="validationSchema"
    :error-message="errorMessage"
    :success-message="successMessage"
    :submit-button-text="submitButtonText"
    :submit-button-color="submitButtonColor"
    :handle-submit="save"
    :custom-cancel-action="close"
    actions-container-class="d-flex justify-end gap-2 mt-2"
    submit-button-class="mt-2"
    cancel-button-class="mt-2 mr-3"
  >
    <template #default>
      <!-- Photo de profil -->
      <v-sheet class="pa-4 mb-4" elevation="1" rounded>
        <h4 class="mb-3">Photo de profil</h4>
        <ProfilPicForm
          ref="profilPicFormRef"
          v-model="formData.photoProfil"
          :existing-photo-path="existingPhotoPath"
          @delete-existing="onDeleteExistingPhoto"
        />
      </v-sheet>

      <!-- Informations -->
      <v-sheet class="pa-4 mb-4" elevation="1" rounded>
        <h4 class="mb-3">Informations</h4>
        <v-row dense>
          <v-col cols="12" md="6">
            <FormField
              v-model="formData.nomUtilisateur"
              field-name="nomUtilisateur"
              label="Nom d'utilisateur"
              placeholder="jdupont, marie.martin..."
            />
          </v-col>

          <v-col cols="12" md="6">
            <FormField
              v-model="formData.email"
              field-name="email"
              label="Email"
              type="email"
              placeholder="utilisateur@exemple.com"
            />
          </v-col>

          <v-col cols="12" md="6">
            <FormField
              v-model="formData.prenom"
              field-name="prenom"
              label="Prénom"
              placeholder="Marie, Jean..."
            />
          </v-col>

          <v-col cols="12" md="6">
            <FormField
              v-model="formData.nomFamille"
              field-name="nomFamille"
              label="Nom de famille"
              placeholder="Dupont, Martin..."
            />
          </v-col>

          <v-col cols="12" md="6">
            <FormSelect
              v-model="formData.role"
              field-name="role"
              label="Rôle"
              :items="roleOptions"
              item-title="label"
              item-value="value"
              placeholder="Sélectionner un rôle"
              :disabled="isEditingSelf"
              :hint="isEditingSelf ? 'Vous ne pouvez pas modifier votre propre rôle' : ''"
              :persistent-hint="isEditingSelf"
            />
          </v-col>

          <v-col cols="12" md="6" class="d-flex align-center">
            <FormCheckbox
              v-model="formData.actif"
              field-name="actif"
              label="Compte actif"
              :disabled="isEditingSelf"
              :hint="isEditingSelf ? 'Vous ne pouvez pas désactiver votre propre compte' : ''"
              :persistent-hint="isEditingSelf"
            />
          </v-col>
        </v-row>
      </v-sheet>

      <!-- Mot de passe (mode édition uniquement) -->
      <v-sheet v-if="isEdit" class="pa-4 mb-4" elevation="1" rounded>
        <h4 class="mb-3">Modifier le mot de passe</h4>
        <p class="text-body-2 text-medium-emphasis mb-4">
          Remplissez les champs ci-dessous uniquement si vous souhaitez modifier le mot de passe. Si
          l'utilisateur n'a jamais eu de mot de passe, laissez le champ "Ancien mot de passe" vide.
        </p>
        <v-row dense>
          <v-col v-if="isEditingSelf" cols="12" md="4">
            <FormField
              v-model="passwordForm.ancien"
              field-name="ancien"
              label="Ancien mot de passe"
              type="password"
              placeholder="••••••••"
            />
          </v-col>
          <v-col cols="12" :md="isEditingSelf ? 4 : 6">
            <FormField
              v-model="passwordForm.nouveau"
              field-name="nouveau"
              label="Nouveau mot de passe"
              type="password"
              placeholder="••••••••"
              :rules="nouveauMotDePasseRules"
            />
          </v-col>
          <v-col cols="12" :md="isEditingSelf ? 4 : 6">
            <FormField
              v-model="passwordForm.confirmation"
              field-name="confirmation"
              label="Confirmer le mot de passe"
              type="password"
              placeholder="••••••••"
              :rules="confirmationMotDePasseRules"
            />
          </v-col>
        </v-row>
      </v-sheet>
    </template>
  </BaseForm>
</template>

<script setup>
  import { computed, ref, watch } from 'vue'
  import BaseForm from '@/components/common/BaseForm.vue'
  import FormField from '@/components/Forms/inputType/FormField.vue'
  import FormSelect from '@/components/Forms/inputType/FormSelect.vue'
  import FormCheckbox from '@/components/Forms/inputType/FormCheckbox.vue'
  import ProfilPicForm from '@/components/Forms/ProfilPicForm.vue'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'
  import { getUserCreateErrorMessage } from '@/utils/drfErrors'

  const props = defineProps({
    title: {
      type: String,
      default: 'Utilisateur',
    },
    submitButtonText: {
      type: String,
      default: 'Enregistrer',
    },
    submitButtonColor: {
      type: String,
      default: 'primary',
    },
    isEdit: {
      type: Boolean,
      default: false,
    },
    userId: {
      type: [String, Number],
      default: null,
    },
    initialData: {
      type: Object,
      default: () => ({}),
    },
    roles: {
      type: Array,
      default: () => [],
    },
    currentUserId: {
      type: [String, Number],
      default: null,
    },
  })

  const emit = defineEmits(['created', 'updated', 'close', 'user-sync'])

  const api = useApi(API_BASE_URL)

  const profilPicFormRef = ref(null)
  const loading = ref(false)
  const isChangingPassword = ref(false)
  const errorMessage = ref('')
  const successMessage = ref('')

  const formData = ref({
    nomUtilisateur: '',
    prenom: '',
    nomFamille: '',
    email: '',
    actif: true,
    role: null,
    photoProfil: null,
  })

  const passwordForm = ref({
    ancien: '',
    nouveau: '',
    confirmation: '',
  })

  const originalFormData = ref(null)
  const existingPhotoPath = ref('')
  const originalPhotoPath = ref('')
  const removeExistingPhoto = ref(false)

  // Options de rôles formatées
  const roleOptions = computed(() =>
    (props.roles || []).map((r) => ({
      label: r.nomRole,
      value: r.id,
    }))
  )

  // Détecte si l'utilisateur modifie son propre compte
  const isEditingSelf = computed(() => {
    if (!props.isEdit || !props.userId || !props.currentUserId) return false
    return String(props.userId) === String(props.currentUserId)
  })

  // Schéma de validation
  const validationSchema = {
    nomUtilisateur: ['required', { name: 'minLength', params: [2] }],
    prenom: ['required', { name: 'minLength', params: [2] }],
    nomFamille: ['required', { name: 'minLength', params: [2] }],
    email: ['required', 'email'],
    role: ['required'],
  }

  // Règles de validation pour les champs mot de passe (hors schéma)
  const nouveauMotDePasseRules = [(v) => !v || v.length >= 8 || '8 caractères minimum']

  const confirmationMotDePasseRules = [
    (v) =>
      !passwordForm.value.nouveau ||
      v === passwordForm.value.nouveau ||
      'Les mots de passe ne correspondent pas',
  ]

  // Initialisation des données
  watch(
    () => props.initialData,
    (newData) => {
      if (newData && Object.keys(newData).length > 0) {
        formData.value = {
          nomUtilisateur: newData.nomUtilisateur || '',
          prenom: newData.prenom || '',
          nomFamille: newData.nomFamille || '',
          email: newData.email || '',
          actif: newData.actif !== undefined ? !!newData.actif : true,
          role: newData.role_id || newData.role || null,
          photoProfil: null,
        }
        existingPhotoPath.value = newData.photoProfil || ''
        originalPhotoPath.value = newData.photoProfil || ''
        removeExistingPhoto.value = false

        if (props.isEdit) {
          originalFormData.value = JSON.parse(JSON.stringify(formData.value))
        }
      }
    },
    { immediate: true, deep: true }
  )

  // Gestion suppression photo existante
  const onDeleteExistingPhoto = () => {
    removeExistingPhoto.value = true
    existingPhotoPath.value = ''
  }

  // Fermer le formulaire
  const close = () => {
    emit('close')
  }

  // Détection des changements (mode édition)
  const hasChanges = () => {
    if (!props.isEdit || !originalFormData.value) return true

    const normalizeString = (v) => (typeof v === 'string' ? v.trim() : v)

    const fieldsChanged = ['nomUtilisateur', 'prenom', 'nomFamille', 'email'].some(
      (key) =>
        normalizeString(formData.value?.[key]) !== normalizeString(originalFormData.value?.[key])
    )

    const activeChanged = !!formData.value.actif !== !!originalFormData.value.actif
    const roleChanged =
      String(formData.value.role ?? '') !== String(originalFormData.value.role ?? '')

    const photoChanged =
      formData.value.photoProfil instanceof File ||
      (removeExistingPhoto.value && !!originalPhotoPath.value)

    return fieldsChanged || activeChanged || roleChanged || photoChanged
  }

  // Sauvegarde
  const save = async () => {
    loading.value = true
    errorMessage.value = ''
    successMessage.value = ''

    // Vérification des changements en mode édition
    const passwordFilled = !!(passwordForm.value.nouveau && passwordForm.value.confirmation)
    if (props.isEdit && !hasChanges() && !passwordFilled) {
      loading.value = false
      errorMessage.value = 'Aucune modification détectée.'
      return
    }

    try {
      const payloadHasFile = formData.value.photoProfil instanceof File
      const payload = payloadHasFile ? new FormData() : {}

      const setField = (key, value) => {
        if (payload instanceof FormData) {
          payload.append(key, value)
        } else {
          payload[key] = value
        }
      }

      setField('nomUtilisateur', formData.value.nomUtilisateur)
      setField('prenom', formData.value.prenom)
      setField('nomFamille', formData.value.nomFamille)
      setField('email', formData.value.email)
      setField('actif', String(!!formData.value.actif))

      // Clé différente selon mode création/édition
      if (props.isEdit) {
        setField('role_id', String(formData.value.role))
      } else {
        setField('role', String(formData.value.role))
      }

      if (payloadHasFile) {
        payload.append('photoProfil', formData.value.photoProfil)
      } else if (props.isEdit && removeExistingPhoto.value) {
        setField('photoProfil', null)
      }

      if (props.isEdit) {
        const updatedUser = await api.put(`utilisateurs/${props.userId}/`, payload)
        emit('user-sync', updatedUser)
        successMessage.value = 'Utilisateur modifié avec succès.'

        // Mise à jour du mot de passe si les champs sont remplis
        if (passwordForm.value.nouveau && passwordForm.value.confirmation) {
          await handlePasswordUpdate()
        }

        setTimeout(() => {
          emit('updated', updatedUser)
        }, 800)
      } else {
        const created = await api.post('utilisateurs/', payload)
        successMessage.value = 'Utilisateur créé avec succès.'
        setTimeout(() => {
          emit('created', created)
        }, 800)
      }
    } catch (e) {
      console.error('Error saving user:', e)
      errorMessage.value = props.isEdit
        ? "Erreur lors de la modification de l'utilisateur."
        : getUserCreateErrorMessage(e)
    } finally {
      loading.value = false
    }
  }

  // Mise à jour du mot de passe
  const handlePasswordUpdate = async () => {
    if (!props.userId) {
      errorMessage.value = 'Impossible de modifier le mot de passe : id manquant.'
      return
    }

    errorMessage.value = ''
    successMessage.value = ''

    const ancien = passwordForm.value.ancien
    const nouveau = passwordForm.value.nouveau
    const confirmation = passwordForm.value.confirmation

    const anyPasswordFieldFilled = !!(ancien || nouveau || confirmation)
    if (!anyPasswordFieldFilled) {
      errorMessage.value = 'Veuillez renseigner au moins le nouveau mot de passe.'
      return
    }

    if (!nouveau || nouveau.length < 8) {
      errorMessage.value = 'Le nouveau mot de passe doit contenir au moins 8 caractères.'
      return
    }

    if (!confirmation) {
      errorMessage.value = 'La confirmation du nouveau mot de passe est requise.'
      return
    }

    if (nouveau !== confirmation) {
      errorMessage.value = 'Les mots de passe ne correspondent pas.'
      return
    }

    isChangingPassword.value = true
    try {
      if (!isEditingSelf.value) {
        // Le responsable modifie un autre utilisateur — pas besoin de l'ancien mot de passe
        await api.post(`utilisateurs/${props.userId}/changer_mot_de_passe/`, {
          ancien_motDePasse: '',
          nouveau_motDePasse: nouveau,
          nouveau_motDePasse_confirmation: confirmation,
        })
        successMessage.value = 'Mot de passe mis à jour avec succès.'
      } else if (ancien && ancien.trim() !== '') {
        await api.post(`utilisateurs/${props.userId}/changer_mot_de_passe/`, {
          ancien_motDePasse: ancien,
          nouveau_motDePasse: nouveau,
          nouveau_motDePasse_confirmation: confirmation,
        })
        successMessage.value = 'Mot de passe mis à jour avec succès.'
      } else {
        if (!formData.value.nomUtilisateur) {
          errorMessage.value = "Nom d'utilisateur manquant : impossible de définir un mot de passe."
          return
        }
        await api.post('utilisateurs/definir_mot_de_passe/', {
          nomUtilisateur: formData.value.nomUtilisateur,
          nouveau_motDePasse: nouveau,
          nouveau_motDePasse_confirmation: confirmation,
        })
        successMessage.value = 'Mot de passe défini avec succès.'
      }

      passwordForm.value = { ancien: '', nouveau: '', confirmation: '' }
    } catch (e) {
      const detail = e?.response?.data?.detail
      if (typeof detail === 'string' && detail.trim() !== '') {
        errorMessage.value = detail
      } else {
        errorMessage.value = 'Erreur lors de la mise à jour du mot de passe.'
      }
    } finally {
      isChangingPassword.value = false
    }
  }
</script>
