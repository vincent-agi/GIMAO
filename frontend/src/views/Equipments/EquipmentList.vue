<template>
  <v-container fluid :style="containerStyle">
    <v-row>
      <!-- Sidebar gauche avec filtres -->
      <v-col cols="12" md="4" lg="3">
        <!-- Card: Structure des Lieux -->
        <v-card elevation="1" class="rounded-lg pa-2 mb-4">
          <v-card-title class="font-weight-bold text-uppercase text-primary text-body-2">
            Structure des Lieux
          </v-card-title>
          <v-divider></v-divider>
          <div class="pa-2">
            <p v-if="!locations || locations.length === 0" class="text-caption">
              Pas de données disponibles.
            </p>
            <VTreeview
              v-else
              v-model:selected="selectedTreeNodes"
              :items="locations"
              item-title="nomLieu"
              item-children="children"
              item-value="id"
              select-strategy="independent"
              selectable
              dense
              @update:selected="onSelectLocation"
            >
              <template #prepend="{ item, open }">
                <v-icon
                  v-if="item.children && item.children.length > 0 && item.nomLieu !== 'Tous'"
                  :class="{ 'rotate-icon': open }"
                  @click.stop="toggleNode(item)"
                >
                  {{ open ? 'mdi-triangle-down' : 'mdi-triangle-right' }}
                </v-icon>
                <span v-else class="tree-icon-placeholder"></span>
              </template>
              <template #label="{ item }">
                <span class="text-caption ml-2 tree-label" :title="item.nomLieu">{{
                  item.nomLieu
                }}</span>
              </template>
            </VTreeview>
          </div>
        </v-card>

        <!-- Card: Types d'équipements -->
        <v-card elevation="1" class="rounded-lg pa-2">
          <v-card-title class="font-weight-bold text-uppercase text-primary text-body-2">
            Types des équipements
          </v-card-title>
          <v-divider></v-divider>
          <v-list dense>
            <v-list-item
              link
              :class="{ 'selected-item': selectedTypeEquipments.length === 0 }"
              @click="handleEquipmentTypeSelected(null)"
            >
              <v-list-item-title>Tous</v-list-item-title>
            </v-list-item>
            <v-list-item
              v-for="(model, index) in equipmentModels"
              :key="index"
              link
              :class="{ 'selected-item': isEquipmentTypeSelected(model) }"
              @click="handleEquipmentTypeSelected(model)"
            >
              <v-list-item-title>{{ model.nom }}</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>

      <!-- Colonne principale avec EquipmentListComponent -->
      <v-col ref="tableContainer" cols="12" md="8" lg="9">
        <EquipmentListComponent
          ref="equipmentListComponentRef"
          :title="title"
          :show-search="showSearch"
          :no-data-text="noDataText"
          :table-headers="computedTableHeaders"
          :filtered-items="filteredEquipments"
          :server-pagination="true"
          :reserve-fab-space="hasCreationPermission && showCreateButton"
          :selected-location-ids="selectedLocationIds"
          :selected-model-ids="selectedModelIds"
          @row-click="handleRowClick"
          @equipments-loaded="handleEquipmentsLoaded"
          @locations-loaded="handleLocationsLoaded"
          @models-loaded="handleModelsLoaded"
        />

        <!-- Bouton flottant en bas à droite -->
        <FloatingCreateButton
          :visible="hasCreationPermission && showCreateButton"
          :tooltip="createButtonText"
          @click="handleCreate"
        />
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
  import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
  import { useRouter } from 'vue-router'
  import { useStore } from 'vuex'
  import { VTreeview } from 'vuetify/labs/components'
  import FloatingCreateButton from '@/components/common/FloatingCreateButton.vue'
  import EquipmentListComponent from '@/components/EquipmentListComponent.vue'

  const store = useStore()

  // Constantes
  const hasCreationPermission = computed(() => {
    return store.getters.hasPermission('eq:create')
  })

  const props = defineProps({
    title: {
      type: String,
      default: 'Liste des Équipements',
    },
    showSearch: {
      type: Boolean,
      default: true,
    },
    showCreateButton: {
      type: Boolean,
      default: true,
    },
    createButtonText: {
      type: String,
      default: 'Ajouter un équipement',
    },
    noDataText: {
      type: String,
      default: 'Aucun équipement trouvé avec ces filtres',
    },
    height: {
      type: String,
      default: null,
    },
    maxHeight: {
      type: String,
      default: null,
    },
  })

  const router = useRouter()

  // Refs pour les données
  const equipmentListComponentRef = ref(null)
  const equipments = ref([])
  const locations = ref([])
  const equipmentModels = ref([])

  // Refs pour les filtres
  const selectedLocationIds = ref([])
  const selectedTypeEquipments = ref([])
  const selectedTreeNodes = ref([])
  const openNodes = ref(new Set())

  // Refs pour le container
  const tableContainer = ref(null)
  const containerWidth = ref(0)

  let resizeObserver

  // Handlers pour les événements du composant enfant
  const handleEquipmentsLoaded = (data) => {
    equipments.value = data
  }

  const handleLocationsLoaded = (data) => {
    locations.value = data
  }

  const handleModelsLoaded = (data) => {
    equipmentModels.value = data
  }

  // Navigation handlers
  const handleCreate = () => {
    router.push('/CreateEquipment')
  }

  const handleRowClick = (item) => {
    router.push({ name: 'EquipmentDetail', params: { id: item.id } })
  }

  // Fonctions utilitaires pour la hiérarchie des lieux
  const findItem = (items, id) => {
    for (const item of items) {
      if (item.id === id) return item
      if (item.children) {
        const found = findItem(item.children, id)
        if (found) return found
      }
    }
    return null
  }

  const getAllDescendantIds = (item) => {
    let ids = [item.id]
    if (item.children && item.children.length > 0) {
      item.children.forEach((child) => {
        ids = ids.concat(getAllDescendantIds(child))
      })
    }
    return ids
  }

  // Gestion de la sélection des lieux
  const onSelectLocation = (items) => {
    if (items.length > 0) {
      const allLocationIds = []

      items.forEach((id) => {
        const selectedItem = findItem(locations.value, id)
        if (selectedItem) {
          allLocationIds.push(...getAllDescendantIds(selectedItem))
        }
      })

      selectedLocationIds.value = [...new Set(allLocationIds)]
    } else {
      selectedLocationIds.value = []
    }
  }

  const toggleNode = (item) => {
    if (openNodes.value.has(item.id)) {
      openNodes.value.delete(item.id)
    } else {
      openNodes.value.add(item.id)
    }
  }

  // Gestion de la sélection des types d'équipements
  const handleEquipmentTypeSelected = (model) => {
    if (model === null) {
      selectedTypeEquipments.value = []
    } else {
      const index = selectedTypeEquipments.value.findIndex((m) => m.nom === model.nom)
      if (index > -1) {
        selectedTypeEquipments.value.splice(index, 1)
      } else {
        selectedTypeEquipments.value.push(model)
      }
    }
  }

  const isEquipmentTypeSelected = (model) => {
    return selectedTypeEquipments.value.some((m) => m.nom === model.nom)
  }

  // Filtrage des équipements
  const filteredEquipments = computed(() => {
    return equipments.value || []
  })

  const selectedModelIds = computed(() =>
    selectedTypeEquipments.value.map((model) => model.id).filter((id) => Number.isInteger(id))
  )

  // Headers responsifs
  const computedTableHeaders = computed(() => {
    if (containerWidth.value < 700) {
      return compactHeaders
    }
    return fullHeaders
  })

  const fullHeaders = [
    { title: 'Code GMAO', key: 'reference', sortable: true, align: 'center' },
    { title: 'Désignation', key: 'designation', sortable: true, align: 'center' },
    { title: 'Lieu', key: 'lieu.nomLieu', sortable: false, align: 'center' },
    { title: 'Modèle', key: 'modele', sortable: false, align: 'center' },
    {
      title: 'Statut',
      key: 'statut.statut',
      sortable: true,
      align: 'center',
      sort: (a, b) => {
        const order = ['EN_FONCTIONNEMENT', 'DEGRADE', 'A_LARRET', 'HORS_SERVICE']
        return order.indexOf(a) - order.indexOf(b)
      },
    },
  ]

  const compactHeaders = [
    { title: 'Code GMAO', key: 'reference', align: 'center' },
    { title: 'Désignation', key: 'designation', align: 'center' },
    { title: 'Statut', key: 'statut.statut', align: 'center' },
  ]

  // Style du container
  const containerStyle = computed(() => {
    const styles = {}
    if (props.height) {
      styles.height = props.height
      styles.overflow = 'auto'
    }
    if (props.maxHeight) {
      styles.maxHeight = props.maxHeight
      styles.overflow = 'auto'
    }
    return styles
  })

  // Observer pour le responsive
  onMounted(() => {
    resizeObserver = new ResizeObserver((entries) => {
      const entry = entries[0]
      containerWidth.value = Math.round(entry.contentRect.width)
    })

    if (tableContainer.value) {
      resizeObserver.observe(tableContainer.value.$el ?? tableContainer.value)
    }
  })

  onBeforeUnmount(() => {
    resizeObserver?.disconnect()
  })
</script>

<style scoped>
  .v-treeview-node--active {
    background-color: #7577e9 !important;
    color: white !important;
  }

  .v-treeview-node--active:hover {
    background-color: #5658c7 !important;
  }

  .selected-item {
    background-color: #7577e9 !important;
    color: white !important;
  }

  .selected-item:hover {
    background-color: #5658c7 !important;
  }

  .text-caption {
    color: #666;
    font-size: 0.75rem;
  }

  .tree-icon-placeholder {
    display: inline-block;
    width: 24px;
    height: 24px;
    margin-right: 4px;
  }

  .rotate-icon {
    transform: rotate(180deg);
  }

  .v-icon {
    transition: transform 0.3s ease;
  }

  .v-list-item__prepend i,
  .tree-icon-placeholder {
    display: none !important;
  }

  .tree-label {
    max-width: 200px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    display: inline-block;
  }
</style>
