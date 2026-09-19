<template>
  <v-form @submit.prevent="handleSave">
    <!-- Équipement -->
    <v-card-subtitle class="text-h6 font-weight-bold px-0 pb-2">Équipement</v-card-subtitle>
    <v-row dense>
      <v-col cols="12">
        <v-autocomplete
          v-model="formData.equipement_id"
          :items="equipments"
          item-title="designation"
          item-value="id"
          label="Équipement *"
          variant="outlined"
          density="comfortable"
          clearable
          :loading="loadingCounters"
          @update:model-value="onEquipementChange"
        />
      </v-col>
    </v-row>

    <template v-if="formData.equipement_id">
      <v-divider class="my-4" />

      <!-- Mode déclencheur -->
      <v-card-subtitle class="text-h6 font-weight-bold px-0 pb-2">
        <v-icon left color="primary" size="small">mdi-tune</v-icon>
        Mode de déclenchement
      </v-card-subtitle>

      <v-radio-group v-model="formData.triggerMode" inline hide-details class="mb-2">
        <v-radio label="Calendrier" value="calendar" />
        <v-radio label="Compteur numérique" value="numeric" />
        <v-radio
          label="Au premier qui arrive à échéance"
          value="first"
          :disabled="!hasCalendarCounter"
        />
      </v-radio-group>

      <!-- Compteurs existants + bouton ajouter -->
      <div class="d-flex align-center flex-wrap gap-2 mb-3 mt-2">
        <v-chip
          v-for="c in numericCounters"
          :key="c.id"
          size="small"
          color="primary"
          variant="tonal"
          prepend-icon="mdi-counter"
        >
          {{ c.nom }} {{ c.valeurCourante }} {{ c.unite }}
        </v-chip>
        <v-btn
          size="small"
          variant="outlined"
          color="primary"
          prepend-icon="mdi-plus"
          @click="showAddCounterDialog = true"
        >
          Ajouter un compteur
        </v-btn>
      </div>

      <v-alert
        v-if="
          (formData.triggerMode === 'numeric' || formData.triggerMode === 'first') &&
          numericCounters.length === 0
        "
        type="warning"
        variant="tonal"
        density="compact"
        class="mb-2"
      >
        Aucun compteur numérique pour cet équipement. Utilisez le bouton "Ajouter un compteur"
        ci-dessous.
      </v-alert>

      <v-alert
        v-if="formData.triggerMode === 'first'"
        type="info"
        variant="tonal"
        density="compact"
        class="mb-4"
      >
        <v-icon start>mdi-information</v-icon>
        Si le calendrier et le compteur arrivent à échéance en même temps, le calendrier est
        prioritaire.
      </v-alert>

      <v-divider class="my-4" />

      <!-- Section Calendrier -->
      <template v-if="formData.triggerMode === 'calendar' || formData.triggerMode === 'first'">
        <v-card-subtitle class="text-h6 font-weight-bold px-0 pb-2">
          <v-icon left color="primary" size="small">mdi-calendar-clock</v-icon>
          Périodicité calendrier
        </v-card-subtitle>

        <SeuilCalendaire
          :model-value="formData.seuilCalendaire"
          :est-glissant="formData.estGlissantCalendaire"
          :valeur-courante="calendarCounterValue"
          @update:model-value="
            (val) =>
              (formData.seuilCalendaire = { ...val, estGlissant: formData.estGlissantCalendaire })
          "
        />

        <v-row dense class="mt-2">
          <v-col cols="12" md="4">
            <v-checkbox
              v-model="formData.estGlissantCalendaire"
              label="Seuil glissant"
              density="comfortable"
              hide-details
              color="primary"
            />
          </v-col>
          <v-col v-if="formData.triggerMode === 'calendar'" cols="12" md="8">
            <v-select
              v-model="formData.anticipation"
              :items="anticipationOptions"
              item-title="label"
              item-value="value"
              label="Anticipation (déclenchement avant échéance)"
              variant="outlined"
              density="comfortable"
              clearable
              hide-details
            />
          </v-col>
        </v-row>

        <v-divider class="my-4" />
      </template>

      <!-- Section Compteur numérique -->
      <template v-if="formData.triggerMode === 'numeric' || formData.triggerMode === 'first'">
        <v-card-subtitle class="text-h6 font-weight-bold px-0 pb-2">
          <v-icon left color="primary" size="small">mdi-counter</v-icon>
          Périodicité compteur
        </v-card-subtitle>

        <!-- Pas encore de compteur numérique : on cache le formulaire -->
        <template v-if="numericCounters.length === 0">
          <v-divider class="my-4" />
        </template>

        <template v-else>
          <v-row dense>
            <v-col cols="12" md="6">
              <v-select
                v-model="formData.numericCounterId"
                :items="numericCounters"
                item-title="nom"
                item-value="id"
                label="Compteur *"
                variant="outlined"
                density="comfortable"
                hide-details
              >
                <template #item="{ props: itemProps, item }">
                  <v-list-item v-bind="itemProps">
                    <template #prepend>
                      <v-icon :color="item.raw.estPrincipal ? 'primary' : 'grey'">
                        {{ item.raw.estPrincipal ? 'mdi-star' : 'mdi-counter' }}
                      </v-icon>
                    </template>
                    <v-list-item-title>
                      {{ item.raw.nom }}
                      <span v-if="item.raw.estPrincipal" class="text-caption text-primary ml-1"
                        >(Principal)</span
                      >
                    </v-list-item-title>
                    <v-list-item-subtitle
                      >{{ item.raw.valeurCourante }} {{ item.raw.unite }}</v-list-item-subtitle
                    >
                  </v-list-item>
                </template>
              </v-select>
            </v-col>
            <v-col v-if="selectedNumericCounter" cols="12" md="6">
              <v-text-field
                :model-value="`${selectedNumericCounter.valeurCourante} ${selectedNumericCounter.unite}`"
                label="Valeur actuelle"
                variant="outlined"
                density="comfortable"
                readonly
                hide-details
              />
            </v-col>
          </v-row>

          <v-row dense class="mt-3">
            <v-col cols="12">
              <SeuilNumerique
                :model-value="formData.seuilNumerique"
                :est-glissant="formData.estGlissantNumerique"
                :valeur-courante="selectedNumericCounter?.valeurCourante ?? null"
                :unite="selectedNumericCounter?.unite ?? ''"
                @update:model-value="
                  (val) =>
                    (formData.seuilNumerique = {
                      ...val,
                      estGlissant: formData.estGlissantNumerique,
                    })
                "
              />
            </v-col>
          </v-row>

          <v-row dense class="mt-2">
            <v-col cols="12" md="4">
              <v-checkbox
                v-model="formData.estGlissantNumerique"
                label="Seuil glissant"
                density="comfortable"
                hide-details
                color="primary"
              />
            </v-col>
          </v-row>

          <v-divider class="my-4" /> </template
        ><!-- fin v-else (compteurs disponibles) -->
      </template>

      <!-- Opération de maintenance -->
      <v-card-subtitle class="text-h6 font-weight-bold px-0 pb-2">
        <v-icon left color="primary" size="small">mdi-clipboard-check</v-icon>
        Opération de maintenance
      </v-card-subtitle>

      <v-row dense>
        <v-col cols="12" md="6">
          <v-text-field
            v-model="formData.nom"
            label="Nom de l'opération *"
            variant="outlined"
            density="comfortable"
            counter="100"
            placeholder="Saisir le nom"
          />
        </v-col>
        <v-col cols="12" md="6">
          <v-select
            v-model="formData.type_id"
            :items="typesPM"
            item-title="libelle"
            item-value="id"
            label="Type de maintenance *"
            variant="outlined"
            density="comfortable"
          />
        </v-col>
        <v-col cols="12">
          <v-textarea
            v-model="formData.description"
            label="Description"
            variant="outlined"
            density="comfortable"
            rows="2"
            placeholder="Description de l'opération"
          />
        </v-col>
      </v-row>

      <v-divider class="my-4" />

      <!-- Consommables -->
      <v-card-subtitle class="text-h6 font-weight-bold px-0 pb-2">
        <v-icon left color="primary" size="small">mdi-package-variant</v-icon>
        Consommables nécessaires
      </v-card-subtitle>

      <v-row v-for="(conso, i) in formData.consommables" :key="i" dense class="mb-2 align-center">
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
          />
        </v-col>
        <v-col cols="12" md="5">
          <v-text-field
            v-model="conso.quantite_necessaire"
            type="number"
            label="Quantité"
            variant="outlined"
            density="comfortable"
            hide-details
            min="1"
          />
        </v-col>
        <v-col cols="1" class="text-center">
          <v-btn icon size="small" color="error" @click="formData.consommables.splice(i, 1)">
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </v-col>
      </v-row>
      <v-btn variant="outlined" color="primary" size="small" class="mb-4" @click="addConsommable">
        <v-icon left>mdi-plus</v-icon> Ajouter un consommable
      </v-btn>

      <v-divider class="my-4" />

      <!-- Habilitations -->
      <v-card-subtitle class="text-h6 font-weight-bold px-0 pb-2">
        <v-icon left color="primary" size="small">mdi-shield-account</v-icon>
        Habilitations requises
      </v-card-subtitle>
      <v-row dense>
        <v-col cols="12" md="6">
          <v-checkbox
            v-model="formData.necessiteHabilitationElectrique"
            label="Habilitation électrique"
            color="orange"
            density="comfortable"
            hide-details
          />
        </v-col>
        <v-col cols="12" md="6">
          <v-checkbox
            v-model="formData.necessitePermisFeu"
            label="Permis feu"
            color="red"
            density="comfortable"
            hide-details
          />
        </v-col>
      </v-row>
    </template>

    <v-alert v-if="localError" type="error" class="mt-4">{{ localError }}</v-alert>

    <v-card-actions class="px-0 pt-4">
      <v-spacer />
      <v-btn variant="text" @click="$emit('cancel')">Annuler</v-btn>
      <v-btn type="submit" color="primary" :loading="loading" :disabled="!isValid">
        Enregistrer
      </v-btn>
    </v-card-actions>
  </v-form>

  <!-- Dialog ajout compteur -->
  <v-dialog v-model="showAddCounterDialog" max-width="600" persistent>
    <v-card>
      <v-card-title class="text-h6 pa-4 pb-2">Ajouter un compteur</v-card-title>
      <v-divider />
      <v-card-text class="pa-4">
        <CounterInlineForm
          v-model="newCounter"
          :is-edit-mode="false"
          :is-first-counter="numericCounters.length === 0"
          @save="saveNewCounter"
          @cancel="showAddCounterDialog = false"
        />
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
  import { ref, computed, watch } from 'vue'
  import { useApi } from '@/composables/useApi'
  import { API_BASE_URL } from '@/utils/constants'
  import SeuilCalendaire from '@/components/Forms/Seuil/SeuilCalendaire.vue'
  import SeuilNumerique from '@/components/Forms/Seuil/SeuilNumerique.vue'
  import CounterInlineForm from '@/components/Forms/CounterInlineForm.vue'

  const props = defineProps({
    equipments: { type: Array, default: () => [] },
    typesPM: { type: Array, default: () => [] },
    consumables: { type: Array, default: () => [] },
    initialEquipmentId: { type: Number, default: null },
  })

  const emit = defineEmits(['saved', 'cancel'])

  const api = useApi(API_BASE_URL)

  const anticipationOptions = [
    { label: 'Aucune anticipation', value: null },
    { label: '5 jours avant', value: 5 },
    { label: '1 semaine avant', value: 7 },
  ]

  const loadingCounters = ref(false)
  const loading = ref(false)
  const localError = ref('')
  const equipmentCounters = ref([])
  const showAddCounterDialog = ref(false)
  const newCounter = ref(emptyCounter())

  function emptyCounter() {
    return {
      nomCompteur: '',
      valeurCourante: 0,
      unite: 'heures',
      estPrincipal: false,
      type: 'Numérique',
      isDefaultCalendar: false,
    }
  }

  const formData = ref(emptyForm())

  function emptyForm() {
    return {
      equipement_id: null,
      triggerMode: 'calendar',
      // calendar
      seuilCalendaire: {
        derniereIntervention: null,
        ecartInterventions: 0,
        prochaineMaintenance: null,
        uniteCalendaire: 'days',
        ecartCalendaire: 0,
      },
      estGlissantCalendaire: false,
      anticipation: null,
      // numeric
      numericCounterId: null,
      seuilNumerique: { derniereIntervention: 0, ecartInterventions: 0, prochaineMaintenance: 0 },
      estGlissantNumerique: false,
      // PM info
      nom: '',
      type_id: null,
      description: '',
      consommables: [],
      necessiteHabilitationElectrique: false,
      necessitePermisFeu: false,
    }
  }

  const calendarCounter = computed(() =>
    equipmentCounters.value.find(
      (c) =>
        c.isDefaultCalendar === true || c.type?.toLowerCase() === 'calendaire' || c.unite === 'date'
    )
  )
  const hasCalendarCounter = computed(() => !!calendarCounter.value)
  const calendarCounterValue = computed(() => calendarCounter.value?.valeurCourante ?? null)

  const numericCounters = computed(() =>
    equipmentCounters.value.filter(
      (c) =>
        c.isDefaultCalendar !== true && c.type?.toLowerCase() !== 'calendaire' && c.unite !== 'date'
    )
  )

  const selectedNumericCounter = computed(
    () => numericCounters.value.find((c) => c.id === formData.value.numericCounterId) ?? null
  )

  const onEquipementChange = async (id) => {
    formData.value = emptyForm()
    formData.value.equipement_id = id
    equipmentCounters.value = []
    if (!id) return

    loadingCounters.value = true
    try {
      const eq = await api.get(`equipement/${id}/affichage/`, { seuils_lite: true })
      equipmentCounters.value = eq.compteurs || []
      // Pré-sélectionner le premier compteur numérique
      if (numericCounters.value.length > 0) {
        formData.value.numericCounterId = numericCounters.value[0].id
      }
    } catch (e) {
      console.error(e)
    } finally {
      loadingCounters.value = false
    }
  }

  const saveNewCounter = async () => {
    try {
      const fd = new FormData()
      const counterData = {
        nom: newCounter.value.nomCompteur,
        unite: newCounter.value.unite,
        valeurCourante: newCounter.value.valeurCourante ?? 0,
        estPrincipal: newCounter.value.estPrincipal,
        equipement: formData.value.equipement_id,
        type: newCounter.value.type,
      }
      fd.append('compteur', JSON.stringify(counterData))
      await api.post('compteurs/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })

      // Rafraîchir les compteurs de l'équipement
      const eq = await api.get(`equipement/${formData.value.equipement_id}/affichage/`, {
        seuils_lite: true,
      })
      equipmentCounters.value = eq.compteurs || []
      // Pré-sélectionner le compteur créé
      if (numericCounters.value.length > 0 && !formData.value.numericCounterId) {
        formData.value.numericCounterId = numericCounters.value[numericCounters.value.length - 1].id
      }
      showAddCounterDialog.value = false
      newCounter.value = emptyCounter()
    } catch (e) {
      console.error('Erreur création compteur:', e)
    }
  }

  const createCalendarCounter = async (equipementId) => {
    try {
      const today = new Date()
      const yyyy = today.getFullYear()
      const mm = String(today.getMonth() + 1).padStart(2, '0')
      const dd = String(today.getDate()).padStart(2, '0')
      const todayISO = `${yyyy}-${mm}-${dd}`

      const fd = new FormData()
      fd.append(
        'compteur',
        JSON.stringify({
          nom: 'Calendrier',
          valeurCourante: todayISO,
          unite: 'date',
          estPrincipal: false,
          equipement: equipementId,
          type: 'Calendaire',
        })
      )
      const res = await api.post('compteurs/', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      // Rafraîchir les compteurs
      const eq = await api.get(`equipement/${equipementId}/affichage/`, { seuils_lite: true })
      equipmentCounters.value = eq.compteurs || []
      return res?.id ?? calendarCounter.value?.id ?? null
    } catch (e) {
      console.error('Erreur création compteur calendaire:', e)
      return null
    }
  }

  // Pré-charger l'équipement si fourni par le parent
  watch(
    () => props.initialEquipmentId,
    async (id) => {
      if (id && id !== formData.value.equipement_id) {
        await onEquipementChange(id)
      }
    },
    { immediate: true }
  )

  // Reset le mode si les compteurs ne supportent pas le choix
  watch(numericCounters, (list) => {
    if (
      list.length === 0 &&
      (formData.value.triggerMode === 'numeric' || formData.value.triggerMode === 'first')
    ) {
      formData.value.triggerMode = 'calendar'
    }
  })

  const addConsommable = () => {
    formData.value.consommables.push({ consommable_id: null, quantite_necessaire: 1 })
  }

  const isValid = computed(() => {
    if (!formData.value.equipement_id) return false
    if (!formData.value.nom?.trim()) return false
    if (!formData.value.type_id) return false

    if (formData.value.triggerMode === 'calendar' || formData.value.triggerMode === 'first') {
      if (!Number(formData.value.seuilCalendaire.ecartInterventions) > 0) return false
    }
    if (formData.value.triggerMode === 'numeric' || formData.value.triggerMode === 'first') {
      if (!formData.value.numericCounterId) return false
      if (!(Number(formData.value.seuilNumerique.ecartInterventions) > 0)) return false
    }
    return true
  })

  const buildFormData = (seuil, compteurId, estGlissant, anticipationDays, modeDeclenchement) => {
    const fd = new FormData()

    fd.append('compteur', String(compteurId))

    fd.append(
      'seuil',
      JSON.stringify({
        derniereIntervention: seuil.derniereIntervention ?? null,
        ecartInterventions: seuil.ecartInterventions ?? 0,
        prochaineMaintenance: seuil.prochaineMaintenance ?? null,
        estGlissant: !!estGlissant,
      })
    )

    fd.append(
      'planMaintenance',
      JSON.stringify({
        id: null,
        nom: formData.value.nom,
        type_id: formData.value.type_id,
        commentaire: formData.value.description || '',
        necessiteHabilitationElectrique: !!formData.value.necessiteHabilitationElectrique,
        necessitePermisFeu: !!formData.value.necessitePermisFeu,
        consommables: formData.value.consommables.filter((c) => c.consommable_id),
        documents: [],
      })
    )

    if (anticipationDays) fd.append('anticipationJours', String(anticipationDays))
    if (modeDeclenchement) fd.append('mode_declenchement', modeDeclenchement)

    return fd
  }

  const handleSave = async () => {
    if (!isValid.value) return
    loading.value = true
    localError.value = ''

    try {
      const requests = []
      const opts = { headers: { 'Content-Type': 'multipart/form-data' } }

      if (formData.value.triggerMode === 'calendar' || formData.value.triggerMode === 'first') {
        let compteurId = calendarCounter.value?.id
        if (!compteurId) {
          // Créer le compteur calendaire automatiquement
          compteurId = await createCalendarCounter(formData.value.equipement_id)
          if (!compteurId) throw new Error('Impossible de créer le compteur calendaire.')
        }
        const mode = formData.value.triggerMode === 'first' ? 'premier' : null
        requests.push(
          api.post(
            'declenchements/',
            buildFormData(
              formData.value.seuilCalendaire,
              compteurId,
              formData.value.estGlissantCalendaire,
              formData.value.anticipation,
              mode
            ),
            opts
          )
        )
      }

      if (formData.value.triggerMode === 'numeric' || formData.value.triggerMode === 'first') {
        const mode = formData.value.triggerMode === 'first' ? 'premier' : null
        requests.push(
          api.post(
            'declenchements/',
            buildFormData(
              formData.value.seuilNumerique,
              formData.value.numericCounterId,
              formData.value.estGlissantNumerique,
              null,
              mode
            ),
            opts
          )
        )
      }

      await Promise.all(requests)
      emit('saved', formData.value.equipement_id)
    } catch (e) {
      console.error(e)
      localError.value = e.message || "Une erreur est survenue lors de l'enregistrement."
    } finally {
      loading.value = false
    }
  }
</script>
