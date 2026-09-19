import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import FormFileInput from '../FormFileInput.vue'

const vuetify = createVuetify({ components, directives })

// Mock URL API
global.URL.createObjectURL = vi.fn(() => 'blob:mock-url')
global.URL.revokeObjectURL = vi.fn()

describe('FormFileInput.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const createWrapper = (props = {}, provide = {}) => {
    return mount(FormFileInput, {
      props: {
        name: 'testField',
        label: 'Test Label',
        ...props,
      },
      global: {
        plugins: [vuetify],
        provide: {
          isFieldRequired: vi.fn(() => false),
          ...provide,
        },
      },
    })
  }

  it('renders label with no required star when not provided or false', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('Test Label')
    expect(wrapper.find('.required-star').exists()).toBe(false)
  })

  it('renders label with required star when isFieldRequired returns true', async () => {
    const wrapper = createWrapper({}, { isFieldRequired: vi.fn(() => true) })
    expect(wrapper.find('.required-star').exists()).toBe(true)
  })

  it('handles missing validation injections gracefully', () => {
    const wrapper = mount(FormFileInput, {
      props: { name: 'test', label: 'Test Label' },
      global: { plugins: [vuetify] },
    })
    expect(wrapper.text()).toContain('Test Label')
  })

  it('handles file selection and creates preview for image', async () => {
    const wrapper = createWrapper()
    const file = new File(['dummy content'], 'test.png', { type: 'image/png' })

    // Appeler la m�thode
    wrapper.vm.handleFileChange(file)

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([file])
    expect(global.URL.createObjectURL).toHaveBeenCalledWith(file)

    // Simuler un autre fichier image pour tester le revokeObjectURL
    const file2 = new File(['dummy 2'], 'test2.jpg', { type: 'image/jpeg' })
    wrapper.vm.handleFileChange(file2)
    expect(global.URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
  })

  it('does not create preview for non-image files', async () => {
    const wrapper = createWrapper()
    const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' })

    wrapper.vm.handleFileChange(file)
    expect(global.URL.createObjectURL).not.toHaveBeenCalled()
  })

  it('handles null file (cleared input)', async () => {
    const wrapper = createWrapper()
    const file = new File(['dummy content'], 'test.png', { type: 'image/png' })
    wrapper.vm.handleFileChange(file) // create preview

    wrapper.vm.handleFileChange(null) // clear input
    expect(global.URL.revokeObjectURL).toHaveBeenCalled()
  })

  it('unmounts gracefully and cleans up object URL', () => {
    const wrapper = createWrapper()
    const file = new File(['dummy content'], 'test.png', { type: 'image/png' })
    wrapper.vm.handleFileChange(file)

    wrapper.unmount()
    expect(global.URL.revokeObjectURL).toHaveBeenCalled()
  })
})
