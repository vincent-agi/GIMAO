import { describe, it, expect } from 'vitest'
import { useFormValidation } from '../useFormValidation'

describe('useFormValidation.js', () => {
  it('gère un formulaire simple avec règles sous forme de tableau (strings et objects)', () => {
    const schema = {
      username: ['required', { name: 'minLength', params: [3], message: 'Trop court' }],
      age: [{ name: 'numeric' }],
    }
    const { getFieldRules, validateAll, hasFieldError, getFieldErrors, clearErrors } =
      useFormValidation(schema)

    // Test getFieldRules
    const rules = getFieldRules('username')
    expect(rules.length).toBe(2)

    // Test validateAll
    const isValid1 = validateAll({ username: 'ab', age: 'dix' })
    expect(isValid1).toBe(false)
    expect(hasFieldError('username')).toBe(true)
    expect(getFieldErrors('username')[0]).toBe('Trop court')
    expect(hasFieldError('age')).toBe(true)

    // Valide correct
    const isValid2 = validateAll({ username: 'abcd', age: '10' })
    expect(isValid2).toBe(true)
    expect(hasFieldError('username')).toBeFalsy()

    clearErrors()
    expect(hasFieldError('username')).toBeFalsy()
  })

  it("gère un formulaire simple avec règles sous forme d'objet", () => {
    const schema = {
      emailField: {
        required: "L'email est obligatoire",
        email: true,
      },
      amount: {
        required: true,
        numeric: true,
        positive: true,
        min: 10,
        max: { value: 100, message: 'Max 100' },
      },
      code: {
        pattern: { value: /^[A-Z]+$/, message: 'Seulement majuscules' },
      },
      password: {
        minLength: 5,
        maxLength: 10,
      },
      customField: {
        custom: (val) => val === 'secret' || 'Incorrect',
      },
    }
    const { validateAll, errors } = useFormValidation(schema)

    const isInvalid = validateAll({
      emailField: 'bad',
      amount: -5,
      code: 'abc',
      password: 'bad',
      customField: 'wrong',
    })

    expect(isInvalid).toBe(false)
    expect(errors.value.emailField[0]).toBe('Email invalide')
    expect(errors.value.amount.length).toBeGreaterThan(0) // positive error, min error... Note: validateField stops at first error usually
    expect(errors.value.code[0]).toBe('Seulement majuscules')
    expect(errors.value.password[0]).toMatch(/Minimum 5 caract/i)
    expect(errors.value.customField[0]).toBe('Incorrect')

    const isValid = validateAll({
      emailField: 'test@test.com',
      amount: 50,
      code: 'ABC',
      password: 'password1',
      customField: 'secret',
    })
    expect(isValid).toBe(true)
  })

  it('gère les règles customs en fonction directe', () => {
    const customRule = (val) => val === 'ok' || 'Pas ok'
    const schema = {
      champ: [customRule],
    }
    const { validateAll, errors } = useFormValidation(schema)

    expect(validateAll({ champ: 'ko' })).toBe(false)
    expect(errors.value.champ[0]).toBe('Pas ok')

    expect(validateAll({ champ: 'ok' })).toBe(true)
  })

  it('gère les formulaires multi-steps', () => {
    const schema = {
      step1: {
        firstName: { required: true },
      },
      step2: {
        lastName: { required: true },
      },
    }
    const { validateStep, validateAll, currentStep } = useFormValidation(schema, { initialStep: 1 })

    expect(currentStep.value).toBe(1)

    // Validation step 1
    let isStep1Valid = validateStep(1, { firstName: '', lastName: '' })
    expect(isStep1Valid).toBe(false)

    isStep1Valid = validateStep(1, { firstName: 'Jean', lastName: '' })
    expect(isStep1Valid).toBe(true)

    // Validation totale
    const isAllValid = validateAll({ firstName: 'Jean', lastName: '' })
    expect(isAllValid).toBe(false)

    const isAllValid2 = validateAll({ firstName: 'Jean', lastName: 'Dupont' })
    expect(isAllValid2).toBe(true)
  })

  it('gère le cas où un champ est absent du schéma', () => {
    const { getFieldRules } = useFormValidation({})
    expect(getFieldRules('unknown')).toEqual([])
  })
})
