import { render, screen } from '@testing-library/vue'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

import FormActions from '../FormActions.vue'

const vuetify = createVuetify({ components, directives })

// Mock de vue-router pour intercepter router.go(-1) appelé dans "Annuler"
const mockRouter = {
  go: vi.fn(),
}
vi.mock('vue-router', () => ({
  useRouter: () => mockRouter,
  useRoute: () => ({}),
}))

const renderComponent = (props = {}) => {
  return render(FormActions, {
    props,
    global: {
      plugins: [vuetify],
    },
  })
}

describe('FormActions.vue', () => {
  it('rend les boutons par défaut (Annuler et Enregistrer)', () => {
    renderComponent()

    expect(screen.getByRole('button', { name: /Annuler/i })).not.toBeNull()
    expect(screen.getByRole('button', { name: /Enregistrer/i })).not.toBeNull()
    expect(screen.queryByRole('button', { name: /RÃ©initialiser/i })).toBeNull() // Pas affiché par défaut
  })

  it("émet l'événement submit quand on clique sur enregistrer", async () => {
    const { emitted } = renderComponent()
    const user = userEvent.setup()

    // WHEN on clique
    await user.click(screen.getByRole('button', { name: /Enregistrer/i }))

    // THEN l'event doit exister
    expect(emitted().submit).toBeTruthy()
  })

  it('appelle le retour du router ou event custom quand on annule', async () => {
    const { emitted } = renderComponent()
    const user = userEvent.setup()

    // reset du mock pour éviter d'avoir le résultat d'un autre test
    mockRouter.go.mockClear()

    await user.click(screen.getByRole('button', { name: /Annuler/i }))

    // En annulant sans customAction, cela émet d'abord 'cancel' :
    expect(emitted().cancel).toBeTruthy()
    // Et ça doit appeler le router
    expect(mockRouter.go).toHaveBeenCalledWith(-1)
  })

  it("utilise l'action annuler personnalisée si elle est founie", async () => {
    const customMock = vi.fn()
    const { emitted } = renderComponent({
      customCancelAction: customMock,
    })

    const user = userEvent.setup()
    mockRouter.go.mockClear()

    await user.click(screen.getByRole('button', { name: /Annuler/i }))

    // Dans ce mode, 'cancel' n'est pas émis par le composant car le code dit de faire uniquement le custom()
    expect(emitted().cancel).toBeFalsy()
    expect(customMock).toHaveBeenCalled()
    expect(mockRouter.go).not.toHaveBeenCalled()
  })

  it('désactive le bouton Annuler et met en chargement le bouton Enregistrer', () => {
    renderComponent({ loading: true })

    // Pour vuetify, un bouton "loading" n'a pas forcement l'attribut natif disabled tout de suite
    const cancelBtn = screen.getByRole('button', { name: /Annuler/i })
    expect(cancelBtn.disabled).toBe(true)

    // L'indicateur de chargement est là pour le submit
    expect(document.querySelector('.v-progress-circular')).not.toBeNull()
  })

  it('désactive le bouton Enregistrer si submitDisabled est true', () => {
    renderComponent({ submitDisabled: true })
    const submitBtn = screen.getByRole('button', { name: /Enregistrer/i })
    expect(submitBtn.disabled).toBe(true)
  })
})
