import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import FormSelect from '../FormSelect.vue'

const vuetify = createVuetify({ components, directives })

describe('FormSelect.vue', () => {
  it('renders the label correctly and no required star when not provided or false', () => {
    const { getByText, queryByText } = render(FormSelect, {
      props: {
        fieldName: 'testField',
        label: 'Test Label',
      },
      global: {
        plugins: [vuetify],
        provide: {
          validation: {
            getFieldRules: vi.fn(() => []),
          },
          isFieldRequired: vi.fn(() => false),
        },
      },
    })

    expect(getByText('Test Label')).toBeTruthy()
    expect(queryByText('*')).toBeNull()
  })

  it('renders the required star when isFieldRequired returns true', () => {
    const { getByText } = render(FormSelect, {
      props: {
        fieldName: 'testField',
        label: 'Test Label',
      },
      global: {
        plugins: [vuetify],
        provide: {
          validation: {
            getFieldRules: vi.fn(() => []),
          },
          isFieldRequired: vi.fn(() => true),
        },
      },
    })

    expect(getByText('*')).toBeTruthy()
  })

  it('handles missing validation injections gracefully', () => {
    const { getByText } = render(FormSelect, {
      props: {
        fieldName: 'testField',
        label: 'Test Label',
      },
      global: {
        plugins: [vuetify],
      },
    })

    expect(getByText('Test Label')).toBeTruthy()
  })
})
