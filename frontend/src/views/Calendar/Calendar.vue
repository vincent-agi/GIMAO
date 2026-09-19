<template>
  <v-container fluid class="calendar-container pa-4">
    <v-card class="pa-4 elevation-2 rounded-lg">
      <!-- Loader -->
      <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-2" />

      <!-- Tabs -->
      <v-tabs v-model="mode" class="mb-4" color="primary" grow @update:model-value="handleNewMode">
        <v-tab value="bt" class="text-none font-weight-medium">
          <v-icon start>mdi-wrench</v-icon>
          Bons de Travail
        </v-tab>

        <v-tab value="maintenance" class="text-none font-weight-medium">
          <v-icon start>mdi-calendar-refresh</v-icon>
          Maintenance Préventive
        </v-tab>
      </v-tabs>

      <!-- Calendrier -->
      <div class="calendar-wrapper">
        <div v-if="mode === 'bt'" class="mb-3 px-2 d-flex flex-wrap ga-3 align-center">
          <FormField
            v-model="dayStartTime"
            field-name="calendar_day_start_time"
            type="time"
            label="Début (jour/semaine)"
            style="max-width: 180px"
          />

          <FormField
            v-model="dayEndTime"
            field-name="calendar_day_end_time"
            type="time"
            label="Fin (jour/semaine)"
            :error="isTimeRangeInvalid"
            :error-messages="
              isTimeRangeInvalid ? 'L\'heure de fin doit être après l\'heure de début.' : ''
            "
            style="max-width: 180px"
          />

          <div class="flex-grow-1" style="min-width: 260px">
            <FormSelect
              v-model="technicienSelected"
              field-name="technicien_filter"
              :items="techniciensOptions"
              item-title="nom"
              item-value="id"
              label="Filtrer par technicien"
              clearable
            />
          </div>

          <div class="flex-grow-1" style="min-width: 260px">
            <FormSelect
              v-model="equipmentSelected"
              field-name="equipment_filter"
              :items="equipmentsOptions"
              item-title="nom"
              item-value="id"
              label="Filtrer par équipement"
              clearable
            />
          </div>
        </div>

        <div v-if="mode === 'maintenance'" class="mb-3 px-2">
          <FormSelect
            v-model="equipmentSelected"
            field-name="equipment_filter"
            :items="equipmentsOptions"
            item-title="nom"
            item-value="id"
            label="Filtrer par équipement"
            clearable
          />
        </div>

        <vue-cal
          ref="vuecal"
          :events="currentEvents"
          :time-from="calendarTimeFrom"
          :time-to="calendarTimeTo"
          :time-step="30"
          active-view="month"
          locale="fr"
          :first-day-of-week="2"
          :on-event-click="onEventClick"
          :max-events-per-cell="3"
          events-on-month-view="short"
          :today-button="true"
          :click-to-navigate="false"
          show-week-numbers
          :time-cell-height="48"
          class="vuecal--custom"
          @view-change="({ view }) => (currentView = view)"
        >
          <template #event="{ event }">
            <div
              class="event-inner"
              :style="{
                '--bg-color': event.backgroundColor || '#1E88E5',
                backgroundColor: 'var(--bg-color)',
                color: event.color || '#fff',
              }"
            >
              <!-- Vue mois -->
              <template v-if="currentView === 'month'">
                <div class="event-content d-flex align-center gap-1">
                  <span class="event-title">{{ event.title }}</span>
                </div>
              </template>

              <!-- Vue semaine / jour -->
              <template v-else>
                <div class="event-content d-flex flex-column">
                  <span class="event-title font-weight-medium">{{ event.title }}</span>

                  <span
                    v-if="event.start && event.end && event.class !== 'event-mp'"
                    class="event-time"
                  >
                    {{
                      new Date(event.start).toLocaleString('fr-FR', {
                        day: '2-digit',
                        month: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                      })
                    }}
                    -
                    {{
                      new Date(event.end).toLocaleString('fr-FR', {
                        day: '2-digit',
                        month: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                      })
                    }}
                  </span>

                  <span v-if="event.equipement" class="event-equipement">
                    <v-icon size="12">mdi-cog</v-icon>
                    {{ event.equipement.nom }}
                  </span>

                  <span v-if="event.techniciens?.length" class="event-techniciens">
                    <span v-if="currentView === 'week'">
                      <v-icon size="12">mdi-account</v-icon>
                      {{
                        event.techniciens.length > 1
                          ? event.techniciens.length + ' techniciens'
                          : event.techniciens[0].nom
                      }}
                    </span>

                    <span v-else class="event-techniciens">
                      <v-icon size="12">mdi-account</v-icon>
                      <span v-for="(t, i) in event.techniciens" :key="t.id">
                        {{ t.nom }}<span v-if="i < event.techniciens.length - 1">, </span>
                      </span>
                    </span>
                  </span>
                </div>
              </template>
            </div>
          </template>
        </vue-cal>

        <span v-if="mode === 'maintenance'" class="caption mt-2 d-block text-center">
          * Les événements de maintenance préventive sont affichés dans leur jour prévu. Etant donné
          qu'elles sont souvent sans heure, on leur attribue un créneau fictif pour les rendre
          visibles dans les vues semaine/jour.
        </span>
      </div>

      <!-- Message si aucun event -->
      <v-alert
        v-if="!loading && currentEvents.length === 0"
        type="info"
        variant="tonal"
        class="mt-4"
      >
        Aucun événement à afficher
      </v-alert>
    </v-card>
  </v-container>
</template>

<script setup>
  import { ref, computed, onMounted, watch } from 'vue'
  import VueCal from 'vue-cal'
  import { API_BASE_URL } from '@/utils/constants'
  import { useApi } from '@/composables/useApi'
  import { useRouter, useRoute } from 'vue-router'
  import FormField from '@/components/Forms/inputType/FormField.vue'
  import FormSelect from '@/components/Forms/inputType/FormSelect.vue'
  import 'vue-cal/dist/vuecal.css'

  const api = useApi(API_BASE_URL)
  const router = useRouter()
  const route = useRoute()

  const currentView = ref('month')
  const dayStartTime = ref('07:00')
  const dayEndTime = ref('20:00')

  const DEFAULT_TIME_FROM = 7 * 60
  const DEFAULT_TIME_TO = 20 * 60
  const MAX_MINUTES_IN_DAY = 24 * 60

  const toMinutes = (timeValue) => {
    if (typeof timeValue !== 'string') {
      return null
    }

    const [hoursStr, minutesStr] = timeValue.split(':')
    const hours = Number(hoursStr)
    const minutes = Number(minutesStr)

    if (
      Number.isNaN(hours) ||
      Number.isNaN(minutes) ||
      hours < 0 ||
      hours > 23 ||
      minutes < 0 ||
      minutes > 59
    ) {
      return null
    }

    return hours * 60 + minutes
  }

  const calendarTimeFrom = computed(() => {
    return toMinutes(dayStartTime.value) ?? DEFAULT_TIME_FROM
  })

  const isTimeRangeInvalid = computed(() => {
    const start = toMinutes(dayStartTime.value)
    const end = toMinutes(dayEndTime.value)

    if (start === null || end === null) {
      return false
    }

    return end <= start
  })

  const calendarTimeTo = computed(() => {
    const end = toMinutes(dayEndTime.value)

    if (end === null) {
      return DEFAULT_TIME_TO
    }

    if (end <= calendarTimeFrom.value) {
      return Math.min(calendarTimeFrom.value + 30, MAX_MINUTES_IN_DAY)
    }

    return end
  })

  const entityColors = {
    technicien: new Map(),
    equipement: new Map(),
  }
  const COLORS = [
    '#E53935',
    '#8E24AA',
    '#1E88E5',
    '#00897B',
    '#F4511E',
    '#6D4C41',
    '#039BE5',
    '#43A047',
    '#FB8C00',
    '#3949AB',
    '#00ACC1',
    '#7CB342',
  ]

  const getColorForEntity = (entityType, entityId, fallback = '#1E88E5') => {
    if (!entityId && entityId !== 0) {
      return fallback
    }

    const registry = entityColors[entityType]
    if (!registry) {
      return fallback
    }

    if (!registry.has(entityId)) {
      registry.set(entityId, COLORS[registry.size % COLORS.length])
    }

    return registry.get(entityId)
  }

  /**
   * Mode actif
   */
  const mode = ref('bt')

  /**
   * Donnees
   */
  const eventsBT = ref([])
  const eventsMaintenance = ref([])

  /**
   * Cache (evite re-fetch)
   */
  const loadedBT = ref(false)
  const loadedMaintenance = ref(false)
  const loadedTechniciens = ref(false)

  /**
   * Loading
   */
  const loading = ref(false)

  /**
   * Filtre générique : retourne les événements correspondant à un équipement donné.
   * Réutilisable pour tous les types d'événements (BT, maintenance).
   */
  const filterByEquipement = (events, equipementId) => {
    if (!equipementId) return events
    return events.filter((e) => Number(e.equipement_id) === Number(equipementId))
  }

  const getFilteredMaintenanceEvents = (equipmentId) => {
    return filterByEquipement(eventsMaintenance.value, equipmentId)
  }

  const getFilteredBTEvents = (technicienId) => {
    if (!technicienId) {
      return eventsBT.value
    }
    return eventsBT.value.filter((event) =>
      (event.techniciens || []).some((technicien) => Number(technicien.id) === Number(technicienId))
    )
  }

  const buildFakeMaintenanceTimeline = (events) => {
    const MAX_EVENTS_PER_SLOT = 2
    const START_HOUR = 8
    const SLOT_DURATION_HOURS = 1

    const eventsByDay = new Map()
    events.forEach((event) => {
      const dayKey = String(event.start || '').substring(0, 10)
      if (!dayKey) {
        return
      }

      if (!eventsByDay.has(dayKey)) {
        eventsByDay.set(dayKey, [])
      }

      eventsByDay.get(dayKey).push(event)
    })

    const timelineEvents = []

    eventsByDay.forEach((dayEvents, dayKey) => {
      dayEvents.forEach((event, index) => {
        const slotIndex = Math.floor(index / MAX_EVENTS_PER_SLOT)
        const slotStartHour = START_HOUR + slotIndex * SLOT_DURATION_HOURS
        const slotEndHour = slotStartHour + SLOT_DURATION_HOURS

        timelineEvents.push({
          ...event,
          start: `${dayKey} ${String(slotStartHour).padStart(2, '0')}:00`,
          end: `${dayKey} ${String(slotEndHour).padStart(2, '0')}:00`,
        })
      })
    })

    return timelineEvents
  }

  const fetchBT = async () => {
    loading.value = true
    try {
      const res = await api.get('bons-travail/calendar/')
      const data = res.data ?? res

      eventsBT.value = (data || []).map((e) => {
        const start = e.start || e.date_prevue
        const end =
          e.end && e.end !== e.start ? e.end : new Date(new Date(start).getTime() + 60 * 60 * 1000)
        const firstTechId = e.techniciens?.[0]?.id ?? null
        const color = getColorForEntity('technicien', firstTechId, '#E53935')

        // Log pour vérifier la couleur
        console.log(`BT ${e.id} - Tech: ${e.techniciens?.[0]?.nom || 'Aucun'}, Color: ${color}`)

        return {
          id: e.id,
          title: e.nom || 'BT',
          start: toVueCalDate(start),
          end: toVueCalDate(end),
          equipement: e.equipement
            ? {
                id: e.equipement.id,
                nom: e.equipement.nom,
              }
            : null,
          equipement_id: e.equipement?.id ?? null,
          techniciens: (e.techniciens || []).map((t) => ({
            id: t.id,
            nom: t.nom,
          })),
          class: 'event-bt',
          route: { name: 'InterventionDetail', params: { id: e.id } },
          backgroundColor: color, // Cette propriété doit être utilisée
          color: '#fff',
        }
      })

      loadedBT.value = true
    } catch (e) {
      console.error('Erreur BT', e)
      eventsBT.value = []
    } finally {
      loading.value = false
    }
  }

  const techniciensOptions = ref([])
  const fetchTechniciens = async () => {
    try {
      const res = await api.get('utilisateurs/techniciens/')
      const data = res.data ?? res ?? []

      techniciensOptions.value = (data || []).map((t) => {
        const fullName = `${t.prenom || ''} ${t.nomFamille || ''}`.trim()

        return {
          id: t.id,
          nom: fullName || t.nom || t.username || t.email || `Technicien ${t.id}`,
        }
      })

      loadedTechniciens.value = true
    } catch (e) {
      console.error('Erreur Techniciens', e)
      techniciensOptions.value = []
    }
  }

  /**
   * API Maintenance
   */
  const fetchMaintenance = async () => {
    loading.value = true
    try {
      const res = await api.get('maintenance/')
      const data = res ?? []

      eventsMaintenance.value = (data || [])
        .map((e) => {
          const dateMaintenance = e.prochaineMaintenance

          if (!dateMaintenance) {
            return null
          }

          const maintenanceDate = dateFromOrdinal(dateMaintenance)
          const dateOnly = toDateOnlyString(maintenanceDate)
          if (!dateOnly) {
            return null
          }

          // Les dates de maintenance sont souvent sans heure: on force un créneau visible
          // dans la plage 07:00 -> 20:00 de VueCal pour les vues semaine/jour.
          const start = `${dateOnly} 08:00`
          const end = `${dateOnly} 09:00`
          const uniqueId = `${e.id ?? e.planMaintenance?.id ?? e.equipement?.id}-${dateMaintenance}`
          const equipementId = e.equipement?.id ?? null
          const equipmentColor = getColorForEntity('equipement', equipementId, '#1E88E5')

          return {
            id: uniqueId,
            title: e.planMaintenance.nom,
            start,
            end,
            equipement: {
              id: e.equipement.id,
              nom: e.equipement.designation,
            },
            equipement_id: e.equipement.id,
            class: 'event-mp',
            route: { name: 'CounterDetail', params: { id: e.compteur.id } },
            backgroundColor: equipmentColor,
            color: '#fff',
          }
        })
        .filter(Boolean)

      loadedMaintenance.value = true
    } catch (e) {
      console.error('Erreur Maintenance', e)
      eventsMaintenance.value = []
    } finally {
      loading.value = false
    }
  }

  const dateFromOrdinal = (ordinal) => {
    if (!ordinal && ordinal !== 0) return null

    const ORDINAL_EPOCH = 719162 // 1970-01-01
    const daysFromEpoch = ordinal - ORDINAL_EPOCH
    const date = new Date(Date.UTC(1970, 0, 1 + daysFromEpoch))

    return date
  }

  const toDateOnlyString = (value) => {
    if (!(value instanceof Date) || Number.isNaN(value.getTime())) {
      return null
    }

    const year = value.getUTCFullYear()
    const month = String(value.getUTCMonth() + 1).padStart(2, '0')
    const day = String(value.getUTCDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  /**
   * API Equipements (pour filtre)
   */
  const equipmentSelected = ref(null)
  const equipmentsOptions = ref([])
  const technicienSelected = ref(null)

  const normalizeEquipments = (payload) => {
    const rawItems = payload?.results ?? payload?.data?.results ?? payload?.data ?? payload ?? []
    const list = Array.isArray(rawItems) ? rawItems : []

    return list.map((e) => ({
      id: e.id,
      nom: e.designation,
    }))
  }

  const ensureSelectedEquipmentOption = async (equipmentId) => {
    if (equipmentId === null || equipmentId === undefined || equipmentId === '') {
      return
    }

    const parsedId = Number(equipmentId)
    if (Number.isNaN(parsedId)) {
      return
    }

    const alreadyPresent = equipmentsOptions.value.some((e) => Number(e.id) === parsedId)
    if (alreadyPresent) {
      return
    }

    try {
      const equipment = await api.get(`equipements/${parsedId}/`)
      if (!equipment || equipment.id === undefined || equipment.id === null) {
        return
      }

      equipmentsOptions.value.push({
        id: equipment.id,
        nom: equipment.designation || `Équipement ${equipment.id}`,
      })
    } catch (e) {
      console.error('Erreur chargement équipement sélectionné', e)
    }
  }

  const fetchEquipments = async () => {
    try {
      const res = await api.get('equipements/')
      equipmentsOptions.value = normalizeEquipments(res)
    } catch (e) {
      console.error('Erreur Equipements', e)
      equipmentsOptions.value = []
    }
  }

  /**
   * Chargement intelligent
   */
  const loadDataIfNeeded = async () => {
    if (mode.value === 'bt' && !loadedBT.value) {
      console.log('BT')
      await fetchBT()
    }

    // Précharge techniciens et équipements pour les filtres BT.
    if (mode.value === 'bt' && !loadedTechniciens.value) {
      await fetchTechniciens()
    }

    if (mode.value === 'bt' && equipmentsOptions.value.length === 0) {
      await fetchEquipments()
    }

    if (mode.value === 'maintenance' && !loadedMaintenance.value) {
      console.log('Maintenance')
      await fetchMaintenance()
      await fetchEquipments()
    }
  }

  /**
   * Changement d’onglet
   */
  const handleNewMode = async () => {
    await loadDataIfNeeded()
  }

  const initializeCalendarFromRoute = async () => {
    const routeMode = String(route.query.mode || '').toLowerCase()
    const routeEquipmentId = route.query.equipmentId ?? route.query.equipementId ?? null

    if (routeMode === 'maintenance' || routeEquipmentId) {
      mode.value = 'maintenance'
    }

    await loadDataIfNeeded()

    if (
      mode.value === 'maintenance' &&
      routeEquipmentId !== null &&
      routeEquipmentId !== undefined &&
      routeEquipmentId !== ''
    ) {
      await ensureSelectedEquipmentOption(routeEquipmentId)
      equipmentSelected.value = Number(routeEquipmentId)
    }
  }

  /**
   * Events affiches
   */
  const currentEvents = computed(() => {
    if (mode.value === 'bt') {
      const byTechnicien = getFilteredBTEvents(technicienSelected.value)
      return filterByEquipement(byTechnicien, equipmentSelected.value)
    }

    const maintenanceEvents = getFilteredMaintenanceEvents(equipmentSelected.value)
    return buildFakeMaintenanceTimeline(maintenanceEvents)
  })

  watch(equipmentSelected, (selectedEquipmentId) => {
    if (mode.value !== 'maintenance') {
      return
    }

    const filteredEvents = getFilteredMaintenanceEvents(selectedEquipmentId)
    if (!selectedEquipmentId) {
      console.log(
        `[Maintenance] Aucun filtre équipement. ${filteredEvents.length} événement(s) affiché(s).`,
        filteredEvents
      )
      return
    }

    const selectedEquipment = equipmentsOptions.value.find(
      (e) => Number(e.id) === Number(selectedEquipmentId)
    )
    console.log(
      `[Maintenance] Filtre équipement: ${selectedEquipment?.nom || selectedEquipmentId}. ${filteredEvents.length} événement(s) trouvé(s).`,
      filteredEvents
    )
  })

  /**
   * Click event
   */
  const onEventClick = (event, e) => {
    e.stopPropagation()
    if (event.route) {
      console.log('Navigating to:', event.route)
      router.push(event.route).catch((err) => {
        console.error('Navigation error:', err)
      })
    }
  }

  const PARIS_TZ = 'Europe/Paris'

  const formatAsParisDate = (date) => {
    if (!(date instanceof Date) || Number.isNaN(date.getTime())) return null
    const parts = new Intl.DateTimeFormat('fr-FR', {
      timeZone: PARIS_TZ,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).formatToParts(date)
    const get = (type) => parts.find((p) => p.type === type)?.value ?? '00'
    return `${get('year')}-${get('month')}-${get('day')} ${get('hour')}:${get('minute')}`
  }

  const toVueCalDate = (value) => {
    if (!value) return null

    if (value instanceof Date) {
      return formatAsParisDate(value)
    }

    if (typeof value === 'string') {
      const trimmed = value.trim()
      if (!trimmed) return null

      if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) return `${trimmed} 00:00`

      // Date avec fuseau horaire (Z, +01:00, etc.) → convertir en heure de Paris
      if (/([zZ]|[+-]\d{2}:\d{2})$/.test(trimmed)) {
        return formatAsParisDate(new Date(trimmed))
      }

      // Date naïve avec T (ex: "2026-04-28T14:30:00") → supposée déjà en heure de Paris
      if (trimmed.includes('T')) return trimmed.replace('T', ' ').substring(0, 16)
      if (value.length === 10) return `${value} 00:00`
      return trimmed.substring(0, 16)
    }

    return null
  }

  /**
   * Initialisation
   */
  onMounted(() => {
    initializeCalendarFromRoute()
  })
</script>

<style scoped>
  .calendar-container {
    background: rgb(var(--v-theme-background)) !important;
    min-height: 100vh;
  }

  .calendar-wrapper {
    background: rgb(var(--v-theme-surface));
    border-radius: 12px;
    overflow: hidden;
  }

  /* ─── Variables de base ─────────────────────────────────────── */
  :deep(.vuecal--custom) {
    /* Couleurs remapées sur les tokens Vuetify */
    --vc-primary: rgb(var(--v-theme-primary));
    --vc-surface: rgb(var(--v-theme-surface));
    --vc-on-surface: rgb(var(--v-theme-on-surface));
    --vc-border: rgba(var(--v-border-color), var(--v-border-opacity));

    font-family: 'Roboto', sans-serif;
    background: var(--vc-surface);
    border: none;
    height: auto;
    min-height: 600px;
  }

  /* Supprime la scrollbar interne de VueCal */
  :deep(.vuecal--custom .vuecal__bg) {
    overflow-y: hidden !important;
  }

  /* ─── En-têtes jours ────────────────────────────────────────── */
  :deep(.vuecal--custom .vuecal__heading) {
    background: var(--vc-primary);
    color: rgb(var(--v-theme-on-primary));
    font-weight: 600;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 12px 0;
    border: none;
  }

  /* ─── Titre mois / période ──────────────────────────────────── */
  :deep(.vuecal--custom .vuecal__title) {
    color: var(--vc-on-surface);
    font-size: 1.4rem;
    font-weight: 500;
    text-transform: capitalize;
    background: none;
    border: none;
  }

  :deep(.vuecal--custom .vuecal__title-bar) {
    background: var(--vc-surface);
    border-bottom: 1px solid var(--vc-border);
    padding: 12px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  /* ─── Boutons navigation ────────────────────────────────────── */
  :deep(.vuecal--custom .vuecal__arrow),
  :deep(.vuecal--custom .vuecal__today-btn),
  :deep(.vuecal--custom .vuecal__view-btn) {
    background: var(--vc-primary);
    color: rgb(var(--v-theme-on-primary));
    border: none;
    border-radius: 8px;
    margin: 0 4px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 0.85rem;
    cursor: pointer;
    transition:
      filter 0.15s ease,
      transform 0.15s ease;
  }

  :deep(.vuecal--custom .vuecal__arrow:hover),
  :deep(.vuecal--custom .vuecal__today-btn:hover),
  :deep(.vuecal--custom .vuecal__view-btn:hover) {
    filter: brightness(1.12);
    transform: translateY(-1px);
  }

  :deep(.vuecal--custom .vuecal__view-btn--active) {
    filter: brightness(0.85);
  }

  /* ─── Cellules de jours ─────────────────────────────────────── */
  :deep(.vuecal--custom .vuecal__cell) {
    border: 1px solid var(--vc-border);
    background: var(--vc-surface);
    transition: background-color 0.15s ease;
    min-height: 80px;
  }

  :deep(.vuecal--custom .vuecal__cell:hover) {
    background: rgba(var(--v-theme-primary), 0.04);
  }

  /* Week-end */
  :deep(.vuecal--custom .vuecal__cell--weekend) {
    background: rgba(var(--v-theme-on-surface), 0.02);
  }

  /* Jour actuel */
  :deep(.vuecal--custom .vuecal__cell--today) {
    background: rgba(var(--v-theme-primary), 0.08) !important;
  }

  :deep(.vuecal--custom .vuecal__cell-date .today) {
    background: var(--vc-primary);
    color: rgb(var(--v-theme-on-primary));
    border-radius: 50%;
    width: 28px;
    height: 28px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
  }

  /* Jours hors mois courant */
  :deep(.vuecal--custom .vuecal__cell--out-of-scope) {
    opacity: 0.45;
  }

  /* Numéros de jours */
  :deep(.vuecal--custom .vuecal__cell-date) {
    color: var(--vc-on-surface);
    font-weight: 500;
    font-size: 0.9rem;
    padding: 6px 8px;
  }

  /* ─── Événements ────────────────────────────────────────────── */
  :deep(.vuecal--custom .vuecal__event) {
    border-radius: 6px;
    padding: 0px;
    margin: 2px 3px;
    font-size: 0.8rem;
    font-weight: 500;
    border: none;
    cursor: pointer;
    transition:
      transform 0.15s ease,
      filter 0.15s ease;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
    line-height: 1.4;
  }

  .event-inner {
    width: 100%;
    height: 100%;
    min-height: 100%;
    display: flex;
    align-items: center;
    border-radius: 6px;
    padding: 2px 6px;
    box-sizing: border-box;
  }

  .event-content {
    width: 100%;
  }

  :deep(.vuecal--custom .vuecal__event:hover) {
    transform: translateY(-1px);
    filter: brightness(1.08);
  }

  :deep(.vuecal--custom .vuecal__event-title) {
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  :deep(.vuecal--custom .vuecal__event-time) {
    font-size: 0.75rem;
    opacity: 0.85;
    margin-right: 4px;
  }

  /* ─── Slots horaires (vue semaine/jour) ─────────────────────── */
  :deep(.vuecal--custom .vuecal__time-cell) {
    color: var(--vc-on-surface);
    font-size: 0.8rem;
    font-weight: 500;
    border-right: 1px solid var(--vc-border);
  }

  :deep(.vuecal--custom .vuecal__time-cell-line) {
    border-color: var(--vc-border);
  }

  /* Indicateur "maintenant" */
  :deep(.vuecal--custom .vuecal__now-line) {
    border-color: var(--vc-primary);
    border-width: 2px;
  }

  /* ─── Responsive ─────────────────────────────────────────────── */
  @media (max-width: 768px) {
    :deep(.vuecal--custom .vuecal__title-bar) {
      flex-wrap: wrap;
      gap: 8px;
      padding: 8px 10px;
    }

    :deep(.vuecal--custom .vuecal__title) {
      font-size: 1.1rem;
    }

    :deep(.vuecal--custom .vuecal__arrow),
    :deep(.vuecal--custom .vuecal__today-btn),
    :deep(.vuecal--custom .vuecal__view-btn) {
      padding: 4px 10px;
      font-size: 0.8rem;
    }

    :deep(.vuecal--custom .vuecal__event) {
      font-size: 0.72rem;
      padding: 2px 4px;
    }

    :deep(.vuecal--custom .vuecal__cell) {
      min-height: 56px;
    }
  }
</style>
