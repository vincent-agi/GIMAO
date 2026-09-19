import { describe, it, expect } from 'vitest'
import { useValidationRules } from '../useValidationRules'

describe('useValidationRules.js', () => {
  const rules = useValidationRules()

  it('required rule', () => {
    const fn = rules.required('Custom error')
    expect(fn('text')).toBe(true)
    expect(fn(0)).toBe(true)
    expect(fn(['item'])).toBe(true)
    expect(fn([])).toBe('Custom error')
    expect(fn('')).toBe('Custom error')
    expect(fn(null)).toBe('Custom error')
    expect(fn(undefined)).toBe('Custom error')
  })

  it('email rule', () => {
    const fn = rules.email()
    expect(fn('')).toBe(true) // allowed if empty
    expect(fn('test@test.fr')).toBe(true)
    expect(typeof fn('bademail')).toBe('string')
  })

  it('minLength and maxLength rules', () => {
    const fnMin = rules.minLength(3)
    expect(fnMin('')).toBe(true)
    expect(fnMin('abc')).toBe(true)
    expect(typeof fnMin('a')).toBe('string')

    const fnMax = rules.maxLength(5)
    expect(fnMax('')).toBe(true)
    expect(fnMax('abcde')).toBe(true)
    expect(typeof fnMax('abcdef')).toBe('string')
  })

  it('numeric and positive rules', () => {
    const fnNum = rules.numeric()
    expect(fnNum('')).toBe(true)
    expect(fnNum('123')).toBe(true)
    expect(fnNum('-12.5')).toBe(true)
    expect(typeof fnNum('abc')).toBe('string')

    const fnPos = rules.positive()
    expect(fnPos('')).toBe(true)
    expect(fnPos(10)).toBe(true)
    expect(fnPos('5.5')).toBe(true)
    expect(fnPos(0)).toBe(true)
    expect(typeof fnPos(-1)).toBe('string')
    expect(typeof fnPos('abc')).toBe('string')
  })

  it('min and max rules', () => {
    const fnMin = rules.min(10)
    expect(fnMin('')).toBe(true)
    expect(fnMin(12)).toBe(true)
    expect(fnMin('10')).toBe(true)
    expect(typeof fnMin(5)).toBe('string')

    const fnMax = rules.max(10)
    expect(fnMax('')).toBe(true)
    expect(fnMax(5)).toBe(true)
    expect(typeof fnMax(12)).toBe('string')
  })

  it('phone rule', () => {
    const fn = rules.phone()
    expect(fn('')).toBe(true)
    expect(fn('0612345678')).toBe(true)
    expect(fn('+33612345678')).toBe(true)
    expect(typeof fn('1234')).toBe('string')
  })

  it('url rule', () => {
    const fn = rules.url()
    expect(fn('')).toBe(true)
    expect(fn('http://google.com')).toBe(true)
    expect(typeof fn('not-a-url')).toBe('string')
  })

  it('date, futureDate, pastDate rules', () => {
    const fnD = rules.date()
    expect(fnD('')).toBe(true)
    expect(fnD('2026-01-01')).toBe(true)
    expect(typeof fnD('abc')).toBe('string')

    const fnFut = rules.futureDate()
    expect(fnFut('')).toBe(true)
    expect(fnFut('2099-01-01')).toBe(true)
    expect(typeof fnFut('2000-01-01')).toBe('string')

    const fnPast = rules.pastDate()
    expect(fnPast('')).toBe(true)
    expect(fnPast('2000-01-01')).toBe(true)
    expect(typeof fnPast('2099-01-01')).toBe('string')
  })

  it('pattern rule', () => {
    const fn = rules.pattern(/^[A-Z]+$/)
    expect(fn('')).toBe(true)
    expect(fn('ABC')).toBe(true)
    expect(typeof fn('abc')).toBe('string')
  })

  it('fileSize and fileType rules', () => {
    const fnSize = rules.fileSize(2)
    expect(fnSize(null)).toBe(true)
    expect(fnSize(new File([''], 'test.txt'))).toBe(true) // file size 0
    expect(typeof fnSize(new File([new ArrayBuffer(3 * 1024 * 1024)], 'big.txt'))).toBe('string')

    const fnType = rules.fileType(['image/jpeg'])
    expect(fnType(null)).toBe(true)
    const validFile = new File([''], 'test.jpg', { type: 'image/jpeg' })
    expect(fnType(validFile)).toBe(true)
    const invalidFile = new File([''], 'test.txt', { type: 'text/plain' })
    expect(typeof fnType(invalidFile)).toBe('string')
  })

  it('match and unique rules', () => {
    const fnMatch = rules.match('SECRET')
    expect(fnMatch('SECRET')).toBe(true)
    expect(typeof fnMatch('OTHER')).toBe('string')

    const fnUnique = rules.unique(['A', 'B'])
    expect(fnUnique('')).toBe(true)
    expect(fnUnique('C')).toBe(true)
    expect(typeof fnUnique('A')).toBe('string')
  })
})
