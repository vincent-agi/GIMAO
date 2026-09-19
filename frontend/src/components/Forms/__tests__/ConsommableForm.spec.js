import { render, screen, waitFor } from '@testing-library/vue'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { describe, it, expect, beforeAll, afterEach, afterAll } from 'vitest'

import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

import ConsommableForm from '../ConsommableForm.vue'

const vuetify = createVuetify({ components, directives })

const server = setupServer(
  http.post('/api/consommables/', async () => {
    return HttpResponse.json({ id: 1, designation: 'Vis' }, { status: 201 })
  }),
  http.patch('/api/consommables/:id/', async () => {
    return HttpResponse.json({ id: 2, designation: 'Boulon' }, { status: 200 })
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

const renderForm = (props = {}) => {
  return render(ConsommableForm, {
    props,
    global: {
      plugins: [vuetify],
    },
  })
}

describe('ConsommableForm.vue', () => {
  it('affiche le bon titre en mode création', () => {
    renderForm({ initialData: null })
    expect(screen.getByText('Ajouter un consommable')).toBeDefined()
  })

  it('affiche le bon titre et pré-remplit les valeurs en mode édition', async () => {
    renderForm({ initialData: { id: 2, designation: 'Boulon', seuilStockFaible: 10 } })

    expect(screen.getByText('Modifier le consommable')).toBeDefined()

    await waitFor(() => {
      expect(screen.getByDisplayValue('Boulon')).toBeDefined()
      expect(screen.getByDisplayValue('10')).toBeDefined()
    })
  })

  it('crée un consommable via API post et emet created', async () => {
    // GIVEN (Étant donné) : Un formulaire vide pour créer un nouveau consommable
    const { emitted } = renderForm({ initialData: null })
    const user = userEvent.setup()

    // WHEN (Quand) : L'utilisateur saisit "Vis" comme désignation et soumet le formulaire
    const desInput = screen.getByPlaceholderText('Saisir la désignation du consommable')
    await user.type(desInput, 'Vis')

    const submitBtn = screen.getByRole('button', { name: /Cr.*er|Enregistrer|Sauvegarder/i })
    await user.click(submitBtn)

    // THEN (Alors) : On attend l'affichage du message de succès et l'émission du signal "created"
    await waitFor(() => {
      expect(screen.getByText('Consommable créé avec succès')).toBeDefined()
      expect(emitted().created).toBeTruthy()
    })
  })

  it('modifie un consommable via API patch et emet updated', async () => {
    const { emitted } = renderForm({ initialData: { id: 2, designation: 'Boulon_old' } })
    const user = userEvent.setup()

    const desInput = await screen.findByDisplayValue('Boulon_old')
    await user.clear(desInput)
    await user.type(desInput, 'Boulon_new')

    const submitBtn = screen.getByRole('button', { name: /Cr.*er|Enregistrer|Sauvegarder/i })
    await user.click(submitBtn)

    await waitFor(() => {
      expect(emitted().updated).toBeTruthy()
    })
  })

  it("affiche une erreur explicite en cas d'echec API", async () => {
    server.use(
      http.post('/api/consommables/', () => {
        return new HttpResponse(null, { status: 403, statusText: 'Droit insuffisant' })
      })
    )

    renderForm({ initialData: null })
    const user = userEvent.setup()

    const desInput = screen.getByPlaceholderText('Saisir la désignation du consommable')
    await user.type(desInput, 'Rondelle')

    const submitBtn = screen.getByRole('button', { name: /Cr.*er|Enregistrer|Sauvegarder/i })
    await user.click(submitBtn)

    await waitFor(() => {
      expect(document.querySelector('.v-alert.bg-error')).not.toBeNull()
    })
  })
})
