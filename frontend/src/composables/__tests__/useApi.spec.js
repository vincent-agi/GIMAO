import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import MockAdapter from 'axios-mock-adapter'
import api from '../http'
import { useApi } from '../useApi'

describe('useApi', () => {
  let mock

  beforeEach(() => {
    mock = new MockAdapter(api)
  })

  afterEach(() => {
    mock.restore()
  })

  it('get() retourne response.data et met a jour data/loading/error', async () => {
    mock.onGet('/equipements/').reply(200, { count: 2 })

    const { data, loading, error, get } = useApi()
    const result = await get('/equipements/')

    expect(result).toEqual({ count: 2 })
    expect(data.value).toEqual({ count: 2 })
    expect(loading.value).toBe(false)
    expect(error.value).toBeNull()
  })

  it('get() met loading a true pendant la requete', async () => {
    mock.onGet('/lent/').reply(() => {
      return new Promise((resolve) => setTimeout(() => resolve([200, {}]), 10))
    })

    const { loading, get } = useApi()
    const promise = get('/lent/')

    expect(loading.value).toBe(true)
    await promise
    expect(loading.value).toBe(false)
  })

  it('post() envoie le body et retourne response.data', async () => {
    mock.onPost('/demandes/', { nom: 'Panne moteur' }).reply(201, { id: 42 })

    const { post } = useApi()
    const result = await post('/demandes/', { nom: 'Panne moteur' })

    expect(result).toEqual({ id: 42 })
  })

  it('remove() effectue un DELETE', async () => {
    mock.onDelete('/equipements/5/').reply(204)

    const { remove } = useApi()
    await expect(remove('/equipements/5/')).resolves.toBeUndefined()
  })

  it('propage une erreur et renseigne error.value quand la requete echoue', async () => {
    mock.onGet('/erreur/').reply(500, { detail: 'Erreur serveur' })

    const { error, get } = useApi()

    await expect(get('/erreur/')).rejects.toBeTruthy()
    expect(error.value).toEqual({ detail: 'Erreur serveur' })
  })

  it('getRaw() retourne la reponse Axios complete (headers inclus)', async () => {
    mock.onGet('/export/').reply(200, new Blob(['contenu']), {
      'content-disposition': 'attachment; filename="export.csv"',
    })

    const { getRaw } = useApi()
    const response = await getRaw('/export/', { exportType: 'eq' }, { responseType: 'blob' })

    expect(response.headers['content-disposition']).toContain('export.csv')
    expect(response.data).toBeInstanceOf(Blob)
  })

  it('getRaw() transmet les query params', async () => {
    mock.onGet('/export/').reply((config) => {
      expect(config.params).toEqual({ exportType: 'eq' })
      return [200, {}]
    })

    const { getRaw } = useApi()
    await getRaw('/export/', { exportType: 'eq' })
  })
})
