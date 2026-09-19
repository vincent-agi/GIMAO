import { computed } from 'vue'

/**
 * Paires d'exclusion mutuelle visuelles — aucun lien en base.
 * Cocher l'un grise et décoche l'autre.
 */
const EXCLUSIVE_PAIRS = [
  ['dash:display.bt', 'dash:display.btAssigned'],
  ['dash:display.di', 'dash:display.diCreated'],
  ['dash:stats.full', 'dash:stats.bt'],
  ['dash:stats.full', 'dash:stats.di'],
]

function getExclusiveGroupNoms(nomPermission) {
  return EXCLUSIVE_PAIRS.filter((pair) => pair.includes(nomPermission)).map((pair) =>
    pair.find((n) => n !== nomPermission)
  )
}

/**
 * Composable partagé pour la sélection de permissions.
 *
 * @param {Ref<Array>} allPermissions - liste complète { id, nomPermission, description, type, parent_id, module }
 * @param {Ref<Array>} selectedIds    - tableau des IDs sélectionnés (modifiable)
 * @param {Ref<string>} searchPerm    - chaîne de recherche
 *
 * Fonctionnement parent_id :
 *   Cocher un enfant coche automatiquement tous ses ancêtres (remontée de chaîne).
 *   Ex : cocher di:archive coche di:viewDetail puis di:viewList.
 *   Un ancêtre est grisé (non décoché) tant qu'un enfant sélectionné en dépend.
 */
export function usePermissionSelector(allPermissions, selectedIds, searchPerm) {
  // Remonte la chaîne des parents et retourne tous les ids ancêtres
  function getAncestorIds(id) {
    const ancestors = []
    let perm = allPermissions.value.find((p) => p.id === id)
    while (perm?.parent_id) {
      ancestors.push(perm.parent_id)
      perm = allPermissions.value.find((p) => p.id === perm.parent_id)
    }
    return ancestors
  }

  // Collecte récursivement tous les ids descendants (via parent_id)
  function getDescendantIds(id) {
    const result = []
    for (const p of allPermissions.value) {
      if (p.parent_id === id) {
        result.push(p.id)
        result.push(...getDescendantIds(p.id))
      }
    }
    return result
  }

  // IDs des autres membres du groupe exclusif visuel
  function getExclusiveGroupIds(permId) {
    const perm = allPermissions.value.find((p) => p.id === permId)
    if (!perm) return []
    return getExclusiveGroupNoms(perm.nomPermission)
      .map((nom) => allPermissions.value.find((p) => p.nomPermission === nom)?.id)
      .filter(Boolean)
  }

  /**
   * Une permission est grisée si un autre membre de son groupe exclusif visuel est sélectionné.
   * Les parents NE sont PAS verrouillés : les décocher décoche automatiquement leurs enfants.
   */
  const isPermDisabledByHierarchy = (permId) => {
    return getExclusiveGroupIds(permId).some((id) => selectedIds.value.includes(id))
  }

  // Permissions groupées par module
  const permissionsByModule = computed(() => {
    const groups = {}
    for (const perm of allPermissions.value) {
      const code = perm.module?.code ?? perm.nomPermission.split(':')[0]
      const nom = perm.module?.nom ?? code
      if (!groups[code]) groups[code] = { nom, affichage: [], action: [] }
      groups[code][perm.type ?? 'action'].push(perm)
    }
    return groups
  })

  // Permissions filtrées par la recherche
  const filteredPermissionsByModule = computed(() => {
    if (!searchPerm.value) return permissionsByModule.value
    const search = searchPerm.value.toLowerCase()
    const result = {}
    for (const [code, data] of Object.entries(permissionsByModule.value)) {
      const filteredAffichage = data.affichage.filter(
        (p) =>
          p.description?.toLowerCase().includes(search) ||
          p.nomPermission.toLowerCase().includes(search)
      )
      const filteredAction = data.action.filter(
        (p) =>
          p.description?.toLowerCase().includes(search) ||
          p.nomPermission.toLowerCase().includes(search)
      )
      if (filteredAffichage.length || filteredAction.length) {
        result[code] = { ...data, affichage: filteredAffichage, action: filteredAction }
      }
    }
    return result
  })

  const isModuleFullySelected = (perms) => perms.every((p) => selectedIds.value.includes(p.id))

  const isModulePartiallySelected = (perms) => {
    const count = perms.filter((p) => selectedIds.value.includes(p.id)).length
    return count > 0 && count < perms.length
  }

  const toggleModule = (perms, value) => {
    const current = new Set(selectedIds.value)
    if (value) {
      for (const perm of perms) {
        current.add(perm.id)
        for (const ancestorId of getAncestorIds(perm.id)) current.add(ancestorId)
      }
    } else {
      for (const perm of perms) {
        current.delete(perm.id)
        for (const descendantId of getDescendantIds(perm.id)) current.delete(descendantId)
      }
    }
    selectedIds.value = [...current]
  }

  const togglePermission = (id, value) => {
    const current = new Set(selectedIds.value)
    if (value) {
      current.add(id)
      for (const ancestorId of getAncestorIds(id)) current.add(ancestorId)
      for (const otherId of getExclusiveGroupIds(id)) current.delete(otherId)
    } else {
      current.delete(id)
      for (const descendantId of getDescendantIds(id)) current.delete(descendantId)
    }
    selectedIds.value = [...current]
  }

  // Applique la hiérarchie après chargement : coche les ancêtres manquants
  const applyHierarchy = () => {
    const current = new Set(selectedIds.value)
    for (const id of [...current]) {
      for (const ancestorId of getAncestorIds(id)) current.add(ancestorId)
    }
    selectedIds.value = [...current]
  }

  return {
    permissionsByModule,
    filteredPermissionsByModule,
    isPermDisabledByHierarchy,
    isModuleFullySelected,
    isModulePartiallySelected,
    toggleModule,
    togglePermission,
    applyHierarchy,
  }
}
