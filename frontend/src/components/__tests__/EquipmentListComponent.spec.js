import { render, screen, waitFor } from '@testing-library/vue'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { describe, it, expect, beforeAll, afterEach, afterAll } from 'vitest'
import { createStore } from 'vuex'

// Vuetify pour le rendu des composants
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

import EquipmentListComponent from '../EquipmentListComponent.vue'

// Constante fictive pour l'exemple
const API_BASE_URL = '/api/'

// ============================================================================
// 1. CONFIGURATION DE L'ENVIRONNEMENT DE TEST (MOCK API & PLUGINS)
// ============================================================================

// Instancie Vuetify pour que Testing Library comprenne les <v-btn>, <v-data-table>, etc.
const vuetify = createVuetify({ components, directives })

// Store minimal : le composant vérifie la permission 'eq:create' pour afficher
// les boutons d'import Excel (voir EquipmentListComponent.vue).
const store = createStore({
  getters: {
    hasPermission: () => () => true,
  },
})

// Initialisation de MSW (Mock Service Worker)
// Il intercepte toutes les vraies requêtes réseau de "useApi" (axios/fetch)
const server = setupServer(
  // Mock standard de la liste des équipements (le cas qui "marche")
  http.get(`${API_BASE_URL}equipements/`, ({ request }) => {
    const url = new URL(request.url)
    const search = url.searchParams.get('search')

    let mockData = [
      {
        id: 1,
        reference: 'EQ-001',
        designation: 'Pompe A1',
        lieu: { nomLieu: 'Atelier' },
        modele: 'Mod A',
        statut: { statut: 'EN_FONCTIONNEMENT' },
      },
      {
        id: 2,
        reference: 'EQ-002',
        designation: 'Compresseur',
        lieu: { nomLieu: 'Usine' },
        modele: 'Mod B',
        statut: { statut: 'HORS_SERVICE' },
      },
    ]

    // Simule la recherche serveur
    if (search) {
      mockData = mockData.filter((eq) =>
        eq.designation.toLowerCase().includes(search.toLowerCase())
      )
    }

    // Le composant gère une pagination serveur, donc on renvoie un objet count/results
    return HttpResponse.json({ count: mockData.length, results: mockData })
  }),

  // Mocks des data annexes appelées dans fetchSupportData()
  http.get(`${API_BASE_URL}lieux/hierarchy/`, () => HttpResponse.json([])),
  http.get(`${API_BASE_URL}modele-equipements/`, () => HttpResponse.json([]))
)

// Cycle de vie MSW
beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

// Wrapper helper pour faciliter le rendu du composant avec Vuetify
const renderComponent = (props = {}) => {
  return render(EquipmentListComponent, {
    props: {
      serverPagination: true, // par défaut
      ...props,
    },
    global: {
      plugins: [vuetify, store],
    },
  })
}

// ============================================================================
// 2. SUITE DE TESTS (Approche Given/When/Then)
// ============================================================================

describe('EquipmentListComponent', () => {
  it('doit afficher la liste des équipements après le chargement initial', async () => {
    // -----------------------------------------------------------------
    // GIVEN (Étant donné...)
    // -----------------------------------------------------------------
    // ... que le serveur API est opérationnel (le server MSW normal est actif)
    // et possède "Pompe A1" et "Compresseur".

    // -----------------------------------------------------------------
    // WHEN (Quand...)
    // -----------------------------------------------------------------
    // ... le composant est monté dans le navigateur
    renderComponent()

    // -----------------------------------------------------------------
    // THEN (Alors...)
    // -----------------------------------------------------------------
    // ... J'attends que la requête réseau asynchrone aboutisse
    await waitFor(() => {
      // ... et je vérifie que les textes sont bien affichés par Vuetify
      expect(screen.getByText('Pompe A1')).toBeDefined()
      expect(screen.getByText('Compresseur')).toBeDefined()
    })

    // Note: Le composant utilise le helper "getStatusLabel". S'il gère les traductions
    // de statut EN_FONCTIONNEMENT -> "En fonctionnement", Testing Library verra le texte traduit.
    // Cela garantit qu'on teste le "vrai" code affiché !
  })

  it("doit filtrer le tableau quand l'utilisateur utilise la barre de recherche", async () => {
    // GIVEN: Le tableau est complètement chargé
    renderComponent()
    await waitFor(() => {
      expect(screen.getByText('Pompe A1')).toBeDefined()
      expect(screen.getByText('Compresseur')).toBeDefined()
    })

    // WHEN: L'utilisateur tape du texte dans le champ de recherche Vuetify de l'enfant BaseListView
    // userEvent est essentiel car il simule de bout en bout l'événement clavier
    const user = userEvent.setup()

    // Remarque: la `BaseListView` a sûrement un input textuel. S'il n'a pas de nom explicite,
    // on vise souvent la class vuetify ou le label. Adaptes ce sélecteur à ton code.
    // Imaginons que "show-search" affiche un champ avec pour label ou placeholder "Rechercher"
    const searchInput = screen.getByLabelText('Rechercher')
    await user.type(searchInput, 'Compresseur')

    // On déclenche la recherche (le debounce défini dans let searchDebounceId = null prendra le relais)

    // THEN: L'API devrait être appelée avec '?search=Compresseur'
    // La Pompe disparaît, le compresseur reste.
    await waitFor(
      () => {
        expect(screen.getByText('Compresseur')).toBeDefined()
        expect(screen.queryByText('Pompe A1')).toBeNull()
      },
      { timeout: 1200 }
    )
  })

  it('doit afficher un message explicite en cas de défaillance réseau', async () => {
    // GIVEN: L'API est injoignable (Génération d'une fausse erreur serveur)
    server.use(
      http.get(`${API_BASE_URL}equipements/`, () => {
        return new HttpResponse(null, { status: 500 })
      })
    )

    // WHEN: Le composant est rendu
    renderComponent()

    // THEN: Le paramètre errorMessage de BaseListView devrait se mettre à jour
    // et la UI devrait intercepter ça
    await waitFor(() => {
      expect(screen.getByText('Erreur lors du chargement des données')).toBeDefined()
    })
  })
})
