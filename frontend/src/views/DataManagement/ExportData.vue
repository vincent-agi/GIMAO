<template>
  <v-container fluid>
    <v-card class="elevation-2 rounded-lg pa-6">
      <h1 class="text-h4 font-weight-bold mb-6 text-center text-primary">Export de Données</h1>

      <v-alert
        v-if="errorMessage"
        type="error"
        variant="tonal"
        closable
        class="mb-6 mx-auto"
        @click:close="errorMessage = null"
      >
        {{ errorMessage }}
      </v-alert>

      <v-form ref="exportForm" @submit.prevent="handleExport">
        <v-row>
          <!-- Type d'export -->
          <v-col cols="12" md="6">
            <FormSelect
              v-model="form.exportType"
              field-name="exportType"
              :items="availableExportTypes"
              item-title="label"
              item-value="value"
              label="Type de données à exporter"
              @update:model-value="onExportTypeChange"
            />
          </v-col>

          <!-- Format de fichier -->
          <v-col cols="12" md="6">
            <FormSelect
              v-model="form.fileType"
              field-name="fileType"
              :items="fileTypes"
              item-title="title"
              item-value="value"
              label="Format de fichier"
            />
          </v-col>

          <!-- Inclure les données archivées -->
          <v-col cols="12" md="6">
            <FormSelect
              v-model="form.includeArchived"
              field-name="includeArchived"
              :items="filteredArchiveOptions"
              item-title="label"
              item-value="value"
              label="Données archivées"
              :disabled="isArchiveOptionDisabled"
            />
          </v-col>

          <!-- Filtres conditionnels -->
          <v-col v-if="requiresEquipementId" cols="12" md="6">
            <FormSelect
              v-model="form.equipementId"
              field-name="equipementId"
              :items="equipementList"
              item-title="designation"
              item-value="id"
              :label="equipementIdLabel"
              :loading="isFiltersLoading"
            />
          </v-col>

          <v-col v-if="requiresMagasinId" cols="12" md="6">
            <FormSelect
              v-model="form.magasinId"
              field-name="magasinId"
              :items="magasinList"
              item-title="nom"
              item-value="id"
              :label="magasinIdLabel"
              :loading="isFiltersLoading"
            />
          </v-col>

          <v-col v-if="requiresUtilisateurId" cols="12" md="6">
            <FormSelect
              v-model="form.utilisateurId"
              field-name="utilisateurId"
              :items="utilisateurList"
              item-title="displayName"
              item-value="id"
              :label="utilisateurIdLabel"
              :loading="isFiltersLoading"
            />
          </v-col>

          <v-col v-if="requiresConsoId" cols="12" md="6">
            <FormSelect
              v-model="form.consoId"
              field-name="consoId"
              :items="consoList"
              item-title="designation"
              item-value="id"
              :label="consoIdLabel"
              :loading="isFiltersLoading"
            />
          </v-col>

          <!-- Période d'export (placée à la fin et alignée) -->
          <v-col v-if="requiresDateFilter" cols="12">
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="form.startDate"
                  label="Date de début (Optionnel)"
                  type="date"
                  variant="outlined"
                  color="primary"
                  density="comfortable"
                  clearable
                ></v-text-field>
              </v-col>

              <v-col cols="12" md="6">
                <v-text-field
                  v-model="form.endDate"
                  label="Date de fin (Optionnel)"
                  type="date"
                  variant="outlined"
                  color="primary"
                  density="comfortable"
                  clearable
                ></v-text-field>
              </v-col>
            </v-row>
          </v-col>

          <!-- Colonnes -->
          <v-col cols="12">
            <v-card elevation="1" class="rounded-lg mb-4">
              <v-card-title class="font-weight-bold text-uppercase text-primary text-body-2">
                Champs spécifiques
              </v-card-title>
              <v-divider></v-divider>

              <div class="pa-4">
                <v-alert
                  v-if="!form.exportType"
                  type="info"
                  variant="tonal"
                  density="compact"
                  class="mb-0"
                >
                  Veuillez sélectionner un type de données à exporter pour voir les champs
                  disponibles.
                </v-alert>

                <div v-else-if="isFieldsLoading" class="d-flex justify-center py-4">
                  <v-progress-circular indeterminate color="primary"></v-progress-circular>
                </div>

                <template v-else>
                  <div v-if="availableFields.length > 0">
                    <div class="mb-4 d-flex align-center flex-wrap gap-2">
                      <v-btn
                        size="small"
                        variant="tonal"
                        color="primary"
                        class="mr-2 text-none"
                        @click="form.columns = availableFields.map((f) => f.value)"
                      >
                        Tout sélectionner
                      </v-btn>
                      <v-btn
                        size="small"
                        variant="tonal"
                        color="error"
                        class="text-none"
                        @click="form.columns = []"
                      >
                        Tout désélectionner
                      </v-btn>
                    </div>

                    <v-row dense>
                      <v-col
                        v-for="field in availableFields"
                        :key="field.value"
                        cols="12"
                        sm="6"
                        md="4"
                        lg="3"
                      >
                        <v-checkbox
                          v-model="form.columns"
                          :label="field.label"
                          :value="field.value"
                          hide-details
                          density="compact"
                          color="primary"
                        ></v-checkbox>
                      </v-col>
                    </v-row>
                  </div>

                  <div v-else class="text-caption text-grey text-center py-4">
                    Aucun champ spécifique trouvé pour ce type d'export.
                  </div>
                </template>
              </div>
            </v-card>
          </v-col>
        </v-row>

        <v-row justify="center" class="mt-8 mb-2">
          <v-btn
            color="primary"
            size="large"
            type="submit"
            prepend-icon="mdi-download"
            elevation="2"
            class="px-8 text-none"
          >
            Exporter les données
          </v-btn>
        </v-row>
      </v-form>
    </v-card>
  </v-container>
</template>

<script setup>
  import { ref, reactive, computed, onMounted } from 'vue'
  import { useStore } from 'vuex'
  import { useApi } from '@/composables/useApi'
  import { FormSelect } from '@/components/Forms/inputType'

  const api = useApi()
  const store = useStore()

  const availableFields = ref([])
  const isFieldsLoading = ref(false)
  const isFiltersLoading = ref(false)
  const errorMessage = ref(null)

  const equipementList = ref([])
  const magasinList = ref([])
  const utilisateurList = ref([])
  const consoList = ref([])

  onMounted(async () => {
    isFiltersLoading.value = true
    try {
      const [eqRes, magRes, userRes, consoRes] = await Promise.all([
        api.get('equipements/'),
        api.get('magasins/'),
        api.get('utilisateurs/'),
        api.get('consommables/'),
      ])
      equipementList.value = eqRes?.results || eqRes || []
      magasinList.value = magRes?.results || magRes || []
      const rawUsers = userRes?.results || userRes || []
      utilisateurList.value = rawUsers.map((u) => ({
        ...u,
        displayName: `${u.nomUtilisateur} (${u.prenom} ${u.nomFamille})`,
      }))
      consoList.value = consoRes?.results || consoRes || []
    } catch (error) {
      console.error('Erreur de récupération des dépendances:', error)
    } finally {
      isFiltersLoading.value = false
    }
  })

  const form = reactive({
    exportType: null,
    fileType: 'csv',
    includeArchived: 'no',
    columns: [],
    equipementId: '',
    magasinId: '',
    utilisateurId: '',
    consoId: '',
    startDate: '',
    endDate: '',
  })

  const fileTypes = [
    { title: 'CSV', value: 'csv' },
    { title: 'Excel (XLSX)', value: 'xlsx' },
  ]

  const archivedOptions = [
    { label: 'Uniquement les données actives', value: 'no' },
    { label: 'Uniquement les données archivées', value: 'yes' },
    { label: 'Tout inclure', value: 'both' },
  ]

  const filteredArchiveOptions = computed(() => {
    if (availableFields.value?.some((f) => f.value === 'archive')) {
      return archivedOptions
    }
    return archivedOptions.filter((option) => option.value !== 'both' && option.value !== 'yes')
  })

  const isArchiveOptionDisabled = computed(() => {
    return !availableFields.value?.some((f) => f.value === 'archive')
  })

  const exportTypes = [
    { label: 'Équipements', value: 'equipement', permission: 'export:eq' },
    { label: 'Statuts des équipements', value: 'statut_equipement', permission: 'export:eqstatus' },
    { label: 'Bons de travail', value: 'bt', permission: 'export:bt' },
    { label: "Demandes d'intervention", value: 'di', permission: 'export:di' },
    { label: 'Consommables', value: 'conso', permission: 'export:cons' },
    {
      label: "Historique d'achat des consommables",
      value: 'historique_achat_conso',
      permission: 'export:histcons',
    },
    { label: 'Stocks en magasin', value: 'stock', permission: 'export:stockmag' },
    { label: 'Magasins', value: 'magasins', permission: 'export:mag' },
    {
      label: 'Historique de sortie des magasins',
      value: 'historique_sortie_magasin',
      permission: 'export:histmag',
    },
    { label: 'Logs système', value: 'logs', permission: 'export:logs' },
    { label: 'Fournisseurs', value: 'fournisseur', permission: 'export:sup' },
    { label: 'Fabricants', value: 'fabricant', permission: 'export:man' },
    { label: "Modèles d'équipements", value: 'modele_equipement', permission: 'export:eqmod' },
    { label: 'Lieux', value: 'lieu', permission: 'export:lieu' },
    { label: 'Compteurs numériques', value: 'compteur', permission: 'export:cp' },
    { label: 'Seuils de compteurs', value: 'seuils_compteur', permission: 'export:seuils' },
    { label: 'Périodicités', value: 'periodicites', permission: 'export:periodicites' },
    { label: 'Utilisateurs', value: 'users', permission: 'export:user' },
  ]

  const availableExportTypes = computed(() => {
    return exportTypes.filter((type) => store.getters.hasPermission(type.permission))
  })

  const requiresEquipementId = computed(() => {
    const types = ['statut_equipement', 'bt', 'di', 'compteur', 'seuils_compteur', 'periodicites']
    return types.includes(form.exportType)
  })

  const requiresDateFilter = computed(() => {
    const types = [
      'statut_equipement',
      'bt',
      'di',
      'historique_achat_conso',
      'historique_sortie_magasin',
      'logs',
      'periodicites',
    ]
    return types.includes(form.exportType)
  })

  const requiresMagasinId = computed(() => {
    const types = ['stock', 'historique_sortie_magasin']
    return types.includes(form.exportType)
  })

  const requiresUtilisateurId = computed(() => {
    const types = ['logs']
    return types.includes(form.exportType)
  })

  const requiresConsoId = computed(() => {
    const types = ['historique_achat_conso']
    return types.includes(form.exportType)
  })

  const selectedLabel = computed(() => {
    const found = exportTypes.find((t) => t.value === form.exportType)
    return found ? found.label : ''
  })

  const equipementIdLabel = computed(
    () => `ID de l'Équipement (Optionnel) - selectionne un ${selectedLabel.value}`
  )

  const magasinIdLabel = computed(
    () => `ID du Magasin (Optionnel) - selectionne un ${selectedLabel.value}`
  )

  const utilisateurIdLabel = computed(
    () => `ID de l'Utilisateur (Optionnel) - selectionne un ${selectedLabel.value}`
  )

  const consoIdLabel = computed(
    () => `ID du Consommable (Optionnel) - selectionne un ${selectedLabel.value}`
  )

  const onExportTypeChange = async () => {
    // Reset columns when type changes
    form.columns = []

    if (!form.exportType) {
      availableFields.value = []
      return
    }

    isFieldsLoading.value = true
    try {
      const response = await api.get('export/fields/', { exportType: form.exportType })
      console.log(response)
      if (response && response.fields) {
        availableFields.value = response.fields
        form.columns = response.fields.map((field) => field.value)
      } else {
        availableFields.value = []
        form.columns = []
      }
    } catch (error) {
      console.error('Erreur de la récupération des champs: ', error)
      availableFields.value = []
      form.columns = []
    } finally {
      isFieldsLoading.value = false
    }
  }

  const handleExport = async () => {
    errorMessage.value = null // reset
    if (!form.exportType) {
      errorMessage.value = 'Veuillez sélectionner un type de données à exporter.'
      return
    }

    const params = {}
    params.exportType = form.exportType
    params.fileType = form.fileType
    params.includeArchived = form.includeArchived

    if (form.columns && form.columns.length > 0) {
      params.columns = form.columns.join(',')
    }

    if (requiresEquipementId.value && form.equipementId) {
      params.equipementId = form.equipementId
    }
    if (requiresMagasinId.value && form.magasinId) {
      params.magasinId = form.magasinId
    }
    if (requiresUtilisateurId.value && form.utilisateurId) {
      params.utilisateurId = form.utilisateurId
    }
    if (requiresConsoId.value && form.consoId) {
      params.consoId = form.consoId
    }

    if (requiresDateFilter.value) {
      if (form.startDate) params.startDate = form.startDate
      if (form.endDate) params.endDate = form.endDate
    }

    try {
      const response = await api.getRaw('export/', params, { responseType: 'blob' })

      let filename = `${form.exportType}.${form.fileType}`
      const disposition = response.headers['content-disposition']
      if (disposition && disposition.indexOf('attachment') !== -1) {
        const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/
        const matches = filenameRegex.exec(disposition)
        if (matches != null && matches[1]) {
          filename = matches[1].replace(/['"]/g, '')
        }
      }

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error("Erreur d'export :", error)
      if (error.response && error.response.data instanceof Blob) {
        try {
          const textData = await error.response.data.text()
          const errJson = JSON.parse(textData)
          if (errJson.error) {
            errorMessage.value = errJson.error
            return
          }
        } catch (e) {
          console.error("Impossible de lire l'erreur Blob", e)
        }
      } else if (error.response && error.response.data && error.response.data.error) {
        errorMessage.value = error.response.data.error
        return
      }
      errorMessage.value = "Une erreur s'est produite lors de l'exportation des données."
    }
  }
</script>

<style scoped>
  .text-primary {
    color: #05004e;
  }
</style>
