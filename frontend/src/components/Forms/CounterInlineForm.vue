<template>
  <v-form @submit.prevent="handleSave">
    <v-row dense>
      <v-col cols="12" md="6">
        <FormField
          v-model="counterLocal.nomCompteur"
          field-name="nomCompteur"
          label="Nom du compteur"
          placeholder="Saisir le nom du compteur"
          counter="100"
        />
      </v-col>

      <v-col cols="12" md="6">
        <FormField
          v-model="counterLocal.valeurCourante"
          field-name="valeurCourante"
          :type="counterLocal.type === 'Calendaire' ? 'date' : 'number'"
          label="Valeur actuelle"
          placeholder="0"
          min="0"
        />
      </v-col>

      <v-col cols="12" md="6">
        <FormSelect
          v-if="showUniteSelect"
          v-model="counterLocal.unite"
          field-name="unite"
          label="Unité"
          :items="COUNTER_UNITS"
          item-title="title"
          item-value="value"
        />
      </v-col>

      <v-col v-if="!(isEditMode && counterLocal.type === 'Calendaire')" cols="12" md="6">
        <FormSelect
          v-model="counterLocal.type"
          field-name="type"
          label="Type de compteur"
          :items="counterTypeOptions"
        />
      </v-col>

      <v-col cols="12" md="6">
        <FormCheckbox
          v-model="counterLocal.estPrincipal"
          field-name="estPrincipal"
          label="Compteur principal"
        />
      </v-col>
    </v-row>

    <v-alert v-if="localError" type="error" class="mt-4">{{ localError }}</v-alert>

    <v-card-actions class="px-0 pt-4">
      <v-spacer />
      <v-btn variant="text" @click="handleCancel">Annuler</v-btn>
      <v-btn type="submit" color="primary" :disabled="!isValid">
        {{ isEditMode ? 'Modifier le compteur' : 'Ajouter le compteur' }}
      </v-btn>
    </v-card-actions>
  </v-form>
</template>

<script setup>
  import { computed, ref, watch } from 'vue'
  import { FormField, FormCheckbox, FormSelect } from '@/components/common'
  import { COUNTER_UNITS } from '@/utils/constants'

  const props = defineProps({
    modelValue: {
      type: Object,
      required: true,
    },
    isEditMode: {
      type: Boolean,
      default: false,
    },
    isFirstCounter: {
      type: Boolean,
      default: false,
    },
  })

  const emit = defineEmits(['update:modelValue', 'save', 'cancel'])

  const localError = ref('')

  const cloneCounter = (value) => {
    if (!value) return {}
    return JSON.parse(JSON.stringify(value))
  }

  // Copie locale: évite de modifier le parent tant que l'utilisateur n'a pas sauvegardé.
  const counterLocal = ref(cloneCounter(props.modelValue))

  watch(
    () => props.modelValue,
    (newValue) => {
      counterLocal.value = cloneCounter(newValue)
    },
    { deep: true, immediate: true }
  )

  // Affiche le select d'unité uniquement si ce n'est pas calendaire
  const showUniteSelect = computed(() => counterLocal.value.type !== 'Calendaire')
  const counterTypeOptions = [
    { title: 'Calendrier', value: 'Calendaire' },
    { title: 'Numérique', value: 'Numérique' },
  ]

  // Validation
  const isValid = computed(() => {
    if (counterLocal.value.type === 'Calendaire') {
      return counterLocal.value.nomCompteur?.trim()
    } else {
      return (
        counterLocal.value.nomCompteur?.trim() &&
        counterLocal.value.unite &&
        Number.isFinite(Number(counterLocal.value.valeurCourante))
      )
    }
  })

  // Gestion du type calendaire : met la date du jour automatiquement
  watch(
    () => counterLocal.value.type,
    (newType) => {
      if (newType === 'Calendaire') {
        let d

        if (!props.isEditMode) {
          console.log('Setting date to today')
          d = new Date()
        } else {
          const ORDINAL_EPOCH = 719162
          const daysFromEpoch = counterLocal.value.valeurCourante - ORDINAL_EPOCH
          d = new Date(Date.UTC(1970, 0, 1 + daysFromEpoch))
        }

        const yyyy = d.getFullYear()
        const mm = String(d.getMonth() + 1).padStart(2, '0')
        const dd = String(d.getDate()).padStart(2, '0')
        counterLocal.value.valeurCourante = `${yyyy}-${mm}-${dd}`
        counterLocal.value.unite = 'date'
        counterLocal.value.nomCompteur = 'Calendrier'
      } else {
        const n = Number(counterLocal.value.valeurCourante)
        if (!props.isEditMode && !counterLocal.value.unite) {
          counterLocal.value.unite = 'jours'
        }
        counterLocal.value.valeurCourante = Number.isFinite(n) ? n : 0
      }
    },
    { immediate: true }
  )

  const handleSave = () => {
    if (!isValid.value) {
      localError.value = 'Veuillez remplir tous les champs obligatoires'
      return
    }
    localError.value = ''
    const savedCounter = cloneCounter(counterLocal.value)
    emit('update:modelValue', savedCounter)
    emit('save', savedCounter)
    emit('cancel')
  }

  const handleCancel = () => {
    localError.value = ''
    emit('cancel')
  }
</script>
