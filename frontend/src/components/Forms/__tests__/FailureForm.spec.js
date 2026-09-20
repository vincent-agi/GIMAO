import { render, screen, waitFor, within } from '@testing-library/vue'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { describe, it, expect, beforeAll, afterEach, afterAll } from 'vitest'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

import FailureForm from '../FailureForm.vue'

const vuetify = createVuetify({ components, directives })

const vehiculeEquipement = { id: 1, designation: 'Fourgon atelier', type: 'VEHICULE' }
const mecaniqueEquipement = { id: 2, designation: 'Presse hydraulique', type: 'MECANIQUE' }

let lastCreateBody = null

const server = setupServer(
  http.get('/api/demandes-intervention/', () => HttpResponse.json({ count: 0, results: [] })),
  http.post('/api/demandes-intervention/', async ({ request }) => {
    lastCreateBody = await request.formData()
    return HttpResponse.json({ id: 42 }, { status: 201 })
  })
)

beforeAll(() => server.listen())
afterEach(() => {
  server.resetHandlers()
  lastCreateBody = null
})
afterAll(() => server.close())

const renderForm = (props = {}) =>
  render(FailureForm, {
    props: {
      equipments: [vehiculeEquipement, mecaniqueEquipement],
      typesDocuments: [],
      connectedUserId: 7,
      ...props,
    },
    global: { plugins: [vuetify] },
  })

describe('FailureForm.vue — avarie véhicule (US-020/021)', () => {
  it("n'affiche pas la section avarie véhicule pour un équipement non-véhicule", async () => {
    renderForm({ initialData: { equipement_id: mecaniqueEquipement.id } })

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Créer' })).toBeDefined()
    })

    expect(screen.queryByText('Avarie véhicule')).toBeNull()
  })

  it('affiche la section avarie véhicule pour un équipement de type VEHICULE', async () => {
    renderForm({ initialData: { equipement_id: vehiculeEquipement.id } })

    await waitFor(() => {
      expect(screen.getByText('Avarie véhicule')).toBeDefined()
    })
  })

  it('envoie incident_vehicule avec les valeurs par défaut à la création', async () => {
    renderForm({ initialData: { equipement_id: vehiculeEquipement.id, statut_suppose: 'DEGRADE' } })
    const user = userEvent.setup()

    await waitFor(() => expect(screen.getByText('Avarie véhicule')).toBeDefined())

    await user.click(screen.getByRole('button', { name: 'Créer' }))

    await waitFor(() => {
      expect(lastCreateBody).not.toBeNull()
    })

    const incidentPayload = JSON.parse(lastCreateBody.get('incident_vehicule'))
    expect(incidentPayload).toEqual({
      type_avarie: 'VOYANT',
      gravite: 'MINEURE',
      immobilisation: false,
    })
    expect(lastCreateBody.has('sinistre')).toBe(false)
  })

  it("affiche et envoie les champs sinistre quand le type d'avarie est un accident de la route", async () => {
    renderForm({
      initialData: { equipement_id: vehiculeEquipement.id, statut_suppose: 'A_LARRET' },
    })
    const user = userEvent.setup()

    await waitFor(() => expect(screen.getByText('Avarie véhicule')).toBeDefined())

    const typeAvarieLabel = screen.getByText("Type d'avarie")
    const typeAvarieField = within(typeAvarieLabel.closest('div')).getByRole('combobox')
    await user.click(typeAvarieField)
    await user.click(await screen.findByRole('option', { name: 'Accident de la route' }))

    await waitFor(() => {
      expect(screen.getByText('Détails du sinistre')).toBeDefined()
    })

    await user.type(screen.getByLabelText("Lieu de l'accident"), 'Rond-point Nord')

    await user.click(screen.getByRole('button', { name: 'Créer' }))

    await waitFor(() => {
      expect(lastCreateBody).not.toBeNull()
    })

    const incidentPayload = JSON.parse(lastCreateBody.get('incident_vehicule'))
    expect(incidentPayload.type_avarie).toBe('ACCIDENT_ROUTE')

    const sinistrePayload = JSON.parse(lastCreateBody.get('sinistre'))
    expect(sinistrePayload.lieu_accident).toBe('Rond-point Nord')
  })
})
