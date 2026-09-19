<template>
  <div class="pagination-bar" :class="{ 'pagination-bar--reserve-fab-space': reserveFabSpace }">
    <div class="pagination-bar__count">{{ totalItems }} {{ resolvedLabel }}</div>

    <div class="pagination-bar__controls">
      <div class="pagination-bar__page-info">
        Page {{ safePage }} sur {{ safePageCount }}
        <span class="pagination-bar__page-range"> • {{ rangeStart }}-{{ rangeEnd }} </span>
      </div>

      <v-select
        :model-value="pageSize"
        :items="pageSizeOptions"
        label="Par page"
        density="compact"
        variant="outlined"
        hide-details
        class="pagination-bar__page-size"
        @update:model-value="$emit('update:page-size', $event)"
      />

      <v-pagination
        :model-value="page"
        :length="pageCount"
        density="comfortable"
        rounded="circle"
        @update:model-value="$emit('update:page', $event)"
      />
    </div>
  </div>
</template>

<script setup>
  import { computed } from 'vue'

  const props = defineProps({
    page: {
      type: Number,
      required: true,
    },
    pageSize: {
      type: Number,
      required: true,
    },
    totalItems: {
      type: Number,
      default: 0,
    },
    pageCount: {
      type: Number,
      default: 1,
    },
    pageSizeOptions: {
      type: Array,
      default: () => [10, 25, 50, 100],
    },
    itemLabelSingular: {
      type: String,
      default: 'élément',
    },
    itemLabelPlural: {
      type: String,
      default: '',
    },
    reserveFabSpace: {
      type: Boolean,
      default: false,
    },
  })

  defineEmits(['update:page', 'update:page-size'])

  const resolvedLabel = computed(() => {
    if (props.totalItems === 1) {
      return props.itemLabelSingular
    }

    return props.itemLabelPlural || `${props.itemLabelSingular}s`
  })

  const safePage = computed(() => Math.max(1, Number(props.page || 1)))
  const safePageCount = computed(() => Math.max(1, Number(props.pageCount || 1)))
  const rangeStart = computed(() => {
    if (props.totalItems <= 0) return 0
    return (safePage.value - 1) * props.pageSize + 1
  })
  const rangeEnd = computed(() => {
    if (props.totalItems <= 0) return 0
    return Math.min(safePage.value * props.pageSize, props.totalItems)
  })
</script>

<style scoped>
  .pagination-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    padding: 16px 8px 0;
    flex-wrap: wrap;
  }

  .pagination-bar__count {
    color: #5f6368;
    font-size: 0.95rem;
  }

  .pagination-bar__controls {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }

  .pagination-bar__page-info {
    color: #5f6368;
    font-size: 0.95rem;
    white-space: nowrap;
  }

  .pagination-bar__page-range {
    color: #7b8088;
  }

  .pagination-bar__page-size {
    width: 120px;
  }

  .pagination-bar--reserve-fab-space {
    padding-bottom: 88px;
  }

  @media (max-width: 960px) {
    .pagination-bar--reserve-fab-space {
      padding-bottom: 96px;
    }
  }
</style>
