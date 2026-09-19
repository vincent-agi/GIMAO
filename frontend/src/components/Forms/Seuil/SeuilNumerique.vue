<template>
  <v-row dense align="end">
    <v-col cols="3">
      <FormField
        v-model="localSeuil.derniereIntervention"
        field-name="derniereIntervention"
        type="number"
        label="Dernière intervention"
        placeholder="0"
        min="0"
        :suffix="selectedUnite"
        @update:model-value="updateProchaineMaintenance"
      />
    </v-col>

    <v-col cols="3">
      <FormField
        v-model="localSeuil.ecartInterventions"
        field-name="ecartInterventions"
        type="number"
        label="Écart"
        placeholder="0"
        min="0"
        @update:model-value="updateProchaineMaintenance"
      />
    </v-col>

    <v-col cols="3">
      <v-select
        v-model="selectedUnite"
        :items="COUNTER_UNITS"
        item-title="title"
        item-value="value"
        label="Unité"
        variant="outlined"
        density="comfortable"
        hide-details
        @update:model-value="updateProchaineMaintenance"
      />
    </v-col>

    <v-col cols="3">
      <FormField
        :model-value="localSeuil.prochaineMaintenance"
        field-name="prochaineMaintenance"
        type="number"
        label="Prochaine maintenance"
        :suffix="selectedUnite"
        :readonly="true"
      />
    </v-col>
  </v-row>
</template>

<script setup>
  import { reactive, ref, watch } from 'vue'
  import { FormField } from '@/components/common'
  import { COUNTER_UNITS } from '@/utils/constants'

  const props = defineProps({
    modelValue: {
      type: Object,
      required: true,
    },
    estGlissant: {
      type: Boolean,
      default: false,
    },
    valeurCourante: {
      type: Number,
      default: null,
    },
    unite: {
      type: String,
      default: '',
    },
  })

  const emit = defineEmits(['update:modelValue'])

  const selectedUnite = ref(props.unite || 'heures')

  watch(
    () => props.unite,
    (val) => {
      if (val && !selectedUnite.value) selectedUnite.value = val
    },
    { immediate: true }
  )

  const toNumberOrNull = (value) => {
    if (value === null || value === undefined || value === '') {
      return null
    }
    const parsed = Number(value)
    return Number.isNaN(parsed) ? null : parsed
  }

  const localSeuil = reactive({
    derniereIntervention: props.modelValue.derniereIntervention ?? 0,
    ecartInterventions: props.modelValue.ecartInterventions ?? 0,
    prochaineMaintenance: props.modelValue.prochaineMaintenance ?? 0,
  })

  watch(
    () => props.modelValue,
    (val) => {
      localSeuil.derniereIntervention = val.derniereIntervention ?? 0
      localSeuil.ecartInterventions = val.ecartInterventions ?? 0
      localSeuil.prochaineMaintenance = val.prochaineMaintenance ?? 0
    },
    { deep: true }
  )

  const updateProchaineMaintenance = () => {
    const ecart = toNumberOrNull(localSeuil.ecartInterventions)
    const base = props.estGlissant
      ? toNumberOrNull(props.valeurCourante)
      : toNumberOrNull(localSeuil.derniereIntervention)

    if (base === null || ecart === null) {
      localSeuil.prochaineMaintenance = ''
    } else {
      localSeuil.prochaineMaintenance = base + ecart
    }

    emit('update:modelValue', {
      ...localSeuil,
      derniereIntervention: toNumberOrNull(localSeuil.derniereIntervention),
      ecartInterventions: toNumberOrNull(localSeuil.ecartInterventions),
      prochaineMaintenance: toNumberOrNull(localSeuil.prochaineMaintenance),
      unite: selectedUnite.value,
    })
  }

  watch(() => props.estGlissant, updateProchaineMaintenance)
</script>
