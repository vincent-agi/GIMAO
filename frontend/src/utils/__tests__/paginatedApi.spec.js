import { describe, it, expect } from 'vitest'
import { extractItems, isPaginatedPayload, fetchAllPages } from '../paginatedApi'

describe('paginatedApi.js', () => {
  describe('extractItems', () => {
    it('retourne le tableau tel quel si le payload est un tableau', () => {
      expect(extractItems([1, 2, 3])).toEqual([1, 2, 3])
    })

    it('retourne payload.results si le payload est paginé', () => {
      expect(extractItems({ results: [1, 2], count: 2 })).toEqual([1, 2])
    })

    it('retourne un tableau vide pour un payload invalide', () => {
      expect(extractItems(null)).toEqual([])
      expect(extractItems({})).toEqual([])
    })
  })

  describe('isPaginatedPayload', () => {
    it('identifie correctement un payload paginé', () => {
      expect(isPaginatedPayload({ results: [], count: 0 })).toBe(true)
    })

    it('retourne faux pour des structures non paginées', () => {
      expect(isPaginatedPayload([])).toBe(false)
      expect(isPaginatedPayload(null)).toBe(false)
      expect(isPaginatedPayload({ results: [] })).toBe(false) // manque count
    })
  })

  describe('fetchAllPages', () => {
    it("retourne les éléments d'un endpoint non paginé", async () => {
      const mockApi = {
        get: async () => [1, 2, 3],
      }
      const res = await fetchAllPages(mockApi, '/test')
      expect(res).toEqual([1, 2, 3])
    })

    it('retourne la première page si une seule page existe', async () => {
      const mockApi = {
        get: async () => ({
          count: 2,
          results: [{ id: 1 }, { id: 2 }],
        }),
      }
      const res = await fetchAllPages(mockApi, '/test')
      expect(res).toEqual([{ id: 1 }, { id: 2 }])
    })

    it("récupère toutes les pages en parallèle si plus d'une page", async () => {
      const mockApi = {
        get: async (endpoint, params) => {
          if (params.page === 1) {
            return { count: 5, results: [1, 2] } // pageSize default is 100 but let's mock it
          }
          if (params.page === 2) {
            return { count: 5, results: [3, 4] }
          }
          if (params.page === 3) {
            return { count: 5, results: [5] }
          }
        },
      }
      const res = await fetchAllPages(mockApi, '/test', { pageSize: 2 })
      expect(res).toEqual([1, 2, 3, 4, 5])
    })
  })
})
