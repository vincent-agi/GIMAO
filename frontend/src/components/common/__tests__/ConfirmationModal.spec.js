import { render, screen } from '@testing-library/vue'
import userEvent from '@testing-library/user-event'
import { describe, it, expect } from 'vitest'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

import ConfirmationModal from '../ConfirmationModal.vue'

const vuetify = createVuetify({ components, directives })

// Il faut attacher Vue au document car v-dialog est téléporté à la racine dans Vuetify
const renderComponent = (props = {}) => {
  return render(ConfirmationModal, {
    props,
    global: {
      plugins: [vuetify],
    },
  })
}

describe('ConfirmationModal.vue', () => {
  // Option pour nettoyer le DOM vu que v-dialog téléporte (Testing Library nettoie, mais la transition peut laisser des traces)

  it('ne rend pas le contenu de la modale si modelValue est false (fermé par defaut)', () => {
    renderComponent({ modelValue: false })

    // Le texte de la modale ne doit pas être présent sur l'écran
    expect(screen.queryByText('Confirmation requise')).toBeNull()
  })

  it("affiche le titre et le message quand la modale s'ouvre", async () => {
    // Rend avec true
    renderComponent({
      modelValue: true,
      title: 'Suppression',
      message: 'Voulez-vous supprimer ce fichier ?',
    })

    // Recherche de la modale. Les modals Vuetify 3 sont insérées direct avec aria-attributes
    const modalText = await screen.findByText('Voulez-vous supprimer ce fichier ?')
    expect(modalText).not.toBeNull()

    expect(screen.getByText('Suppression')).not.toBeNull()
  })

  it("émet l'événement confirm quand le bouton Confirmer est cliqué", async () => {
    const { emitted } = renderComponent({ modelValue: true })
    const user = userEvent.setup()

    // Le bouton a le texte "Confirmer" par défaut
    const confirmButton = await screen.findByRole('button', { name: /Confirmer/i })
    await user.click(confirmButton)

    expect(emitted().confirm).toBeTruthy()
    expect(emitted().confirm.length).toBe(1)
  })

  it('émet cancel et met à jour v-model quand le bouton Annuler est cliqué', async () => {
    const { emitted } = renderComponent({ modelValue: true })
    const user = userEvent.setup()

    // Le bouton a le texte "Annuler" par défaut
    const cancelButton = await screen.findByRole('button', { name: /Annuler/i })
    await user.click(cancelButton)

    // Vérifie qu'il envoie l'événement d'annulation standard
    expect(emitted().cancel).toBeTruthy()

    // Vérifie qu'il ferme la modale en envoyant false sur v-model
    expect(emitted()['update:modelValue'][0]).toEqual([false])
  })

  it('Affiche les textes des boutons personnalisés', async () => {
    renderComponent({
      modelValue: true,
      confirmText: 'Oui, détruire',
      cancelText: 'Non, garder',
    })

    expect(await screen.findByRole('button', { name: 'Oui, détruire' })).toBeDefined()
    expect(await screen.findByRole('button', { name: 'Non, garder' })).toBeDefined()
  })
})
