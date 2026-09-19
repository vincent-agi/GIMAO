<template>
  <div>
    <v-row align="center" class="mb-2" justify="space-between">
      <v-col v-if="showTitle" cols="auto">
        <h3 class="mb-0">Sélectionner un lieu</h3>
      </v-col>
      <v-col v-if="showCreateButton" cols="auto">
        <v-btn color="primary" @click="createWithoutParent">
          <v-icon left>mdi-plus</v-icon>
          Créer un nouveau lieu
        </v-btn>
      </v-col>
    </v-row>

    <p v-if="!items || items.length === 0" class="text-caption">Pas de données disponibles.</p>

    <VTreeview
      v-else
      v-model:opened="openNodes"
      :items="processedItems"
      item-value="id"
      item-title="nomLieu"
      activatable
      hoverable
      rounded
      density="compact"
    >
      <!-- Checkbox après la flèche par défaut -->
      <template #prepend="{ item }">
        <v-checkbox
          :model-value="isSelected(item)"
          density="compact"
          hide-details
          :disabled="isLocked && !isSelected(item)"
          :style="{ marginLeft: !item.children ? '28px' : '0' }"
          @update:model-value="() => onSelect(item)"
        />
      </template>

      <!-- Titre avec marge à droite -->
      <template #title="{ item }">
        <span class="mr-5">{{ item.nomLieu }}</span>
      </template>

      <!-- Boutons modifier + ajouter à droite -->
      <template #append="{ item }">
        <v-btn
          v-if="showEditButton"
          icon
          color="primary"
          variant="text"
          size="x-small"
          class="mr-1"
          @click.stop="onEdit(item)"
        >
          <v-icon size="18">mdi-pencil</v-icon>
        </v-btn>
        <v-btn
          v-if="showCreateButton"
          icon
          color="primary"
          size="x-small"
          @click.stop="onCreate(item)"
        >
          <v-icon size="18">mdi-plus</v-icon>
        </v-btn>
      </template>
    </VTreeview>

    <!-- Chip avec le lieu -->
    <v-chip
      v-if="selected"
      color="primary"
      class="mt-2"
      closable
      @click:close="emit('update:selected', null)"
    >
      Lieu sélectionné : {{ selectedName }}
    </v-chip>
  </div>
</template>

<script setup>
  import { computed, ref, watch } from 'vue'
  import { VTreeview } from 'vuetify/labs/components'

  const props = defineProps({
    items: { type: Array, default: () => [] },
    selected: { type: [Object, Number, String], default: null },
    lockSelection: { type: Boolean, default: false },
    showTitle: { type: Boolean, default: true },
    showCreateButton: { type: Boolean, default: false },
    showEditButton: { type: Boolean, default: false },
  })

  const emit = defineEmits(['update:selected', 'create', 'edit'])

  const onEdit = (item) => emit('edit', item)

  const cleanItems = (nodes) => {
    if (!nodes) return []
    return nodes.map((node) => {
      const newNode = { ...node }
      if (newNode.children && newNode.children.length > 0) {
        newNode.children = cleanItems(newNode.children)
      } else {
        delete newNode.children
      }
      return newNode
    })
  }

  const processedItems = computed(() => cleanItems(props.items))

  const openNodes = ref([])

  // Retrieve path to a node to expand the tree
  const getPathToNode = (nodes, targetId, currentPath = []) => {
    if (!nodes) return null
    for (const node of nodes) {
      if (node.id == targetId) {
        return currentPath
      }
      if (node.children && node.children.length > 0) {
        const result = getPathToNode(node.children, targetId, [...currentPath, node.id])
        if (result) return result
      }
    }
    return null
  }

  // Watch selected to expand tree
  watch(
    [() => props.selected, () => props.items],
    () => {
      if (!props.selected || !props.items) return

      const targetId = typeof props.selected === 'object' ? props.selected.id : props.selected
      console.log('LocationTreeView: targetId for expansion:', targetId)

      if (!targetId) return

      const path = getPathToNode(props.items, targetId)
      console.log('LocationTreeView: found path:', path)

      if (path) {
        // Add path ids to openNodes if not already present
        const newOpen = new Set([...openNodes.value, ...path])
        openNodes.value = Array.from(newOpen)
        console.log('LocationTreeView: new openNodes:', openNodes.value)
      }
    },
    { immediate: true, deep: true }
  )

  // Détecte si sélection bloquée
  const isLocked = computed(() => props.lockSelection && props.selected !== null)

  // Détecte si un item est celui sélectionné
  const isSelected = (item) => {
    if (!props.selected) return false
    const selectedId = typeof props.selected === 'object' ? props.selected.id : props.selected
    return selectedId == item.id
  }

  // Sélection via checkbox
  const onSelect = (item) => {
    if (isLocked.value && !isSelected(item)) return // sélection bloquée

    emit('update:selected', isSelected(item) ? null : item)
  }

  // Transmission de l’événement de création
  const onCreate = (item) => {
    console.log('Create location under parent:', item) // Debug
    emit('create', item.id)
  }

  const createWithoutParent = () => {
    emit('create', null)
  }

  const findNodeById = (nodes, id) => {
    if (!nodes) return null
    for (const node of nodes) {
      if (node.id == id) return node
      if (node.children && node.children.length > 0) {
        const found = findNodeById(node.children, id)
        if (found) return found
      }
    }
    return null
  }

  const selectedName = computed(() => {
    if (!props.selected) return ''
    if (typeof props.selected === 'object') return props.selected.nomLieu

    const found = findNodeById(props.items, props.selected)
    return found ? found.nomLieu : props.selected
  })
</script>

<style scoped>
  /* S'assurer que tout est sur une seule ligne avec le bon espacement */
  :deep(.v-treeview-item__content) {
    display: flex !important;
    align-items: center !important;
    width: 100% !important;
    gap: 8px !important;
  }

  :deep(.v-treeview-item__prepend) {
    display: flex;
    align-items: center;
    gap: 4px;
    flex-shrink: 0;
  }

  :deep(.v-treeview-item__label) {
    flex: 1 !important;
    display: flex;
    align-items: center;
    min-width: 0;
  }

  :deep(.v-treeview-item__append) {
    margin-left: auto !important;
    display: flex;
    align-items: center;
    flex-shrink: 0;
    padding-left: 24px !important;
  }
</style>
