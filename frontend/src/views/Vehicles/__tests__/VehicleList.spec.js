import { render, screen, waitFor } from '@testing-library/vue'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { describe, it, expect, beforeAll, afterEach, afterAll, vi } from 'vitest'
import { createStore } from 'vuex'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush }),
}))

import VehicleList from '../VehicleList.vue'

const API_BASE_URL = '/api/'
const vuetify = createVuetify({ components, directives })

const store = createStore({
  getters: {
    hasPermission: () => () => true,
  },
})

const vehicules = [
  {
    id: 1,
    designation: 'Fourgon atelier',
    modele: 'Trafic',
    lieu: { id: 1, nomLieu: 'Dépôt central' },
    statut: { statut: 'EN_FONCTIONNEMENT' },
    vehicule_profile: { immatriculation: 'AB-123-CD', genre: 'VL', energie: 'DIESEL' },
  },
  {
    id: 2,
    designation: 'Camion benne',
    modele: 'Daily',
    lieu: { id: 2, nomLieu: 'Chantier Nord' },
    statut: { statut: 'HORS_SERVICE' },
    vehicule_profile: { immatriculation: 'EF-456-GH', genre: 'PL', energie: 'DIESEL' },
  },
]

const server = setupServer(
  http.get(`${API_BASE_URL}vehicules/`, () => {
    return HttpResponse.json({ count: vehicules.length, results: vehicules })
  }),
)

beforeAll(() => server.listen())
afterEach(() => {
  server.resetHandlers()
  mockPush.mockClear()
})
afterAll(() => server.close())

const renderView = () =>
  render(VehicleList, {
    global: { plugins: [vuetify, store] },
  })

describe('VehicleList.vue', () => {
  it('affiche les véhicules avec leur immatriculation et leur statut après chargement', async () => {
    renderView()

    await waitFor(() => {
      expect(screen.getByText('AB-123-CD')).toBeDefined()
      expect(screen.getByText('EF-456-GH')).toBeDefined()
      expect(screen.getByText('Fourgon atelier')).toBeDefined()
    })
  })

  it("affiche un état vide explicite quand aucun véhicule n'existe", async () => {
    server.use(
      http.get(`${API_BASE_URL}vehicules/`, () => HttpResponse.json({ count: 0, results: [] })),
    )

    renderView()

    await waitFor(() => {
      expect(screen.getByText('Aucun véhicule trouvé')).toBeDefined()
    })
  })

  it('affiche un message explicite en cas de défaillance réseau', async () => {
    server.use(
      http.get(`${API_BASE_URL}vehicules/`, () => new HttpResponse(null, { status: 500 })),
    )

    renderView()

    await waitFor(() => {
      expect(screen.getByText('Erreur lors du chargement des données')).toBeDefined()
    })
  })
})
