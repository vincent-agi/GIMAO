import { render, screen, waitFor, fireEvent } from '@testing-library/vue'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { describe, it, expect, beforeAll, afterEach, afterAll, vi } from 'vitest'
import { createStore } from 'vuex'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

import VehiculeForm from '../VehiculeForm.vue'

const vuetify = createVuetify({ components, directives })

const store = createStore({
  getters: {
    currentUser: () => ({ id: 7 }),
  },
})

let lastPutBody = null

const server = setupServer(
  http.post('/api/vehicules/', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({ id: 42, type: 'VEHICULE', ...body }, { status: 201 })
  }),
  http.put('/api/vehicules/:id/', async ({ request, params }) => {
    lastPutBody = await request.json()
    return HttpResponse.json(
      { id: Number(params.id), vehicule_profile: { immatriculation: 'AB-123-CD' } },
      { status: 200 },
    )
  }),
)

beforeAll(() => server.listen())
afterEach(() => {
  server.resetHandlers()
  lastPutBody = null
})
afterAll(() => server.close())

const renderForm = (props = {}) =>
  render(VehiculeForm, {
    props,
    global: { plugins: [vuetify, store] },
  })

const existingVehicule = {
  id: 10,
  designation: 'Fourgon atelier',
  reference: 'REF-010',
  lieu: { id: 1 },
  famille: { id: 2 },
  fabricant: { id: 3 },
  fournisseur: { id: 4 },
  modele: { id: 5 },
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

describe('VehiculeForm.vue', () => {
  it('affiche les champs identification en mode création', () => {
    renderForm()

    expect(screen.getByText('Ajouter un véhicule')).toBeDefined()
    expect(screen.getByPlaceholderText('Ex: Fourgon atelier n°3')).toBeDefined()
    expect(screen.getByPlaceholderText('AB-123-CD')).toBeDefined()
  })

  it('signale un VIN au format invalide', async () => {
    renderForm()
    const user = userEvent.setup()

    const vinInput = screen.getByPlaceholderText('17 caractères, ex: VF1BB000000000001')
    await user.type(vinInput, 'TROP_COURT')
    await fireEvent.blur(vinInput)

    await waitFor(() => {
      expect(screen.getByText('Le VIN doit comporter 17 caractères (hors I, O, Q)')).toBeDefined()
    })
  })

  it('pré-remplit le formulaire en mode édition', () => {
    renderForm({ title: 'Modifier le véhicule', isEdit: true, initialData: existingVehicule })

    expect(screen.getByText('Modifier le véhicule')).toBeDefined()
    expect(screen.getByDisplayValue('Fourgon atelier')).toBeDefined()
    expect(screen.getByDisplayValue('VF1BB000000000010')).toBeDefined()
    expect(screen.getByDisplayValue('AB-123-CD')).toBeDefined()
  })

  it("modifie la désignation et n'envoie que le champ modifié", async () => {
    const { emitted } = renderForm({
      isEdit: true,
      initialData: existingVehicule,
      submitButtonText: 'Enregistrer les modifications',
    })
    const user = userEvent.setup()

    const designationInput = screen.getByDisplayValue('Fourgon atelier')
    await user.clear(designationInput)
    await user.type(designationInput, 'Fourgon rénové')

    const submitBtn = screen.getByRole('button', { name: 'Enregistrer les modifications' })
    await user.click(submitBtn)

    await waitFor(() => {
      expect(screen.getByText('Véhicule modifié avec succès')).toBeDefined()
      expect(emitted().updated).toBeTruthy()
    })

    expect(lastPutBody).toBeTruthy()
    const changes = JSON.parse(lastPutBody.changes)
    expect(Object.keys(changes)).toEqual(['designation'])
    expect(changes.designation.nouvelle).toBe('Fourgon rénové')
  })

  it("n'envoie aucune requête si aucun changement n'est détecté en édition", async () => {
    renderForm({ isEdit: true, initialData: existingVehicule })
    const user = userEvent.setup()

    const submitBtn = screen.getByRole('button', { name: 'Créer' })
    await user.click(submitBtn)

    await waitFor(() => {
      expect(screen.getByText('Aucun changement détecté')).toBeDefined()
    })
    expect(lastPutBody).toBeNull()
  })
})
