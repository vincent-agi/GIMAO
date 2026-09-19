import { describe, it, expect } from 'vitest'
import {
  getStatusColor,
  getStatusLabel,
  getFailureLevelColor,
  getInterventionStatusColor,
  formatDate,
  formatDateTime,
  formatDuration,
  toTimeInputValue,
} from '../helpers'
import { EQUIPMENT_STATUS, EQUIPMENT_STATUS_COLORS, INTERVENTION_STATUS_COLORS } from '../constants'

describe('helpers.js', () => {
  describe('Fonctions de couleurs et libellés', () => {
    it('getStatusColor retourne la bonne couleur ou "grey"', () => {
      // Test d'une clé existante
      const knownKey = Object.keys(EQUIPMENT_STATUS_COLORS)[0]
      if (knownKey) {
        expect(getStatusColor(knownKey)).toBe(EQUIPMENT_STATUS_COLORS[knownKey])
      }
      expect(getStatusColor('XXX_UNKNOWN')).toBe('grey')
    })

    it('getStatusLabel retourne le bon libellé ou "Inconnu"', () => {
      const knownKey = Object.keys(EQUIPMENT_STATUS)[0]
      if (knownKey) {
        expect(getStatusLabel(knownKey)).toBe(EQUIPMENT_STATUS[knownKey])
      }
      expect(getStatusLabel('XXX_UNKNOWN')).toBe('Inconnu')
    })

    it('getFailureLevelColor fonctionne (alias interne)', () => {
      expect(getFailureLevelColor('XXX_UNKNOWN')).toBe('grey')
    })

    it('getInterventionStatusColor fonctionne comme prevu', () => {
      const knownKey = Object.keys(INTERVENTION_STATUS_COLORS)[0]
      if (knownKey) {
        expect(getInterventionStatusColor(knownKey)).toBe(INTERVENTION_STATUS_COLORS[knownKey])
      }
      expect(getInterventionStatusColor('XXX_UNKNOWN')).toBe('grey')
    })
  })

  describe('Fonctions de formatage', () => {
    it('formatDate formate correctement une ISO string', () => {
      expect(formatDate(null)).toBe('Non spécifié')
      const formatted = formatDate('2026-03-30T10:00:00Z')
      expect(formatted).toBe('30/03/2026')
    })

    it('formatDateTime formate la date et heure', () => {
      expect(formatDateTime('')).toBe('Non spécifié')
      const formatted = formatDateTime('2026-03-30T10:30:00Z')
      // Note : peut varier selon le fuseau horaire du serveur.
      // On vérifie quelques inclusions clés.
      expect(formatted).toContain('30/03/2026')
    })

    it('formatDuration décompose correctement X jours hh:mm:ss', () => {
      expect(formatDuration(null)).toBe('Non spécifié')

      // Cas simple
      expect(formatDuration('02:30:15')).toBe('2h 30m 15s')
      // Cas avec Jours
      expect(formatDuration('1 02:00:00')).toBe('26h') // 1 jour + 2 heures, min/sec à 0 sont tronqués
      // Si on passe une chaîne malformée
      expect(formatDuration('bad string')).toBe('bad string')
    })

    it('toTimeInputValue extrait "HH:MM"', () => {
      expect(toTimeInputValue(null)).toBe('')
      expect(toTimeInputValue(undefined)).toBe('')
      expect(toTimeInputValue('')).toBe('')

      expect(toTimeInputValue('02:30:15')).toBe('2:30')
      expect(toTimeInputValue('1 02:30:00')).toBe('26:30')
      expect(toTimeInputValue('bad sequence')).toBe('')
    })
  })
})
