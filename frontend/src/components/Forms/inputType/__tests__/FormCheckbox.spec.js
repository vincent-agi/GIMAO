import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import FormCheckbox from '../FormCheckbox.vue'

const vuetify = createVuetify({ components, directives })

describe('FormCheckbox.vue', () => {
  it('renders label with no required star when not provided or false', () => {
    const { getByText, queryByText } = render(FormCheckbox, {
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
    expect(queryByText('Test Label *')).toBeNull()
  })

  it('renders label with required star when isFieldRequired returns true', () => {
    const { getByText } = render(FormCheckbox, {
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

    expect(getByText('Test Label *')).toBeTruthy()
  })

  it('handles missing validation injections gracefully', () => {
    const { getByText } = render(FormCheckbox, {
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
