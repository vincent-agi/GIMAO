<template>
  <v-form @submit.prevent="handleSave">
    <!-- Section: Configuration des seuils -->
    <div v-if="!hideSeuilSection">
      <h4 class="mb-3 text-body-1 font-weight-bold">
        <v-icon left color="primary" size="small">mdi-gauge</v-icon>
        Configuration du seuil
      </h4>
      <v-row dense>
        <v-col cols="12" md="6">
          <FormSelect
            v-model="plan.compteurIndex"
            field-name="compteurIndex"
            label="Compteur associé"
            :items="countersForSelect"
            item-title="label"
            item-value="value"
            :disabled="selectedCounterType === 'Calendaire'"
          >
            <template #item="{ props: itemProps, item }">
              <v-list-item v-bind="itemProps">
                <template #prepend>
                  <v-icon :color="item.raw.isPrincipal ? 'primary' : 'grey'">
                    mdi-{{ item.raw.isPrincipal ? 'star' : 'counter' }}
                  </v-icon>
                </template>
                <v-list-item-title>
                  {{ item.raw.nomCompteur || 'Compteur sans nom' }}
                  <span v-if="item.raw.isPrincipal" class="text-caption text-primary ml-1"
                    >(Principal)</span
                  >
                </v-list-item-title>
                <v-list-item-subtitle v-if="item.raw.type !== 'Calendaire'">
                  {{ item.raw.currentValue }} {{ item.raw.unit }}
                </v-list-item-subtitle>
                <v-list-item-subtitle v-else>
                  {{ ordinalToDisplay(item.raw.currentValue) ?? '—' }}
                </v-list-item-subtitle>
              </v-list-item>
            </template>
          </FormSelect>
        </v-col>

        <v-col cols="12" md="6">
          <FormField
            :model-value="selectedCounterValue"
            field-name="valeurCompteur"
            label="Valeur du compteur"
            :readonly="true"
            :suffix="selectedCounterType === 'Calendaire' ? '' : selectedCounterUnit"
            :type="selectedCounterType === 'Calendaire' ? 'date' : 'text'"
          />
        </v-col>
      </v-row>

      <!-- Seuil numérique ou calendaire selon le type de compteur -->
      <!-- On préserve estGlissant lors des mises à jour du seuil :
           SeuilNumerique et SeuilCalendaire n'ont pas connaissance de ce champ,
           donc un simple v-model l'écraserait à chaque frappe. -->
      <SeuilNumerique
        v-if="selectedCounterType !== 'Calendaire'"
        :model-value="plan.seuil"
        :est-glissant="!!plan.seuil.estGlissant"
        :valeur-courante="selectedCounter?.valeurCourante ?? null"
        :unite="selectedCounterUnit"
        @update:model-value="
          (val) => (plan.seuil = { ...val, estGlissant: plan.seuil.estGlissant })
        "
      />
      <SeuilCalendaire
        v-else
        :model-value="plan.seuil"
        :est-glissant="!!plan.seuil.estGlissant"
        :valeur-courante="selectedCounter?.valeurCourante ?? null"
        @update:model-value="
          (val) => (plan.seuil = { ...val, estGlissant: plan.seuil.estGlissant })
        "
      />

      <v-row dense class="mt-2">
        <v-col cols="12" md="4">
          <FormCheckbox
            v-model="plan.seuil.estGlissant"
            field-name="estGlissant"
            label="Seuil glissant"
          />
        </v-col>
      </v-row>

      <v-divider class="my-4"></v-divider>
    </div>

    <!-- Sélection de PM existant ou création -->
    <div v-if="showPmSelection">
      <h4 class="mb-3 text-body-1 font-weight-bold">
        <v-icon left color="primary" size="small">mdi-clipboard-check</v-icon>
        Opération de maintenance
      </h4>
      <v-radio-group v-model="pmMode" inline hide-details class="mb-4">
        <v-radio
          label="Sélectionner une opération de maintenance existante"
          value="existing"
        ></v-radio>
        <v-radio label="Créer une nouvelle opération de maintenance" value="new"></v-radio>
      </v-radio-group>
      <v-divider class="my-4"></v-divider>
    </div>

    <!-- Sélection PM existant -->
    <div v-if="showPmSelection && pmMode === 'existing'">
      <v-row dense>
        <v-col cols="12">
          <v-select
            v-model="selectedExistingPMId"
            :items="existingPMs"
            item-title="nom"
            item-value="id"
            label="Sélectionner une opération de maintenance"
            variant="outlined"
            density="comfortable"
            clearable
          >
            <template #item="{ props: itemProps, item }">
              <v-list-item v-bind="itemProps">
                <template #title>{{ item.raw.nom }}</template>
                <template #subtitle>{{
                  getPMTypeLabel(item.raw.type_id ?? item.raw.type)
                }}</template>
              </v-list-item>
            </template>
          </v-select>
        </v-col>
      </v-row>

      <v-alert v-if="selectedExistingPM" type="info" class="mt-4" variant="tonal">
        <div class="text-subtitle-2 font-weight-bold mb-2">
          <v-icon left size="small">mdi-information</v-icon>
          Aperçu de l'opération de maintenance sélectionnée
        </div>
        <v-row dense class="mb-2">
          <v-col cols="12" md="6">
            <div class="text-caption">Nom de l'opération</div>
            <div class="font-weight-medium">{{ selectedExistingPM.nom }}</div>
          </v-col>
          <v-col cols="12" md="6">
            <div class="text-caption">Type de maintenance</div>
            <div class="font-weight-medium">{{ getPMTypeLabel(selectedExistingPM.type_id) }}</div>
          </v-col>
        </v-row>
        <div v-if="selectedExistingPM.description || selectedExistingPM.commentaire" class="mt-2">
          <div class="text-caption">Commentaire</div>
          <div>{{ selectedExistingPM.description || selectedExistingPM.commentaire }}</div>
        </div>
        <div
          v-if="
            selectedExistingPM.necessiteHabilitationElectrique ||
            selectedExistingPM.necessitePermisFeu
          "
          class="mt-2"
        >
          <div class="text-caption mb-1">Habilitations requises</div>
          <v-chip
            v-if="selectedExistingPM.necessiteHabilitationElectrique"
            size="small"
            color="orange"
            class="mr-2"
          >
            <v-icon left size="small">mdi-flash</v-icon>
            Habilitation électrique
          </v-chip>
          <v-chip v-if="selectedExistingPM.necessitePermisFeu" size="small" color="red">
            <v-icon left size="small">mdi-fire</v-icon>
            Permis feu
          </v-chip>
        </div>
      </v-alert>
    </div>

    <!-- Section: Opération de maintenance (nouveau) -->
    <div v-if="!showPmSelection || pmMode === 'new'">
      <h4 class="mb-3 text-body-1 font-weight-bold">
        <v-icon left color="primary" size="small">mdi-clipboard-check</v-icon>
        Informations de l'opération de maintenance
      </h4>
      <v-row dense>
        <v-col cols="12" md="6">
          <FormField
            v-model="plan.nom"
            field-name="nom"
            label="Nom de l'opération de maintenance"
            placeholder="Saisir le nom de l'opération"
            counter="100"
          />
        </v-col>
        <v-col cols="12" md="6">
          <FormSelect
            v-model="plan.type_id"
            field-name="type_id"
            label="Type de maintenance"
            :items="typesPM"
            item-title="libelle"
            item-value="id"
          />
        </v-col>
        <v-col cols="12">
          <FormField
            v-model="plan.description"
            field-name="description"
            label="Description"
            type="textarea"
            rows="2"
            placeholder="Description de l'opération de maintenance"
          />
        </v-col>
      </v-row>

      <v-divider class="my-4"></v-divider>

      <!-- Section: Consommables -->
      <h4 class="mb-3 text-body-1 font-weight-bold">
        <v-icon left color="primary" size="small">mdi-package-variant</v-icon>
        Consommables nécessaires
      </h4>
      <v-row
        v-for="(conso, index) in plan.consommables"
        :key="index"
        dense
        class="mb-2 align-center"
      >
        <v-col cols="12" md="6">
          <v-select
            v-model="conso.consommable_id"
            :items="consumables"
            item-title="designation"
            item-value="id"
            label="Consommable"
            variant="outlined"
            density="comfortable"
            hide-details
          ></v-select>
        </v-col>
        <v-col cols="12" md="5">
          <v-text-field
            v-model="conso.quantite_necessaire"
            type="number"
            label="Quantité nécessaire"
            variant="outlined"
            density="comfortable"
            hide-details
            min="1"
          ></v-text-field>
        </v-col>
        <v-col cols="12" md="1" class="text-center">
          <v-btn icon size="small" color="error" @click="removeConsommable(index)">
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </v-col>
      </v-row>
      <v-row dense>
        <v-col cols="12">
          <v-btn variant="outlined" color="primary" size="small" @click="addConsommable">
            <v-icon left>mdi-plus</v-icon>
            Ajouter un consommable
          </v-btn>
        </v-col>
      </v-row>

      <v-divider class="my-4"></v-divider>

      <!-- Section: Documents -->
      <h4 class="mb-3 text-body-1 font-weight-bold">
        <v-icon left color="primary" size="small">mdi-file-document</v-icon>
        Documents associés
      </h4>
      <DocumentForm v-model="documentFormModel" :type-documents="typesDocuments" />

      <v-divider class="my-4"></v-divider>

      <!-- Section: Habilitations -->
      <h4 class="mb-3 text-body-1 font-weight-bold">
        <v-icon left color="primary" size="small">mdi-shield-account</v-icon>
        Habilitations requises
      </h4>
      <v-row dense>
        <v-col cols="12" md="6">
          <FormCheckbox
            v-model="plan.necessiteHabilitationElectrique"
            field-name="necessiteHabilitationElectrique"
            label="Habilitation électrique requise"
            color="orange"
          />
        </v-col>
        <v-col cols="12" md="6">
          <FormCheckbox
            v-model="plan.necessitePermisFeu"
            field-name="necessitePermisFeu"
            label="Permis feu requis"
            color="red"
          />
        </v-col>
      </v-row>
    </div>

    <v-alert v-if="localError" type="error" class="mt-4">{{ localError }}</v-alert>

    <v-card-actions v-if="showActions" class="px-0 pt-4">
      <v-spacer />
      <v-btn variant="text" @click="handleCancel">Annuler</v-btn>
      <v-btn type="submit" color="primary" :disabled="!isValid">
        {{ isEditMode ? "Modifier l'opération" : "Ajouter l'opération" }}
      </v-btn>
    </v-card-actions>
  </v-form>
</template>

<script setup>
  import { computed, ref, watch } from 'vue'
  import { FormField, FormCheckbox, FormSelect } from '@/components/common'
  import DocumentForm from '@/components/Forms/DocumentForm.vue'
  import SeuilNumerique from '@/components/Forms/Seuil/SeuilNumerique.vue'
  import SeuilCalendaire from '@/components/Forms/Seuil/SeuilCalendaire.vue'

  const props = defineProps({
    modelValue: {
      type: Object,
      required: true,
    },
    isEditMode: {
      type: Boolean,
      default: false,
    },
    showActions: {
      type: Boolean,
      default: true,
    },
    hideSeuilSection: {
      type: Boolean,
      default: false,
    },
    showPmSelection: {
      type: Boolean,
      default: false,
    },
    existingPMs: {
      type: Array,
      default: () => [],
    },
    counters: {
      type: Array,
      default: () => [],
    },
    counterFilter: {
      type: String,
      default: 'all',
    },
    typesPM: {
      type: Array,
      default: () => [],
    },
    consumables: {
      type: Array,
      default: () => [],
    },
    typesDocuments: {
      type: Array,
      default: () => [],
    },
  })

  const emit = defineEmits(['update:modelValue', 'save', 'cancel'])

  const localError = ref('')
  const pmMode = ref('new')
  const selectedExistingPMId = ref(null)

  const plan = computed({
    get: () => props.modelValue,
    set: (v) => emit('update:modelValue', v),
  })

  // --- Compteurs ---

  const countersForSelect = computed(() =>
    props.counters
      .map((counter, index) => ({ counter, index }))
      .filter(({ counter }) => {
        const cal =
          counter?.isDefaultCalendar === true ||
          counter?.type?.toLowerCase() === 'calendaire' ||
          counter?.unite === 'date'
        if (props.counterFilter === 'calendar') return cal
        if (props.counterFilter === 'numeric') return !cal
        return true
      })
      .map(({ counter, index }) => ({
        value: index,
        label: counter.nomCompteur || 'Compteur sans nom',
        type: counter.type,
        isPrincipal: counter.estPrincipal,
        currentValue: counter.valeurCourante,
        unit: counter.unite,
      }))
  )

  watch(
    countersForSelect,
    (items) => {
      if (!items.length) {
        plan.value.compteurIndex = null
        return
      }

      const isCurrentStillAvailable = items.some((item) => item.value === plan.value.compteurIndex)
      if (!isCurrentStillAvailable) {
        plan.value.compteurIndex = items[0].value
      }
    },
    { immediate: true }
  )

  watch(
    () => props.counterFilter,
    (mode) => {
      if (mode !== 'numeric') return
      const selected = props.counters?.[plan.value.compteurIndex]
      const selectedIsCalendar =
        selected?.isDefaultCalendar === true || selected?.type === 'Calendaire'
      if (selectedIsCalendar) {
        const firstNumeric = countersForSelect.value.find((item) => {
          const counter = props.counters?.[item.value]
          return !(counter?.isDefaultCalendar === true || counter?.type === 'Calendaire')
        })
        plan.value.compteurIndex = firstNumeric ? firstNumeric.value : null
      }
    },
    { immediate: true }
  )

  const selectedCounter = computed(() => {
    if (plan.value.compteurIndex === null || plan.value.compteurIndex === undefined) return null
    return props.counters[plan.value.compteurIndex] ?? null
  })

  const isCalendarCounter = (c) =>
    c?.type?.toLowerCase() === 'calendaire' || c?.unite === 'date' || c?.isDefaultCalendar === true

  const selectedCounterType = computed(() =>
    isCalendarCounter(selectedCounter.value) ? 'Calendaire' : (selectedCounter.value?.type ?? '')
  )
  const selectedCounterUnit = computed(() => selectedCounter.value?.unite ?? '')

  const selectedCounterValue = computed(() => {
    if (!selectedCounter.value) return '—'
    if (selectedCounterType.value === 'Calendaire') {
      return ordinalToISO(selectedCounter.value.valeurCourante)
    }
    return selectedCounter.value.valeurCourante ?? '—'
  })

  // Utilitaire (lecture seule ici, la conversion onMounted vit dans SeuilCalendaire)
  const ordinalToISO = (ordinal) => {
    if (ordinal == null || ordinal <= 0) return null
    const ORDINAL_EPOCH = 719162
    const date = new Date(Date.UTC(1970, 0, 1 + (ordinal - ORDINAL_EPOCH)))
    if (isNaN(date.getTime())) return null
    return date.toISOString().split('T')[0]
  }

  const ordinalToDisplay = (ordinal) => {
    const iso = ordinalToISO(ordinal)
    if (!iso) return null
    const [year, month, day] = iso.split('-')
    return `${day}/${month}/${year}`
  }

  // --- PM existant ---

  const selectedExistingPM = computed(() =>
    props.existingPMs.find((pm) => pm.id === selectedExistingPMId.value)
  )

  const getPMTypeLabel = (typeId) => {
    const type = props.typesPM.find((t) => t.id === typeId)
    return type ? type.libelle : 'Non spécifié'
  }

  const applyExistingPMToPlan = (pm) => {
    if (!pm) return
    plan.value.id = pm.id
    plan.value.nom = pm.nom ?? plan.value.nom
    plan.value.type_id = pm.type_id ?? pm.type ?? plan.value.type_id
    plan.value.description = pm.description ?? pm.commentaire ?? plan.value.description
    plan.value.necessiteHabilitationElectrique = !!pm.necessiteHabilitationElectrique
    plan.value.necessitePermisFeu = !!pm.necessitePermisFeu
    plan.value.consommables = Array.isArray(pm.consommables)
      ? pm.consommables.map((c) => ({
          consommable_id: c.consommable_id || c.id,
          quantite_necessaire: c.quantite_necessaire || c.quantite || 1,
        }))
      : []
    plan.value.documents = Array.isArray(pm.documents)
      ? pm.documents.map((d) => ({
          nom: d.nomDocument || d.nom || d.titre,
          type_id: d.typeDocument_id || d.type_id || d.type,
          file: null,
        }))
      : []
    // seuil et compteurIndex intentionnellement préservés
  }

  watch(pmMode, (mode) => {
    localError.value = ''
    if (mode !== 'existing') selectedExistingPMId.value = null
  })

  watch(selectedExistingPMId, () => {
    localError.value = ''
    if (!props.showPmSelection || pmMode.value !== 'existing') return
    if (selectedExistingPM.value) applyExistingPMToPlan(selectedExistingPM.value)
  })

  // --- Documents (adaptateur vers DocumentForm) ---

  const documentFormModel = computed({
    get: () => {
      const base = Array.isArray(plan.value.documents) ? plan.value.documents : []
      return base.map((d) => ({
        document_id: d.document_id ?? d.id ?? null,
        nomDocument: d.nomDocument ?? d.nom ?? d.titre ?? '',
        typeDocument_id: (() => {
          const raw = d.typeDocument_id ?? d.type_id ?? d.type ?? null
          return raw === null || raw === undefined || raw === '' ? null : raw
        })(),
        file: d.file ?? null,
        existingFileName: d.existingFileName ?? d.path ?? null,
      }))
    },
    set: (rows) => {
      const normalized = (Array.isArray(rows) ? rows : []).map((d) => ({
        nom: d?.nomDocument ?? '',
        type_id: d?.typeDocument_id ?? null,
        file: d?.file ?? null,
      }))
      plan.value = { ...plan.value, documents: normalized }
    },
  })

  // --- Consommables ---

  const addConsommable = () => {
    if (!plan.value.consommables) plan.value.consommables = []
    plan.value.consommables.push({ consommable_id: null, quantite_necessaire: 1 })
  }

  const removeConsommable = (index) => {
    plan.value.consommables.splice(index, 1)
  }

  // --- Validation ---

  const isValid = computed(() => {
    const seuilValid = Number(plan.value.seuil?.ecartInterventions) > 0
    if (!seuilValid) return false

    if (props.showPmSelection && pmMode.value === 'existing') {
      return (
        !!selectedExistingPMId.value &&
        plan.value.compteurIndex !== null &&
        plan.value.compteurIndex !== undefined
      )
    }

    return (
      plan.value.nom?.trim() !== '' &&
      plan.value.type_id !== null &&
      plan.value.compteurIndex !== null &&
      plan.value.compteurIndex !== undefined
    )
  })

  // --- Actions ---

  const handleSave = () => {
    if (!isValid.value) {
      localError.value = 'Veuillez remplir tous les champs obligatoires (nom, type et compteur)'
      return
    }
    localError.value = ''
    emit('save', {
      pmMode: pmMode.value,
      selectedExistingPMId: selectedExistingPMId.value,
      planData: plan.value,
    })
  }

  const handleCancel = () => {
    localError.value = ''
    emit('cancel')
  }
</script>
