import { render, screen } from '@testing-library/vue'
import userEvent from '@testing-library/user-event'
import { describe, it, expect } from 'vitest'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

import FormAlert from '../FormAlert.vue'

const vuetify = createVuetify({ components, directives })

const renderComponent = (props = {}) => {
  return render(FormAlert, {
    props,
    global: {
      plugins: [vuetify],
    },
  })
}

describe('FormAlert.vue', () => {
  it("ne s'affiche pas si le message est vide", () => {
    // GIVEN un composant avec message vide (comportement par défaut)
    renderComponent({ message: '' })

    // THEN l'alerte n'existe pas dans le DOM
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('affiche le message passé en props', () => {
    // GIVEN un composant avec un message spécifique
    renderComponent({ message: 'Identifiants invalides' })

    // THEN le message est visible
    expect(screen.getByText('Identifiants invalides')).toBeDefined()
  })

  it('affiche un bouton de fermeture si dismissible est true', async () => {
    // GIVEN une alerte dismissible
    const { emitted } = renderComponent({
      message: 'Erreur',
      dismissible: true,
    })

    // On trouve le bouton de fermeture (Vuetify met souvent aria-label="Close")
    const closeButton = screen.getByRole('button', { name: /Close|Fermer/i })
    expect(closeButton).toBeDefined()

    // WHEN on clique dessus
    const user = userEvent.setup()
    await user.click(closeButton)

    // THEN un événement "close" est émis
    expect(emitted().close).toBeTruthy()
  })
})
