<template>
  <v-row>
    <v-col cols="6" md="3">
      <v-card
        elevation="1"
        class="rounded-lg pa-2 cursor-pointer stat-card stat-card--error"
        :class="{ 'selected-stat': selectedFilter === 'hors-stock' }"
        @click="handleFilterClick('hors-stock')"
      >
        <div class="d-flex align-center justify-space-between">
          <div>
            <p class="text-caption stat-card__label mb-0">Hors stock</p>
            <p class="text-h5 font-weight-bold text-error mb-0">{{ horsStockCount }}</p>
          </div>
          <v-icon size="32" color="error" class="opacity-50">mdi-alert-circle</v-icon>
        </div>
      </v-card>
    </v-col>
    <v-col cols="6" md="3">
      <v-card
        elevation="1"
        class="rounded-lg pa-2 cursor-pointer stat-card stat-card--warning"
        :class="{ 'selected-stat': selectedFilter === 'sous-seuil' }"
        @click="handleFilterClick('sous-seuil')"
      >
        <div class="d-flex align-center justify-space-between">
          <div>
            <p class="text-caption stat-card__label mb-0">Sous le seuil</p>
            <p class="text-h5 font-weight-bold text-warning mb-0">{{ sousSeuilCount }}</p>
          </div>
          <v-icon size="32" color="warning" class="opacity-50">mdi-alert</v-icon>
        </div>
      </v-card>
    </v-col>
    <v-col cols="6" md="3">
      <v-card
        elevation="1"
        class="rounded-lg pa-2 cursor-pointer stat-card stat-card--success"
        :class="{ 'selected-stat': selectedFilter === 'stock-suffisant' }"
        @click="handleFilterClick('stock-suffisant')"
      >
        <div class="d-flex align-center justify-space-between">
          <div>
            <p class="text-caption stat-card__label mb-0">Stock suffisant</p>
            <p class="text-h5 font-weight-bold text-success mb-0">{{ stockSuffisantCount }}</p>
          </div>
          <v-icon size="32" color="success" class="opacity-50">mdi-check-circle</v-icon>
        </div>
      </v-card>
    </v-col>
    <v-col cols="6" md="3">
      <v-card elevation="1" class="rounded-lg pa-2 stat-card stat-card--primary">
        <div class="d-flex align-center justify-space-between">
          <div>
            <p class="text-caption stat-card__label mb-0">BT en attente</p>
            <p class="text-h5 font-weight-bold text-primary mb-0">{{ btCount }}</p>
          </div>
          <v-icon size="32" color="primary" class="opacity-50">mdi-clipboard-list</v-icon>
        </div>
      </v-card>
    </v-col>
  </v-row>
</template>

<script setup>
  import { computed } from 'vue'

  const props = defineProps({
    consommables: {
      type: Array,
      default: () => [],
    },
    summary: {
      type: Object,
      default: () => null,
    },
    selectedFilter: {
      type: String,
      default: null,
    },
    btCount: {
      type: Number,
      default: 0,
    },
  })

  const emit = defineEmits(['filter-change'])

  // Statistiques de stock
  const horsStockCount = computed(() => {
    if (props.summary && Number.isFinite(Number(props.summary.hors_stock_count))) {
      return Number(props.summary.hors_stock_count)
    }
    return props.consommables.filter((c) => (c.quantite ?? c.quantite_totale ?? 0) === 0).length
  })

  const sousSeuilCount = computed(() => {
    if (props.summary && Number.isFinite(Number(props.summary.sous_seuil_count))) {
      return Number(props.summary.sous_seuil_count)
    }
    return props.consommables.filter((c) => {
      const quantite = c.quantite ?? c.quantite_totale ?? 0
      return quantite > 0 && c.seuilStockFaible !== null && quantite <= c.seuilStockFaible
    }).length
  })

  const stockSuffisantCount = computed(() => {
    if (props.summary && Number.isFinite(Number(props.summary.stock_suffisant_count))) {
      return Number(props.summary.stock_suffisant_count)
    }
    return props.consommables.filter((c) => {
      const quantite = c.quantite ?? c.quantite_totale ?? 0
      return c.seuilStockFaible === null || quantite > c.seuilStockFaible
    }).length
  })

  const handleFilterClick = (filterType) => {
    if (props.selectedFilter === filterType) {
      emit('filter-change', null)
    } else {
      emit('filter-change', filterType)
    }
  }
</script>

<style scoped>
  .opacity-50 {
    opacity: 0.5;
  }

  .cursor-pointer {
    cursor: pointer;
  }

  .stat-card {
    background: rgba(var(--v-theme-on-surface), 0.03);
    border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
    transition: all 0.2s ease-in-out;
  }

  .stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(var(--v-theme-on-surface), 0.12);
  }

  .stat-card__label {
    color: rgba(var(--v-theme-on-surface), 0.68);
    font-size: 0.7rem;
  }

  .stat-card--error {
    background: rgba(var(--v-theme-error), 0.1);
  }

  .stat-card--warning {
    background: rgba(var(--v-theme-warning), 0.1);
  }

  .stat-card--success {
    background: rgba(var(--v-theme-success), 0.1);
  }

  .stat-card--primary {
    background: rgba(var(--v-theme-primary), 0.1);
  }

  .selected-stat {
    border: 2px solid rgb(var(--v-theme-primary));
    box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.3);
  }
</style>
