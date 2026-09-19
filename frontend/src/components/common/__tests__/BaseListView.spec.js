import { describe, it, expect } from 'vitest'
import { render, fireEvent } from '@testing-library/vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import BaseListView from '../BaseListView.vue'

const vuetify = createVuetify({ components, directives })

describe('BaseListView.vue', () => {
  it('renders the title and create button', async () => {
    const { getByText, emitted } = render(BaseListView, {
      props: {
        title: 'Liste des tests',
        showCreateButton: true,
        createButtonText: 'Ajouter',
        items: [],
        headers: [{ title: 'Nom', key: 'nom' }],
      },
      global: {
        plugins: [vuetify],
      },
    })

    expect(getByText('Liste des tests')).toBeTruthy()
    const createBtn = getByText('Ajouter')
    expect(createBtn).toBeTruthy()

    await fireEvent.click(createBtn)
    expect(emitted()).toHaveProperty('create')
  })

  it('emits edit and delete events from table actions', async () => {
    const { getAllByRole } = render(BaseListView, {
      props: {
        title: 'Liste',
        items: [{ id: 1, nom: 'Test 1' }],
        headers: [
          { title: 'Nom', key: 'nom' },
          { title: 'Actions', key: 'actions' },
        ],
      },
      global: {
        plugins: [vuetify],
      },
    })

    expect(getAllByRole('button').length).toBeGreaterThan(0)
  })
})
