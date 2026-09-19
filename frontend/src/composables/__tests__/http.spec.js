import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import api from '../http'
import MockAdapter from 'axios-mock-adapter'

describe('http.js interceptors', () => {
  let mock

  beforeEach(() => {
    mock = new MockAdapter(api)
    // Clear localStorage
    localStorage.clear()
    // By default, jsdom changes to window.location don't fail, but we'll mock if needed
    delete window.location
    window.location = { href: '' }
  })

  afterEach(() => {
    mock.restore()
  })

  it('ajoute le token au header si présent dans localStorage', async () => {
    localStorage.setItem('token', 'MY_SECRET_TOKEN')

    mock.onGet('/test').reply((config) => {
      return [200, { headerToken: config.headers.Authorization }]
    })

    const response = await api.get('/test')
    expect(response.data.headerToken).toBe('Bearer MY_SECRET_TOKEN')
  })

  it("n'ajoute pas le token si absent du localStorage", async () => {
    mock.onGet('/test').reply((config) => {
      return [200, { headerToken: config.headers.Authorization }]
    })

    const response = await api.get('/test')
    expect(response.data.headerToken).toBeUndefined()
  })

  it("redirige vers /login et nettoie le localStorage en cas d'erreur 401", async () => {
    localStorage.setItem('token', 'bad_token')
    localStorage.setItem('user', 'my_user')
    localStorage.setItem('authTimestamp', '123')

    mock.onGet('/protected').reply(401)

    try {
      await api.get('/protected')
    } catch (error) {
      expect(error.response.status).toBe(401)
    }

    expect(localStorage.getItem('token')).toBeNull()
    expect(localStorage.getItem('user')).toBeNull()
    expect(localStorage.getItem('authTimestamp')).toBeNull()
    expect(window.location.href).toBe('/login')
  })

  it('laisse passer les autres erreurs sans rediriger', async () => {
    mock.onGet('/error').reply(500)

    try {
      await api.get('/error')
    } catch (error) {
      expect(error.response.status).toBe(500)
    }

    expect(window.location.href).not.toBe('/login')
  })
})
