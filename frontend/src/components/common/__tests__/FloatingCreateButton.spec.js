import { render, screen } from '@testing-library/vue'
import userEvent from '@testing-library/user-event'
import { describe, it, expect } from 'vitest'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

import FloatingCreateButton from '../FloatingCreateButton.vue'

const vuetify = createVuetify({ components, directives })

const renderComponent = (props = {}) => {
  return render(FloatingCreateButton, {
    props,
    global: {
      plugins: [vuetify],
    },
  })
}

describe('FloatingCreateButton.vue', () => {
  it("s'affiche par défaut quand visible est true", () => {
    // GIVEN le composant rendu par défaut
    renderComponent()

    // THEN le bouton doit être présent (par défaut une icône ou un bouton)
    const button = screen.getByRole('button')
    expect(button).not.toBeNull()
  })

  it('ne se rend pas dans le DOM si visible est false', () => {
    // GIVEN le composant monté avec visible: false
    renderComponent({ visible: false })

    // THEN aucun bouton n'est trouvé
    const button = screen.queryByRole('button')
    expect(button).toBeNull()
  })

  it("émet l'événement click quand l'utilisateur interagit", async () => {
    // GIVEN le bouton bien visible
    const { emitted } = renderComponent()
    const user = userEvent.setup()

    // WHEN on clique sur le bouton
    const button = screen.getByRole('button')
    await user.click(button)

    // THEN l'événement `click` doit être présent dans l'objet emitted
    expect(emitted().click).toBeTruthy()
    expect(emitted().click.length).toBe(1)
  })
})
