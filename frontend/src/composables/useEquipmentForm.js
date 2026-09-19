import { computed, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { useApi } from '@/composables/useApi'
import { API_BASE_URL, MEDIA_BASE_URL } from '@/utils/constants'
import { EQUIPMENT_STATUS } from '@/utils/constants.js'

export function useEquipmentForm(isEditMode = false) {
  const router = useRouter()
  const store = useStore()
  const api = useApi(API_BASE_URL)

  const loading = ref(false)
  const loadingData = ref(false)
  const errorMessage = ref('')
  const successMessage = ref('')
  const editingCounterIndex = ref(-1)
  const isCounterEditMode = ref(false)

  const getCurrentUserId = () => {
    const currentUser = store.getters.currentUser
    if (currentUser?.id) return currentUser.id

    const userFromStorage = localStorage.getItem('user')
    if (userFromStorage) {
      try {
        const userData = JSON.parse(userFromStorage)
        return userData.id
      } catch (e) {
        console.error('Error parsing user from localStorage:', e)
      }
    }

    console.error('Aucun utilisateur connecté trouvé')
    return null
  }

  const ORDINAL_EPOCH = 719162 // 1970-01-01

  const todayToOrdinal = () => {
    const now = new Date()
    const msPerDay = 1000 * 60 * 60 * 24
    const daysSinceEpoch = Math.floor(
      (Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()) - Date.UTC(1970, 0, 1)) /
        msPerDay
    )
    return daysSinceEpoch + ORDINAL_EPOCH
  }

  // Ce compteur "cache" sert d'ancre pour les plans calendaires :
  // l'utilisateur ne le gere pas comme un compteur metier, mais le backend
  // a besoin d'une valeur date stable pour calculer les echeances.
  const createDefaultCalendarCounter = () => ({
    id: null,
    nomCompteur: 'Calendrier',
    valeurCourante: todayToOrdinal(),
    unite: 'date',
    estPrincipal: false,
    type: 'Calendaire',
    isDefaultCalendar: true,
  })

  const formData = ref({
    numSerie: '',
    reference: '',
    designation: '',
    type: null,
    dateMiseEnService: '',
    prixAchat: null,
    lienImageEquipement: null,
    modeleEquipement: null,
    fournisseur: null,
    fabricant: null,
    famille: null,
    lieu: null,
    statut: null,
    consommables: [],
    compteurs: isEditMode ? [] : [createDefaultCalendarCounter()],
    plansMaintenance: [],
    createurEquipement: getCurrentUserId(),
  })

  const initialData = ref(null)

  const locations = ref([])
  const equipmentModels = ref([])
  const fournisseurs = ref([])
  const fabricants = ref([])
  const consumables = ref([])
  const familles = ref([])
  const typesPM = ref([])
  const typesDocuments = ref([])
  const equipmentModelsLoading = ref(false)
  const fournisseursLoading = ref(false)
  const fabricantsLoading = ref(false)
  const consumablesLoading = ref(false)

  const showCounterDialog = ref(false)
  const showFabricantDialog = ref(false)
  const showFournisseurDialog = ref(false)
  const showModeleDialog = ref(false)
  const showFamilleDialog = ref(false)

  const existingPMs = ref([])
  const sectionSearchTimeouts = new Map()

  const generateTempPmId = () => `pm_${Date.now()}_${Math.random().toString(16).slice(2)}`

  // Stocke un "plan de maintenance" en tampon pour pouvoir le re-sélectionner
  // lors de l'ajout d'un nouveau seuil (dans le flow de création).
  const upsertExistingPM = (planData) => {
    const nom = planData?.nom?.trim()
    if (!nom) return

    const normalized = {
      id: planData?.id ?? generateTempPmId(),
      nom,
      type_id: planData?.type_id ?? null,
      description: planData?.description ?? '',
      necessiteHabilitationElectrique: !!planData?.necessiteHabilitationElectrique,
      necessitePermisFeu: !!planData?.necessitePermisFeu,
      consommables: Array.isArray(planData?.consommables)
        ? planData.consommables.map((c) => ({ ...c }))
        : [],
      documents: Array.isArray(planData?.documents)
        ? planData.documents.map((d) => ({ ...d }))
        : [],
    }

    const existingIndex = existingPMs.value.findIndex((pm) => pm.nom === nom)

    if (existingIndex >= 0) {
      const prev = existingPMs.value[existingIndex]
      existingPMs.value[existingIndex] = {
        ...prev,
        ...normalized,
        id: prev?.id ?? normalized.id,
      }
    } else {
      existingPMs.value.push(normalized)
    }
  }

  const equipmentStatuses = computed(() => {
    return Object.entries(EQUIPMENT_STATUS).map(([value, label]) => ({
      value,
      label,
    }))
  })

  const getEmptyCounter = () => ({
    id: null,
    nomCompteur: '',
    valeurCourante: null,
    unite: 'date',
    estPrincipal: false,
    type: 'Calendaire',
    isDefaultCalendar: false,
  })
  const currentCounter = ref(getEmptyCounter())

  const getEmptyPlan = () => ({
    id: null,
    nom: '',
    type_id: null,
    description: '',
    compteurIndex: null,
    consommables: [],
    documents: [],
    necessiteHabilitationElectrique: false,
    necessitePermisFeu: false,
    seuil: {
      estGlissant: false,
      derniereIntervention: null,
      ecartInterventions: null,
      prochaineMaintenance: null,
      uniteCalendaire: 'Jours',
      ecartCalendaire: 1,
    },
  })
  const currentPlan = ref(getEmptyPlan())
  const isPlanEditMode = ref(false)
  const editingPlanIndex = ref(-1)
  const showPlanDialog = ref(false)

  const validateForm = () => {
    const requiredFields = [
      'numSerie',
      'reference',
      'designation',
      'modeleEquipement',
      'lieu',
      'statut',
    ]
    let isValid = true

    requiredFields.forEach((field) => {
      if (!formData.value[field]) {
        isValid = false
      }
    })

    if (isEditMode) {
      const compteursSansId = formData.value.compteurs.filter((c) => !c.id)
      if (compteursSansId.length > 0) {
        errorMessage.value = `Les compteurs suivants n'ont pas d'ID: ${compteursSansId.map((c) => c.nom).join(', ')}`
        isValid = false
      }
    }

    return isValid
  }

  const handleFileUpload = (file) => {
    formData.value.lienImageEquipement = file
  }

  const mergeUniqueById = (currentItems, nextItems) => {
    const merged = new Map()

    for (const item of currentItems || []) {
      if (item?.id !== undefined && item?.id !== null) {
        merged.set(item.id, item)
      }
    }

    for (const item of nextItems || []) {
      if (item?.id !== undefined && item?.id !== null) {
        merged.set(item.id, item)
      }
    }

    return Array.from(merged.values())
  }

  const fetchFormDataSection = async (section, { search = '', ids = [] } = {}) => {
    const params = {
      section,
      page: 1,
      page_size: 25,
    }

    if (search?.trim()) {
      params.search = search.trim()
    }

    if (Array.isArray(ids) && ids.length > 0) {
      params.ids = ids.join(',')
    }

    return api.get('equipements/form-data/', params)
  }

  const sectionConfigs = {
    equipmentModels: {
      target: equipmentModels,
      loading: equipmentModelsLoading,
    },
    fournisseurs: {
      target: fournisseurs,
      loading: fournisseursLoading,
    },
    fabricants: {
      target: fabricants,
      loading: fabricantsLoading,
    },
    consumables: {
      target: consumables,
      loading: consumablesLoading,
    },
  }

  const loadSectionOptions = async (section, options = {}) => {
    const config = sectionConfigs[section]
    if (!config) return

    config.loading.value = true

    try {
      const response = await fetchFormDataSection(section, options)
      const nextItems = Array.isArray(response?.results)
        ? response.results
        : Array.isArray(response)
          ? response
          : []

      if (options.ids?.length) {
        // En mode edition, une valeur selectionnee peut ne pas appartenir
        // a la premiere page chargee. On la fusionne au lieu d'ecraser la liste.
        config.target.value = mergeUniqueById(config.target.value, nextItems)
      } else {
        config.target.value = nextItems
      }
    } finally {
      config.loading.value = false
    }
  }

  const searchSectionOptions = (section, search) => {
    const previousTimeout = sectionSearchTimeouts.get(section)
    if (previousTimeout) {
      clearTimeout(previousTimeout)
    }

    const timeoutId = setTimeout(() => {
      loadSectionOptions(section, { search }).catch((error) => {
        console.error(`Erreur lors du chargement de ${section}:`, error)
      })
    }, 300)

    sectionSearchTimeouts.set(section, timeoutId)
  }

  const ensureSelectedOptions = async () => {
    // Le formulaire ne charge qu'un sous-ensemble des options au depart.
    // On recharge explicitement les valeurs deja choisies pour que les selects
    // puissent afficher un libelle correct meme si l'option n'est pas dans la page courante.
    const requests = []

    if (formData.value.modeleEquipement) {
      requests.push(
        loadSectionOptions('equipmentModels', { ids: [formData.value.modeleEquipement] })
      )
    }

    if (formData.value.fournisseur) {
      requests.push(loadSectionOptions('fournisseurs', { ids: [formData.value.fournisseur] }))
    }

    if (formData.value.fabricant) {
      requests.push(loadSectionOptions('fabricants', { ids: [formData.value.fabricant] }))
    }

    if (Array.isArray(formData.value.consommables) && formData.value.consommables.length > 0) {
      requests.push(loadSectionOptions('consumables', { ids: formData.value.consommables }))
    }

    if (requests.length > 0) {
      await Promise.all(requests)
    }
  }

  const fetchData = async () => {
    loadingData.value = true
    errorMessage.value = ''

    try {
      // "minimal" evite de charger toutes les grosses listes au premier rendu ;
      // les options volumineuses sont ensuite chargees section par section.
      const data = await api.get('equipements/form-data/', { minimal: true })

      locations.value = data.locations
      familles.value = data.familles
      typesPM.value = data.typesPM
        .filter(
          (item) =>
            item.libelle === 'Préventive conditionnelle' ||
            item.libelle === 'Préventive systématique'
        )
        .map((item) => ({
          id: item.id,
          libelle: item.libelle,
        }))
      typesDocuments.value = data.typesDocuments

      await Promise.all([
        loadSectionOptions('equipmentModels'),
        loadSectionOptions('fournisseurs'),
        loadSectionOptions('fabricants'),
        loadSectionOptions('consumables'),
      ])
    } catch (error) {
      console.error('Erreur lors du chargement des données:', error)
      errorMessage.value = 'Erreur lors du chargement des données. Veuillez réessayer.'
    } finally {
      loadingData.value = false
    }
  }

  const fetchEquipment = async (equipmentId) => {
    if (!equipmentId) return

    try {
      loadingData.value = true
      errorMessage.value = ''
      const res = await api.get(`equipement/${equipmentId}/affichage/`)
      const eq = res

      // Formater la date de mise en service pour l'input type="date" (format YYYY-MM-DD)
      let formattedDate = ''
      if (eq.dateMiseEnService) {
        const date = new Date(eq.dateMiseEnService)
        if (!isNaN(date.getTime())) {
          formattedDate = date.toISOString().split('T')[0]
        }
      }

      const equipmentData = {
        numSerie: eq.numSerie || '',
        reference: eq.reference || '',
        designation: eq.designation || '',
        type: eq.type || null,
        dateMiseEnService: formattedDate,
        prixAchat: eq.prixAchat || null,
        lienImageEquipement: eq.lienImage ? MEDIA_BASE_URL + eq.lienImage : null,
        modeleEquipement: eq.modele?.id || null,
        fournisseur: eq.fournisseur?.id || null,
        fabricant: eq.fabricant?.id || null,
        famille: eq.famille?.id || null,
        lieu: eq.lieu?.id || eq.lieu || null,
        statut: eq.dernier_statut?.statut || null,
        consommables: eq.consommables?.map((c) => c.id) || [],
        compteurs: eq.compteurs || [],
      }

      initialData.value = JSON.parse(JSON.stringify(equipmentData))
      formData.value = equipmentData
      await ensureSelectedOptions()
    } catch (e) {
      console.error('Erreur détaillée fetchEquipment:', e)
      console.error('Response:', e.response?.data)
      console.error('Status:', e.response?.status)
      errorMessage.value =
        "Erreur lors du chargement de l'équipement: " + (e.response?.data?.detail || e.message)
    } finally {
      loadingData.value = false
    }
  }

  const fetchDocs = async () => {
    try {
      // Ne rien faire si pas de compteurs
      if (!formData.value.compteurs || formData.value.compteurs.length === 0) {
        return
      }

      const fetchPromises = []

      formData.value.compteurs.forEach((counter) => {
        if (counter.planMaintenance && counter.planMaintenance.documents) {
          counter.planMaintenance.documents.forEach((doc) => {
            if (doc.path) {
              const promise = fetch(MEDIA_BASE_URL + doc.path)
                .then((res) => res.blob())
                .then((blob) => {
                  const filename = doc.titre || 'document'
                  const file = new File([blob], filename, { type: blob.type })
                  doc.file = file
                  return file
                })
                .catch((err) => {
                  console.error(`Erreur pour ${doc.path}:`, err)
                })

              fetchPromises.push(promise)
            }
          })
        }
      })

      await Promise.all(fetchPromises)
    } catch (error) {
      console.error('Erreur lors du chargement des documents:', error)
    }
  }

  const handleCounterAdd = () => {
    editingCounterIndex.value = -1
    isCounterEditMode.value = false
    currentCounter.value = getEmptyCounter()
    showCounterDialog.value = true
  }

  const handleCounterEdit = (counter) => {
    editingCounterIndex.value = formData.value.compteurs.indexOf(counter)
    isCounterEditMode.value = true

    currentCounter.value = {
      ...counter,
      planMaintenance: {
        ...counter.planMaintenance,
        consommables: counter.planMaintenance?.consommables
          ? counter.planMaintenance.consommables.map((c) => ({ ...c }))
          : [],
        documents: counter.planMaintenance?.documents
          ? counter.planMaintenance.documents.map((d) => ({ ...d }))
          : [],
      },
    }

    showCounterDialog.value = true
  }

  const handleCounterDelete = (counter) => {
    if (counter?.isDefaultCalendar) {
      return
    }
    if (confirm('Êtes-vous sûr de vouloir supprimer ce compteur ?')) {
      formData.value.compteurs = formData.value.compteurs.filter((c) => c !== counter)
    }
  }

  const dateToOrdinal = (dateStr) => {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return null

    // Nombre de jours depuis 1970-01-01 en UTC
    const msPerDay = 1000 * 60 * 60 * 24
    const daysSinceEpoch = Math.floor(
      (Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()) -
        Date.UTC(1970, 0, 1)) /
        msPerDay
    )

    return daysSinceEpoch + ORDINAL_EPOCH
  }

  const ordinalToDate = (ordinal) => {
    const msPerDay = 1000 * 60 * 60 * 24
    const date = new Date((ordinal - ORDINAL_EPOCH) * msPerDay)
    return date.toISOString().split('T')[0]
  }

  // [CODE MORT — OBSOLÈTE]
  // Utilisée uniquement par l'ancienne étape "Compteurs" du wizard de création
  // d'équipement, retirée depuis le passage à 3 étapes. Plus appelée en pratique.
  // NB : forçait tout compteur Calendaire en Numérique (un seul compteur calendaire
  // par défaut à l'époque). Conservée pour référence.
  const saveCurrentCounter = () => {
    const normalizedCounter = {
      ...currentCounter.value,
      isDefaultCalendar: false,
      type:
        currentCounter.value?.type === 'Calendaire'
          ? 'Numérique'
          : currentCounter.value?.type || 'Numérique',
    }

    if (normalizedCounter.type !== 'Calendaire' && !normalizedCounter.unite) {
      normalizedCounter.unite = 'heures'
    }

    if (editingCounterIndex.value >= 0) {
      // Mode édition
      formData.value.compteurs[editingCounterIndex.value] = { ...normalizedCounter }
      // Le formulaire manipule une date lisible, mais l'API attend un ordinal
      // pour les compteurs calendaires historiques.
      formData.value.compteurs[editingCounterIndex.value].type === 'Calendaire'
        ? (formData.value.compteurs[editingCounterIndex.value].valeurCourante = dateToOrdinal(
            normalizedCounter.valeurCourante
          ))
        : (formData.value.compteurs[editingCounterIndex.value].valeurCourante =
            normalizedCounter.valeurCourante)
    } else {
      // Mode ajout
      formData.value.compteurs.push({ ...normalizedCounter })
      formData.value.compteurs[formData.value.compteurs.length - 1].type === 'Calendaire'
        ? (formData.value.compteurs[formData.value.compteurs.length - 1].valeurCourante =
            dateToOrdinal(normalizedCounter.valeurCourante))
        : (formData.value.compteurs[formData.value.compteurs.length - 1].valeurCourante =
            normalizedCounter.valeurCourante)
    }
    closeCounterDialog()
  }

  const handlePlanAdd = () => {
    editingPlanIndex.value = -1
    isPlanEditMode.value = false
    currentPlan.value = getEmptyPlan()
    // Ne pas pré-sélectionner de compteur ici : c'est l'appelant
    // (openPeriodicMaintenanceDialog ou openPreventiveMaintenanceDialog)
    // qui choisit le bon compteur selon le filtre actif.
    showPlanDialog.value = true
  }

  const handlePlanEdit = (plan) => {
    editingPlanIndex.value = formData.value.plansMaintenance.indexOf(plan)
    isPlanEditMode.value = true
    currentPlan.value = {
      ...plan,
      seuil: { ...plan.seuil },
      consommables: [...plan.consommables],
      documents: [...plan.documents],
    }

    showPlanDialog.value = true
  }

  const handlePlanDelete = (plan) => {
    if (confirm('Êtes-vous sûr de vouloir supprimer ce plan de maintenance ?')) {
      formData.value.plansMaintenance = formData.value.plansMaintenance.filter((p) => p !== plan)
    }
  }

  const savePlan = () => {
    // Mettre à jour la liste tampon pour permettre la re-sélection ensuite.
    upsertExistingPM(currentPlan.value)
    if (editingPlanIndex.value >= 0) {
      formData.value.plansMaintenance[editingPlanIndex.value] = { ...currentPlan.value }
    } else {
      formData.value.plansMaintenance.push({ ...currentPlan.value })
    }
    closePlanDialog()
  }

  const closePlanDialog = () => {
    showPlanDialog.value = false
    editingPlanIndex.value = -1
    isPlanEditMode.value = false
    currentPlan.value = getEmptyPlan()
  }

  // (ancien) updateExistingPM supprimé : remplacé par upsertExistingPM(planData)

  const closeCounterDialog = () => {
    showCounterDialog.value = false
    editingCounterIndex.value = -1
    isCounterEditMode.value = false
    currentCounter.value = getEmptyCounter()
    errorMessage.value = ''
  }

  const handleFabricantCreated = (newFabricant) => {
    fabricants.value.push(newFabricant)
    formData.value.fabricant = newFabricant.id
  }

  const handleFournisseurCreated = (newFournisseur) => {
    fournisseurs.value.push(newFournisseur)
    formData.value.fournisseur = newFournisseur.id
  }

  const handleModeleCreated = (newModele) => {
    equipmentModels.value.push(newModele)
    formData.value.modeleEquipement = newModele.id
    formData.value.fabricant = newModele.fabricant
  }

  const handleFamilleCreated = (newFamille) => {
    familles.value.push(newFamille)
    formData.value.famille = newFamille.id
  }

  const handleLocationCreated = (newLocation) => {
    locations.value.push(newLocation)
    formData.value.lieu = newLocation.id
  }

  onBeforeUnmount(() => {
    for (const timeoutId of sectionSearchTimeouts.values()) {
      clearTimeout(timeoutId)
    }
    sectionSearchTimeouts.clear()
  })

  const detectChanges = () => {
    if (!initialData.value || !formData.value) return { hasChanges: false, changes: {} }

    const changes = {}
    let hasChanges = false

    const fieldsToCheck = [
      'numSerie',
      'reference',
      'designation',
      'type',
      'dateMiseEnService',
      'prixAchat',
      'modeleEquipement',
      'fournisseur',
      'fabricant',
      'famille',
      'statut',
    ]

    for (let key of fieldsToCheck) {
      if (formData.value[key] !== initialData.value[key]) {
        changes[key] = {
          ancienne: initialData.value[key],
          nouvelle: formData.value[key],
        }
        hasChanges = true
      }
    }

    if (formData.value.lienImageEquipement instanceof File) {
      changes.lienImageEquipement = { nouvelle: 'Nouvelle image' }
      hasChanges = true
    }

    const currentLieu =
      typeof formData.value.lieu === 'object' ? formData.value.lieu?.id : formData.value.lieu
    const initialLieu =
      typeof initialData.value.lieu === 'object'
        ? initialData.value.lieu?.id
        : initialData.value.lieu

    if (currentLieu !== initialLieu) {
      changes.lieu = {
        ancienne: initialLieu,
        nouvelle: currentLieu,
      }
      hasChanges = true
    }

    const currentConsos = JSON.stringify([...(formData.value.consommables || [])].sort())
    const initialConsos = JSON.stringify([...(initialData.value.consommables || [])].sort())

    // L'ordre d'affichage n'a pas de sens metier ici ; on compare donc
    // un ensemble trie pour ne remonter que les vrais changements.
    if (currentConsos !== initialConsos) {
      changes.consommables = {
        ancienne: initialData.value.consommables,
        nouvelle: formData.value.consommables,
      }
      hasChanges = true
    }

    const currentCompteurs = JSON.stringify(formData.value.compteurs)
    const initialCompteurs = JSON.stringify(initialData.value.compteurs)

    if (currentCompteurs !== initialCompteurs) {
      changes.compteurs = { message: 'Compteurs modifiés' }
      hasChanges = true
    }

    return { hasChanges, changes }
  }

  return {
    // State
    formData,
    initialData,
    loading,
    loadingData,
    errorMessage,
    successMessage,

    // Data
    locations,
    equipmentModels,
    fournisseurs,
    fabricants,
    consumables,
    familles,
    typesPM,
    typesDocuments,
    equipmentStatuses,
    equipmentModelsLoading,
    fournisseursLoading,
    fabricantsLoading,
    consumablesLoading,

    // Counter state
    currentCounter,
    editingCounterIndex,
    isCounterEditMode,
    existingPMs,

    // Plan state
    currentPlan,
    editingPlanIndex,
    isPlanEditMode,

    // Dialogs
    showCounterDialog,
    showPlanDialog,
    showFabricantDialog,
    showFournisseurDialog,
    showModeleDialog,
    showFamilleDialog,

    // Methods
    validateForm,
    handleFileUpload,
    fetchData,
    fetchEquipment,
    fetchDocs,
    detectChanges,
    dateToOrdinal,
    ordinalToDate,
    loadSectionOptions,
    searchSectionOptions,

    // Counter methods
    getEmptyCounter,
    handleCounterAdd,
    handleCounterEdit,
    handleCounterDelete,
    saveCurrentCounter,
    closeCounterDialog,

    // Plan methods
    getEmptyPlan,
    handlePlanAdd,
    handlePlanEdit,
    handlePlanDelete,
    savePlan,
    closePlanDialog,

    // Dialog handlers
    handleFabricantCreated,
    handleFournisseurCreated,
    handleModeleCreated,
    handleFamilleCreated,
    handleLocationCreated,

    // Utilities
    api,
    router,
  }
}
