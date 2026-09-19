<template>
  <div class="zoom-image">
    <img :src="src" :alt="alt" class="preview" @click="dialog = true" />

    <v-dialog v-model="dialog" max-width="90%">
      <v-card>
        <v-card-title class="text-h6">
          {{ alt }}
        </v-card-title>

        <v-card-text class="d-flex justify-center">
          <v-img :src="src" :alt="alt" max-height="80vh" contain />
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="dialog = false"> Fermer </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
  import { ref } from 'vue'

  defineProps({
    src: { type: String, default: '' },
    alt: { type: String, default: '' },
  })

  const dialog = ref(false)
</script>

<style scoped>
  .preview {
    max-width: 100%;
    cursor: pointer;
    border-radius: 6px;
    transition: transform 0.2s;
  }

  .preview:hover {
    transform: scale(1.02);
  }
</style>
