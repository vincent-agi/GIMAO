import { EQUIPMENT_STATUS, EQUIPMENT_STATUS_COLORS, INTERVENTION_STATUS_COLORS } from './constants'

// ============================================
// FONCTIONS DE COULEURS
// ============================================

/**
 * Retourne la couleur associée à un statut d'équipement
 * @param {string} status - Le statut de l'équipement
 * @returns {string} La couleur correspondante
 */
export function getStatusColor(code) {
  return EQUIPMENT_STATUS_COLORS[code] || 'grey'
}

/**
 * Retourne le libellé associé à un code de statut d'équipement
 * @param {string} code
 * @returns  {string} Le libellé du statut
 */
export function getStatusLabel(code) {
  return EQUIPMENT_STATUS[code] || 'Inconnu'
}

/**
 * Retourne la couleur associée à un niveau de défaillance
 * @param {string} level - Le niveau de défaillance
 * @returns {string} La couleur correspondante
 */
export function getFailureLevelColor(level) {
  return EQUIPMENT_STATUS_COLORS[level] || 'grey'
}

/**
 * Retourne la couleur (token Vuetify) associée à un statut de bon de travail
 * @param {string} statusCode
 * @returns {string}
 */
export function getInterventionStatusColor(statusCode) {
  return INTERVENTION_STATUS_COLORS[statusCode] || 'grey'
}

// ============================================
// FONCTIONS DE FORMATAGE
// ============================================

/**
 * Formate une date au format français (JJ/MM/AAAA)
 * @param {string} dateString - La date à formater
 * @returns {string} La date formatée
 */
export function formatDate(dateString) {
  if (!dateString) return 'Non spécifié'
  const date = new Date(dateString)
  return date.toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

/**
 * Formate une date avec l'heure au format français
 * @param {string} dateString - La date à formater
 * @returns {string} La date et l'heure formatées
 */
export function formatDateTime(dateString) {
  if (!dateString) return 'Non spécifié'
  const date = new Date(dateString)
  return date.toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * Formate un timedelta (en secondes) en une chaîne lisible (ex: "1h 30m")
 * @param {timedelta} hour - La durée à formater au format HH:MM:SS
 * @returns {string} La durée formatée
 */
export function formatDuration(duration) {
  if (!duration) return 'Non spécifié'

  const rawValue = String(duration).trim()
  const match = rawValue.match(/^(?:(\d+)\s+)?(\d+):([0-5]\d)(?::([0-5]\d)(?:\.\d+)?)?$/)
  if (!match) return rawValue

  const days = Number(match[1] || 0)
  const hours = Number(match[2] || 0)
  const minutes = Number(match[3] || 0)
  const seconds = Number(match[4] || 0)
  const totalHours = days * 24 + hours

  let result = ''
  if (totalHours > 0) result += `${totalHours}h `
  if (minutes > 0) result += `${minutes}m `
  if (seconds > 0) result += `${seconds}s`

  if (!result.trim()) return '0m'

  return result.trim()
}

/**
 * Convertit une durée au format "X jours Y:MM" en "HH:MM" pour les inputs de type time
 * @param {string} value - La durée à convertir
 * @returns {string} La durée au format "HH:MM" ou une chaîne vide si le format est invalide
 */
export const toTimeInputValue = (value) => {
  if (value === null || value === undefined) return ''
  const rawValue = String(value).trim()
  if (!rawValue) return ''

  const match = rawValue.match(/^(?:(\d+)\s+)?(\d+):(\d{2})(?::\d{2}(?:\.\d+)?)?$/)
  if (!match) return ''

  const days = Number(match[1] || 0)
  const hours = Number(match[2] || 0)
  const minutes = Number(match[3] || 0)
  if (!Number.isFinite(days) || !Number.isFinite(hours) || !Number.isFinite(minutes)) return ''

  const totalHours = days * 24 + hours
  if (minutes > 59) return ''

  return `${String(totalHours)}:${String(minutes).padStart(2, '0')}`
}

export const formatCalendarDate = (value) => {
  if (value == null || value === '') return '—'
  if (typeof value === 'number' && value <= 0) return '—'

  let date

  if (typeof value === 'string') {
    date = new Date(value + 'T00:00:00')
  } else if (typeof value === 'number' && value > 10000000000) {
    date = new Date(value)
  } else if (typeof value === 'number') {
    const ORDINAL_EPOCH = 719162
    const daysFromEpoch = value - ORDINAL_EPOCH
    date = new Date(Date.UTC(1970, 0, 1 + daysFromEpoch))
  } else {
    return '—'
  }

  if (isNaN(date.getTime())) return '—'

  return date.toLocaleDateString('fr-FR', { timeZone: 'UTC' })
}
