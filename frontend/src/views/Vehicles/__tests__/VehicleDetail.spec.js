import { render, screen, waitFor } from '@testing-library/vue'
import userEvent from '@testing-library/user-event'
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
  http.get('/api/cartes-grises/', () => HttpResponse.json([])),
  http.get('/api/controles-techniques/', () => HttpResponse.json([])),
  http.get('/api/codes-defaut-obd/', () => HttpResponse.json([]))
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

  it("affiche l'historique des cartes grises et permet d'en ajouter une (US-010)", async () => {
    server.use(
      http.get('/api/cartes-grises/', ({ request }) => {
        const url = new URL(request.url)
        if (url.searchParams.get('vehicule_profile') !== '10') return HttpResponse.json([])
        return HttpResponse.json([
          {
            id: 1,
            immatriculation: 'AB-123-CD',
            titulaire: 'Société GIMAO',
            date_emission: '2024-03-01',
          },
        ])
      })
    )

    renderWithPermission()

    await waitFor(() => {
      expect(screen.getByText('Société GIMAO')).toBeDefined()
    })
  })

  it('crée une carte grise via le formulaire inline (US-010)', async () => {
    let created = null
    server.use(
      http.post('/api/cartes-grises/', async ({ request }) => {
        created = await request.json()
        return HttpResponse.json({ id: 2, ...created }, { status: 201 })
      })
    )

    renderWithPermission()
    const user = userEvent.setup()

    await waitFor(() => expect(screen.getByText('Fourgon atelier')).toBeDefined())

    await user.click(screen.getByRole('button', { name: 'Ajouter une carte grise' }))
    await user.type(screen.getByLabelText('Immatriculation'), 'AB-123-CD')
    await user.type(screen.getByLabelText('Titulaire'), 'Société GIMAO')
    await user.type(screen.getByLabelText('Date de première mise en circulation'), '2020-01-15')
    await user.type(screen.getByLabelText("Date d'émission"), '2024-03-01')
    await user.click(screen.getByRole('button', { name: 'Enregistrer' }))

    await waitFor(() => {
      expect(created).toMatchObject({ vehicule_profile: '10', immatriculation: 'AB-123-CD' })
    })
  })

  it("affiche l'historique des contrôles techniques avec un badge de résultat (US-011)", async () => {
    server.use(
      http.get('/api/controles-techniques/', () =>
        HttpResponse.json([
          {
            id: 1,
            date_passage: '2024-03-01',
            date_echeance: '2026-03-01',
            resultat: 'FAVORABLE',
            centre_controle: 'Centre Nord',
          },
        ])
      )
    )

    renderWithPermission()

    await waitFor(() => {
      expect(screen.getByText('Favorable')).toBeDefined()
      expect(screen.getByText('Centre Nord')).toBeDefined()
    })
  })

  it("affiche l'historique des codes défaut OBD (US-022)", async () => {
    server.use(
      http.get('/api/codes-defaut-obd/', () =>
        HttpResponse.json([
          {
            id: 1,
            code: 'P0301',
            description: "Raté d'allumage cylindre 1",
            date_lecture: '2024-03-01T10:00:00Z',
            source: 'MANUEL',
          },
        ])
      )
    )

    renderWithPermission()

    await waitFor(() => {
      expect(screen.getByText('P0301')).toBeDefined()
      expect(screen.getByText("Raté d'allumage cylindre 1")).toBeDefined()
      expect(screen.getByText('Manuel')).toBeDefined()
    })
  })

  it('saisit un code défaut OBD via le formulaire inline (US-022)', async () => {
    let created = null
    server.use(
      http.post('/api/codes-defaut-obd/', async ({ request }) => {
        created = await request.json()
        return HttpResponse.json({ id: 2, ...created }, { status: 201 })
      })
    )

    renderWithPermission()
    const user = userEvent.setup()

    await waitFor(() => expect(screen.getByText('Fourgon atelier')).toBeDefined())

    await user.click(screen.getByRole('button', { name: 'Saisir un code défaut' }))
    await user.type(screen.getByLabelText('Code DTC'), 'P0301')
    await user.type(screen.getByLabelText('Date de lecture'), '2024-03-01T10:00')
    await user.click(screen.getByRole('button', { name: 'Enregistrer' }))

    await waitFor(() => {
      expect(created).toMatchObject({ vehicule_profile: '10', code: 'P0301', source: 'MANUEL' })
    })
  })
})
