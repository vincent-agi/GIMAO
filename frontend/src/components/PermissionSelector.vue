<template>
  <div>
    <v-text-field
      v-model="searchPerm"
      placeholder="Rechercher une permission..."
      prepend-inner-icon="mdi-magnify"
      variant="outlined"
      density="compact"
      clearable
      class="mb-3"
    />

    <div v-for="(types, module) in filteredPermissionsByModule" :key="module" class="mb-2">
      <v-expansion-panels variant="accordion">
        <v-expansion-panel>
          <v-expansion-panel-title>
            <div class="d-flex align-center" style="gap: 12px">
              <v-checkbox
                :model-value="isModuleFullySelected([...types.affichage, ...types.action])"
                :indeterminate="isModulePartiallySelected([...types.affichage, ...types.action])"
                density="compact"
                hide-details
                color="primary"
                @update:model-value="toggleModule([...types.affichage, ...types.action], $event)"
                @click.stop
              />
              <span class="font-weight-medium">{{ types.nom }}</span>
              <v-chip size="x-small" color="primary" variant="tonal">
                {{
                  [...types.affichage, ...types.action].filter((p) => modelValue.includes(p.id))
                    .length
                }}/{{ types.affichage.length + types.action.length }}
              </v-chip>
            </div>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <div v-if="types.affichage.length > 0" class="mb-3">
              <div class="text-caption font-weight-bold text-medium-emphasis mb-1">AFFICHAGE</div>
              <div v-for="perm in types.affichage" :key="perm.id" class="d-flex align-center">
                <v-checkbox
                  :model-value="modelValue.includes(perm.id)"
                  :label="perm.description"
                  density="compact"
                  hide-details
                  color="blue"
                  :disabled="isPermDisabledByHierarchy(perm.id)"
                  @update:model-value="togglePermission(perm.id, $event)"
                />
              </div>
            </div>
            <div v-if="types.action.length > 0">
              <div class="text-caption font-weight-bold text-medium-emphasis mb-1">ACTIONS</div>
              <div v-for="perm in types.action" :key="perm.id" class="d-flex align-center">
                <v-checkbox
                  :model-value="modelValue.includes(perm.id)"
                  :label="perm.description"
                  density="compact"
                  hide-details
                  color="orange"
                  :disabled="isPermDisabledByHierarchy(perm.id)"
                  @update:model-value="togglePermission(perm.id, $event)"
                />
              </div>
            </div>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </div>

    <p
      v-if="Object.keys(filteredPermissionsByModule).length === 0"
      class="text-body-2 text-medium-emphasis"
    >
      Aucune permission trouvée.
    </p>
  </div>
</template>

<script setup>
  import { ref, computed } from 'vue'
  import { usePermissionSelector } from '@/composables/usePermissionSelector'

  const props = defineProps({
    allPermissions: { type: Array, required: true },
    modelValue: { type: Array, required: true },
  })

  const emit = defineEmits(['update:modelValue'])

  const searchPerm = ref('')

  const selectedIds = computed({
    get: () => props.modelValue,
    set: (val) => emit('update:modelValue', val),
  })

  const allPermissionsRef = computed(() => props.allPermissions)

  const {
    filteredPermissionsByModule,
    isPermDisabledByHierarchy,
    isModuleFullySelected,
    isModulePartiallySelected,
    toggleModule,
    togglePermission,
    applyHierarchy,
  } = usePermissionSelector(allPermissionsRef, selectedIds, searchPerm)

  const resetSearch = () => {
    searchPerm.value = ''
  }

  defineExpose({ applyHierarchy, resetSearch })
</script>
