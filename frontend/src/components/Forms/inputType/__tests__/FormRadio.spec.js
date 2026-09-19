import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import FormRadio from '../FormRadio.vue'

const vuetify = createVuetify({ components, directives })

describe('FormRadio.vue', () => {
  it('renders label with no required star when not provided or false', () => {
    const { getByText, queryByText } = render(FormRadio, {
      props: {
        fieldName: 'testField',
        label: 'Test Label',
        items: ['A', 'B'],
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
    expect(getByText('A')).toBeTruthy()
    expect(getByText('B')).toBeTruthy()
  })

  it('renders label with required star when isFieldRequired returns true', () => {
    const { getByText } = render(FormRadio, {
      props: {
        fieldName: 'testField',
        label: 'Test Label',
        items: [{ title: 'Opt 1', value: '1' }],
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
    expect(getByText('Opt 1')).toBeTruthy()
  })

  it('handles missing validation injections gracefully', () => {
    const { getByText } = render(FormRadio, {
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
