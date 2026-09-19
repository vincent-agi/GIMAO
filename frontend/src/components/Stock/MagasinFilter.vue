<template>
  <div class="magasin-filter">
    <v-row dense>
      <!-- Tous les magasins -->
      <v-col cols="12" sm="6" md="6">
        <div
          class="magasin-item"
          :class="{ 'magasin-item--selected': selectedMagasin === null }"
          @click="handleSelectMagasin(null)"
        >
          <v-icon size="20" color="primary" class="mr-3">mdi-view-grid</v-icon>
          <div class="magasin-item__content">
            <span class="magasin-item__name">Tous les magasins</span>
            <span class="magasin-item__count">{{ totalCount }} consommables</span>
          </div>
          <v-icon v-if="selectedMagasin === null" color="primary" size="18"> mdi-check </v-icon>
        </div>
      </v-col>

      <!-- Chaque magasin -->
      <v-col v-for="magasin in magasins" :key="magasin.id" cols="12" sm="6" md="6">
        <div
          class="magasin-item"
          :class="{ 'magasin-item--selected': selectedMagasin === magasin.id }"
        >
          <div class="magasin-item-select" @click="handleSelectMagasin(magasin.id)">
            <v-icon size="20" :color="magasin.estMobile ? 'warning' : 'primary'" class="mr-3">
              {{ magasin.estMobile ? 'mdi-truck' : 'mdi-warehouse' }}
            </v-icon>
            <div class="magasin-item__content">
              <span class="magasin-item__name">{{ magasin.nom }}</span>
              <span class="magasin-item__count">
                {{ getConsommableCountByMagasin(magasin.id) }} consommables
              </span>
            </div>
            <v-icon v-if="selectedMagasin === magasin.id" color="primary" size="18">
              mdi-check
            </v-icon>
          </div>
          <div class="magasin-item-actions">
            <v-btn
              v-if="magasin && !magasin.archive && store.getters.hasPermission('mag:archive')"
              icon
              size="x-small"
              variant="text"
              color="warning"
              class="magasin-item-archive"
              @click.stop="handleArchiveMagasin(magasin)"
            >
              <v-icon size="16">mdi-archive-outline</v-icon>
              <v-tooltip activator="parent" location="top">Archiver</v-tooltip>
            </v-btn>
            <v-btn
              icon
              size="x-small"
              variant="text"
              color="primary"
              class="magasin-item-edit"
              @click.stop="handleEditMagasin(magasin)"
            >
              <v-icon size="16">mdi-pencil</v-icon>
              <v-tooltip activator="parent" location="top">Modifier</v-tooltip>
            </v-btn>
          </div>
        </div>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
  import { computed } from 'vue'
  import { useStore } from 'vuex'

  const store = useStore()

  const props = defineProps({
    magasins: {
      type: Array,
      default: () => [],
    },
    consommables: {
      type: Array,
      default: () => [],
    },
    selectedMagasin: {
      type: Number,
      default: null,
    },
  })

  const emit = defineEmits(['update:selectedMagasin', 'edit:magasin', 'archive:magasin'])

  const totalCount = computed(() => props.consommables.length)

  const getConsommableCountByMagasin = (magasinId) => {
    return props.consommables.filter(
      (c) => Array.isArray(c.stocks) && c.stocks.some((s) => s.magasin === magasinId)
    ).length
  }

  const handleSelectMagasin = (magasinId) => {
    emit('update:selectedMagasin', magasinId)
  }

  const handleEditMagasin = (magasin) => {
    emit('edit:magasin', magasin)
  }

  const handleArchiveMagasin = (magasin) => {
    emit('archive:magasin', magasin)
  }
</script>

<style scoped>
  .magasin-item {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    border-radius: 8px;
    border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
    background: rgb(var(--v-theme-surface));
    transition: all 0.15s ease;
    gap: 8px;
  }

  .magasin-item:hover {
    border-color: rgba(var(--v-theme-primary), 0.4);
    background: rgba(var(--v-theme-primary), 0.06);
  }

  .magasin-item--selected {
    border-color: rgb(var(--v-theme-primary));
    background: rgba(var(--v-theme-primary), 0.12);
  }

  .magasin-item-select {
    display: flex;
    align-items: center;
    flex: 1;
    cursor: pointer;
    min-width: 0;
  }

  .magasin-item__content {
    flex: 1;
    min-width: 0;
  }

  .magasin-item__name {
    display: block;
    font-size: 0.875rem;
    font-weight: 500;
    color: rgba(var(--v-theme-on-surface), 0.92);
  }

  .magasin-item__count {
    display: block;
    font-size: 0.75rem;
    color: rgba(var(--v-theme-on-surface), 0.68);
    margin-top: 2px;
  }

  .magasin-item-actions {
    display: flex;
    align-items: center;
    gap: 2px;
    flex-shrink: 0;
  }
</style>
