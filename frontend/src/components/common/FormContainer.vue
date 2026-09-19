<template>
  <v-container :fluid="fluid" :class="containerClass">
    <v-row :justify="justify">
      <v-col :cols="cols" :md="md" :lg="lg" :xl="xl">
        <v-card :elevation="elevation" :class="cardClass">
          <v-card-title v-if="title" :class="titleClass">
            {{ title }}
          </v-card-title>

          <v-card-subtitle v-if="subtitle" :class="subtitleClass">
            {{ subtitle }}
          </v-card-subtitle>

          <v-card-text :class="contentClass">
            <slot></slot>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
  import { defineProps } from 'vue'

  defineProps({
    // Titre et sous-titre
    title: {
      type: String,
      default: '',
    },
    subtitle: {
      type: String,
      default: '',
    },

    // Responsive
    cols: {
      type: [String, Number],
      default: 12,
    },
    md: {
      type: [String, Number],
      default: 8,
    },
    lg: {
      type: [String, Number],
      default: 6,
    },
    xl: {
      type: [String, Number],
      default: 4,
    },

    // Layout
    justify: {
      type: String,
      default: 'center',
    },
    fluid: {
      type: Boolean,
      default: false,
    },

    // Styles
    elevation: {
      type: [String, Number],
      default: 2,
    },
    containerClass: {
      type: String,
      default: '',
    },
    cardClass: {
      type: String,
      default: '',
    },
    titleClass: {
      type: String,
      default: '',
    },
    subtitleClass: {
      type: String,
      default: '',
    },
    contentClass: {
      type: String,
      default: '',
    },
  })
</script>
