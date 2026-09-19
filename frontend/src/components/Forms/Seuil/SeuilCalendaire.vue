<template>
  <v-row dense>
    <v-col cols="12" md="4">
      <FormField
        v-model="derniereIntervention"
        field-name="derniereIntervention"
        type="date"
        label="Dernière intervention"
        @update:model-value="onInputChange"
      />
    </v-col>

    <v-col cols="12" md="4">
      <v-row dense>
        <v-col cols="4">
          <FormField
            v-model="ecart"
            field-name="ecartInterventions"
            type="number"
            label="Écart"
            placeholder="0"
            min="0"
            @update:model-value="onInputChange"
          />
        </v-col>
        <v-col cols="8">
          <FormSelect
            v-model="unite"
            field-name="uniteIntervalle"
            label="Unité"
            :items="UNITES"
            item-title="label"
            item-value="value"
            @update:model-value="onInputChange"
          />
        </v-col>
      </v-row>
    </v-col>

    <v-col cols="12" md="4">
      <div>
        <label class="field-label">Prochaine maintenance</label>
        <v-text-field
          :key="prochaine"
          :model-value="prochaine"
          type="date"
          variant="outlined"
          density="comfortable"
          hide-details="auto"
          readonly
        />
      </div>
    </v-col>
  </v-row>
</template>

<script setup>
  import { ref, computed, watch } from 'vue'
  import { FormField, FormSelect } from '@/components/common'

  const UNITES = [
    { label: 'Heures', value: 'hours' },
    { label: 'Jours', value: 'days' },
    { label: 'Semaines', value: 'weeks' },
    { label: 'Mois', value: 'months' },
    { label: 'Années', value: 'years' },
  ]

  const props = defineProps({
    modelValue: { type: Object, required: true },
    estGlissant: { type: Boolean, default: false },
    valeurCourante: { type: [Number, String], default: null },
  })

  const emit = defineEmits(['update:modelValue'])

  // --- Utilitaires ---
  const toISO = (val) => {
    if (!val && val !== 0) return ''
    if (typeof val === 'number') {
      const EPOCH = 719162
      return new Date(Date.UTC(1970, 0, 1 + (val - EPOCH))).toISOString().split('T')[0]
    }
    return String(val)
  }

  const normalizeUnit = (u) => {
    const m = {
      hours: 'hours',
      days: 'days',
      weeks: 'weeks',
      months: 'months',
      years: 'years',
      heure: 'hours',
      heures: 'hours',
      jour: 'days',
      jours: 'days',
      semaine: 'weeks',
      semaines: 'weeks',
      mois: 'months',
      an: 'years',
      ans: 'years',
      annee: 'years',
      annees: 'years',
    }
    return m[String(u || '').toLowerCase()] || 'days'
  }

  const addToDate = (isoDate, n, unit) => {
    if (!isoDate || !n || !unit) return ''
    const base = new Date(isoDate)
    if (isNaN(base.getTime())) return ''
    const prochaine = new Date(base)
    switch (unit) {
      case 'hours':
        prochaine.setHours(prochaine.getHours() + n)
        break
      case 'days':
        prochaine.setDate(prochaine.getDate() + n)
        break
      case 'weeks':
        prochaine.setDate(prochaine.getDate() + n * 7)
        break
      case 'months':
        prochaine.setMonth(prochaine.getMonth() + n)
        break
      case 'years':
        prochaine.setFullYear(prochaine.getFullYear() + n)
        break
      default:
        return ''
    }
    return prochaine.toISOString().split('T')[0]
  }

  // --- État ---
  const derniereIntervention = ref('')
  const ecart = ref(0)
  const unite = ref('days')

  // --- Prochaine maintenance (computed) ---
  const prochaine = computed(() => {
    const n = Number(ecart.value) || 0
    const u = unite.value
    const base = props.estGlissant
      ? toISO(props.valeurCourante) || new Date().toISOString().split('T')[0]
      : derniereIntervention.value
    return addToDate(base, n, u)
  })

  // --- Emit vers le parent ---
  const emitValue = () => {
    const base = props.estGlissant
      ? toISO(props.valeurCourante) || new Date().toISOString().split('T')[0]
      : derniereIntervention.value
    const p = prochaine.value
    emit('update:modelValue', {
      derniereIntervention: derniereIntervention.value,
      prochaineMaintenance: p,
      ecartInterventions: p && base ? new Date(p).getTime() - new Date(base).getTime() : 0, // delta ms
      ecartCalendaire: Number(ecart.value) || 0,
      uniteCalendaire: unite.value,
    })
  }

  const onInputChange = () => emitValue()

  // --- Init depuis props.modelValue ---
  watch(
    () => props.modelValue,
    (val) => {
      if (!val) return
      derniereIntervention.value = toISO(val.derniereIntervention) || ''
      // Priorité : ecartCalendaire + uniteCalendaire explicites
      if (val.ecartCalendaire > 0) {
        ecart.value = Number(val.ecartCalendaire)
        unite.value = normalizeUnit(val.uniteCalendaire)
      } else if (val.ecartInterventions > 0) {
        const ms = Number(val.ecartInterventions)
        const days = Math.round(ms / 86400000)
        if (days < 1) {
          ecart.value = Math.round(ms / 3600000)
          unite.value = 'hours'
        } else if (days < 7) {
          ecart.value = days
          unite.value = 'days'
        } else if (days < 60) {
          ecart.value = Math.round(days / 7)
          unite.value = 'weeks'
        } else if (days < 365) {
          ecart.value = Math.round(days / 30)
          unite.value = 'months'
        } else {
          ecart.value = Math.round(days / 365)
          unite.value = 'years'
        }
      }
    },
    { immediate: true }
  )

  // --- Émet quand estGlissant change ---
  watch(
    () => props.estGlissant,
    () => emitValue()
  )
</script>

<style scoped>
  .field-label {
    display: block;
    margin-bottom: 4px;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-color);
  }
</style>
