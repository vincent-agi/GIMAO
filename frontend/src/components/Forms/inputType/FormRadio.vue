<template>
  <div>
    <label v-if="label" class="field-label">
      {{ label }} <span v-if="isRequired" class="required-star">*</span>
    </label>
    <v-radio-group v-bind="$attrs" :rules="fieldRules" hide-details="auto">
      <v-radio
        v-for="item in items"
        :key="getItemValue(item)"
        :label="getItemTitle(item)"
        :value="getItemValue(item)"
      />
    </v-radio-group>
  </div>
</template>

<script setup>
  import { computed, inject } from 'vue'

  defineOptions({
    inheritAttrs: false,
  })

  const props = defineProps({
    label: {
      type: String,
      default: '',
    },
    fieldName: {
      type: String,
      required: true,
    },
    step: {
      type: Number,
      default: null,
    },
    items: {
      type: Array,
      default: () => [],
    },
    itemTitle: {
      type: String,
      default: 'title',
    },
    itemValue: {
      type: String,
      default: 'value',
    },
  })

  // Injecter validation et isFieldRequired depuis le parent (BaseForm)
  const validation = inject('validation', null)
  const isFieldRequired = inject('isFieldRequired', null)

  // Vérifier si le champ est requis
  const isRequired = computed(() => {
    if (!isFieldRequired) return false
    return isFieldRequired(props.fieldName, props.step)
  })

  // Récupérer les règles de validation
  const fieldRules = computed(() => {
    if (!validation) return []
    return validation.getFieldRules(props.fieldName, props.step)
  })

  // Helpers pour extraire titre et valeur des items
  const getItemTitle = (item) => {
    if (typeof item === 'string') return item
    return item[props.itemTitle]
  }

  const getItemValue = (item) => {
    if (typeof item === 'string') return item
    return item[props.itemValue]
  }
</script>

<style scoped>
  .field-label {
    display: block;
    margin-bottom: 4px;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-color);
  }

  .required-star {
    color: #d32f2f;
    margin-left: 2px;
  }
</style>
