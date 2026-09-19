<template>
  <div>
    <label v-if="label" class="field-label">
      {{ label }} <span v-if="isRequired" class="required-star">*</span>
    </label>

    <v-autocomplete
      v-bind="$attrs"
      :rules="fieldRules"
      variant="outlined"
      density="comfortable"
      :disabled="disabled"
      hide-details="auto"
    >
      <!-- Slot personnalisé pour #no-data -->
      <template v-if="!$slots['no-data']" #no-data>
        <v-list-item>
          <v-list-item-title> Aucun élément trouvé </v-list-item-title>
        </v-list-item>
      </template>

      <!-- Forward de tous les autres slots -->
      <template v-for="(_, slot) in $slots" #[slot]="scope">
        <slot :name="slot" v-bind="scope || {}" />
      </template>
    </v-autocomplete>
  </div>
</template>

<script setup>
  import { computed, inject } from 'vue'

  const props = defineProps({
    label: { type: String, default: '' },
    fieldName: { type: String, required: true },
    step: { type: Number, default: null },
    disabled: { type: Boolean, default: false },
  })

  const validation = inject('validation', null)
  const isFieldRequired = inject('isFieldRequired', null)

  const isRequired = computed(() => {
    if (!isFieldRequired) return false
    return isFieldRequired(props.fieldName, props.step)
  })

  const fieldRules = computed(() => {
    if (!validation) return []
    return validation.getFieldRules(props.fieldName, props.step)
  })
</script>
