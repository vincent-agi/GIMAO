<template>
  <v-alert
    v-if="message"
    :type="type"
    :class="alertClass"
    :closable="dismissible"
    @click:close="handleClose"
  >
    {{ message }}
  </v-alert>
</template>

<script setup>
  import { defineProps } from 'vue'

  defineProps({
    message: {
      type: String,
      default: '',
    },
    type: {
      type: String,
      default: 'info',
      validator: (value) => ['success', 'info', 'warning', 'error'].includes(value),
    },
    dismissible: {
      type: Boolean,
      default: false,
    },
    alertClass: {
      type: String,
      default: 'mb-4',
    },
  })

  const emit = defineEmits(['close'])

  const handleClose = () => {
    emit('close')
  }
</script>

<style scoped>
  .v-alert {
    margin-bottom: 16px;
  }
</style>
