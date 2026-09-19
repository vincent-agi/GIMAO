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
  useRoute: () => ({ params: { id: '10' } }),
  useRouter: () => ({ push: mockPush }),
}))

import VehicleDetail from '../VehicleDetail.vue'

const vuetify = createVuetify({ components, directives })

const vehicule = {
  id: 10,
  designation: 'Fourgon atelier',
  reference: 'REF-010',
  lieu: { nomLieu: 'Dépôt central' },
  modele: 'Trafic',
  statut: { statut: 'EN_FONCTIONNEMENT' },
  vehicule_profile: {
    vin: 'VF1BB000000000010',
    immatriculation: 'AB-123-CD',
    genre: 'VL',
    energie: 'DIESEL',
    co2: 120,
    puissanceFiscale: 6,
    ptac: 2000,
  },
}

const server = setupServer(
  http.get('/api/vehicules/10/', () => HttpResponse.json(vehicule)),
)

const renderWithPermission = (hasPermission = true) => {
  const store = createStore({
    getters: { hasPermission: () => () => hasPermission },
  })
  return render(VehicleDetail, { global: { plugins: [vuetify, store] } })
}

beforeAll(() => server.listen())
afterEach(() => {
  server.resetHandlers()
  mockPush.mockClear()
})
afterAll(() => server.close())

describe('VehicleDetail.vue', () => {
  it('affiche les informations du véhicule après chargement', async () => {
    renderWithPermission()

    await waitFor(() => {
      expect(screen.getByText('Fourgon atelier')).toBeDefined()
      expect(screen.getByText('AB-123-CD')).toBeDefined()
      expect(screen.getByText('VF1BB000000000010')).toBeDefined()
      expect(screen.getByText('Véhicule léger')).toBeDefined()
      expect(screen.getByText('Diesel')).toBeDefined()
    })
  })

  it("n'affiche pas le bouton d'édition sans la permission veh:edit", async () => {
    renderWithPermission(false)

    await waitFor(() => {
      expect(screen.getByText('Fourgon atelier')).toBeDefined()
    })

    expect(screen.queryByRole('button', { name: /Modifier le véhicule/i })).toBeNull()
  })

  it('affiche un message explicite en cas de véhicule introuvable', async () => {
    server.use(http.get('/api/vehicules/10/', () => new HttpResponse(null, { status: 404 })))

    renderWithPermission()

    await waitFor(() => {
      expect(screen.getByText('Erreur lors du chargement du véhicule.')).toBeDefined()
    })
  })
})
