<template>
  <v-btn
    v-if="visible"
    :color="color"
    :size="size"
    :icon="iconOnly"
    class="floating-create-button"
    :elevation="elevation"
    @click="$emit('click')"
  >
    <v-icon :size="iconSize">{{ icon }}</v-icon>
    <v-tooltip activator="parent" location="left">
      {{ tooltip }}
    </v-tooltip>
  </v-btn>
</template>

<script setup>
  defineProps({
    visible: {
      type: Boolean,
      default: true,
    },
    tooltip: {
      type: String,
      default: '',
    },
    icon: {
      type: String,
      default: 'mdi-plus',
    },
    color: {
      type: String,
      default: 'primary',
    },
    size: {
      type: String,
      default: 'large',
    },
    iconSize: {
      type: String,
      default: 'large',
    },
    elevation: {
      type: [Number, String],
      default: 4,
    },
    iconOnly: {
      type: Boolean,
      default: true,
    },
  })

  defineEmits(['click'])
</script>

<style scoped>
  .floating-create-button {
    position: fixed !important;
    right: 24px;
    bottom: 24px;
    z-index: 100;
  }

  .floating-create-button:hover {
    transform: scale(1.1);
    transition: transform 0.2s ease;
  }
</style>
