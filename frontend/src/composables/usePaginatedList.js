import { computed, onBeforeUnmount, ref, unref, watch } from 'vue'

const PAGINATION_KEYS = new Set(['count', 'next', 'previous', 'results'])

const toSearchValue = (value) => {
  if (typeof value === 'string') {
    return value
  }

  if (value && typeof value === 'object' && typeof value.target?.value === 'string') {
    return value.target.value
  }

  return ''
}

const normalizeResponse = (response) => {
  if (Array.isArray(response)) {
    // Compatibilite avec les endpoints encore non pagines : on expose
    // la meme structure cote composant pour eviter des branches partout.
    return {
      items: response,
      totalItems: response.length,
      extra: {},
    }
  }

  const items = Array.isArray(response?.results) ? response.results : []
  const extra = {}

  if (response && typeof response === 'object') {
    for (const [key, value] of Object.entries(response)) {
      if (!PAGINATION_KEYS.has(key)) {
        extra[key] = value
      }
    }
  }

  return {
    items,
    totalItems: Number(response?.count || 0),
    extra,
  }
}

/**
 * Composable générique pour gérer une liste paginée côté serveur.
 *
 * Gère automatiquement la pagination, la recherche avec debounce, et le rechargement
 * quand une source réactive change. Compatible avec les endpoints DRF paginés
 * (`{ count, next, previous, results }`) et les endpoints non paginés (tableau brut).
 *
 * @param {object}   options
 * @param {ReturnType<import('./useApi').useApi>} options.api
 *   Instance retournée par `useApi()`.
 * @param {string | import('vue').Ref<string> | (() => string)} options.endpoint
 *   URL de l'endpoint (ex : `'equipements/'`). Peut être une ref ou une fonction réactive.
 * @param {number}   [options.initialPageSize=10]   Taille de page initiale.
 * @param {number}   [options.debounceMs=300]        Délai de debounce sur la recherche.
 * @param {(ctx: { currentPage: number, pageSize: number, searchQuery: string }) => object} [options.buildParams]
 *   Fonction pour construire les query params additionnels à chaque requête.
 * @param {import('vue').WatchSource | null} [options.watchSource]
 *   Source réactive dont le changement déclenche un rechargement en page 1.
 * @param {boolean | import('vue').Ref<boolean> | (() => boolean)} [options.enabled=true]
 *   Si false, la liste est vidée et aucun appel réseau n't effectué.
 * @param {((raw: any, normalized: { items: any[], totalItems: number, extra: object }) => void) | null} [options.onFetched]
 *   Callback appelé après chaque chargement réussi.
 *
 * @returns {{
 *   items: import('vue').Ref<any[]>,
 *   currentPage: import('vue').Ref<number>,
 *   pageSize: import('vue').Ref<number>,
 *   searchQuery: import('vue').Ref<string>,
 *   totalItems: import('vue').Ref<number>,
 *   totalPages: import('vue').ComputedRef<number>,
 *   loading: import('vue').ComputedRef<boolean>,
 *   extra: import('vue').Ref<object>,
 *   errorMessage: import('vue').Ref<string>,
 *   fetchPage: () => Promise<any[]>,
 *   handleSearch: (value: string | Event) => void,
 *   resetToFirstPageAndFetch: () => Promise<void>
 * }}
 *
 * @example
 * const { items, currentPage, totalPages, handleSearch, fetchPage } = usePaginatedList({
 *   api: useApi(),
 *   endpoint: 'equipements/',
 *   buildParams: ({ searchQuery }) => ({ search: searchQuery }),
 * })
 */
export function usePaginatedList({
  api,
  endpoint,
  initialPageSize = 10,
  debounceMs = 300,
  buildParams = () => ({}),
  watchSource = null,
  enabled = true,
  onFetched = null,
}) {
  const items = ref([])
  const currentPage = ref(1)
  const pageSize = ref(initialPageSize)
  const searchQuery = ref('')
  const totalItems = ref(0)
  const extra = ref({})
  const errorMessage = ref('')

  let searchTimeoutId = null

  const loading = computed(() => api.loading.value)
  const totalPages = computed(() => {
    if (pageSize.value <= 0) return 1
    return Math.max(1, Math.ceil(totalItems.value / pageSize.value))
  })

  const resolveEndpoint = () => (typeof endpoint === 'function' ? endpoint() : unref(endpoint))
  const resolveEnabled = () => (typeof enabled === 'function' ? enabled() : unref(enabled))

  const fetchPage = async () => {
    if (!resolveEnabled()) {
      items.value = []
      totalItems.value = 0
      extra.value = {}
      return []
    }

    errorMessage.value = ''

    try {
      const params = {
        page: currentPage.value,
        page_size: pageSize.value,
        ...buildParams({
          currentPage: currentPage.value,
          pageSize: pageSize.value,
          searchQuery: searchQuery.value.trim(),
        }),
      }

      // Si le composant ne fournit pas de mapping custom pour la recherche,
      // on injecte le parametre DRF standard une seule fois ici.
      if (!params.search && searchQuery.value.trim()) {
        params.search = searchQuery.value.trim()
      }

      const response = await api.get(resolveEndpoint(), params)
      const normalized = normalizeResponse(response)

      items.value = normalized.items
      totalItems.value = normalized.totalItems
      extra.value = normalized.extra

      if (typeof onFetched === 'function') {
        onFetched(response, normalized)
      }

      return normalized.items
    } catch (error) {
      errorMessage.value = error?.response?.data?.error || 'Erreur lors du chargement des données'
      throw error
    }
  }

  const resetToFirstPageAndFetch = async () => {
    if (currentPage.value !== 1) {
      // Le watcher sur currentPage declenche deja fetchPage ; on evite
      // donc un deuxieme appel reseau quand on force simplement le retour page 1.
      currentPage.value = 1
      return
    }

    await fetchPage()
  }

  const handleSearch = (value) => {
    searchQuery.value = toSearchValue(value)

    if (searchTimeoutId) {
      clearTimeout(searchTimeoutId)
    }

    searchTimeoutId = setTimeout(() => {
      resetToFirstPageAndFetch().catch(() => {})
    }, debounceMs)
  }

  watch(currentPage, () => {
    fetchPage().catch(() => {})
  })

  watch(pageSize, () => {
    resetToFirstPageAndFetch().catch(() => {})
  })

  if (watchSource) {
    watch(watchSource, () => {
      resetToFirstPageAndFetch().catch(() => {})
    })
  }

  onBeforeUnmount(() => {
    if (searchTimeoutId) {
      clearTimeout(searchTimeoutId)
    }
  })

  return {
    items,
    currentPage,
    pageSize,
    searchQuery,
    totalItems,
    totalPages,
    loading,
    extra,
    errorMessage,
    fetchPage,
    handleSearch,
    resetToFirstPageAndFetch,
  }
}
