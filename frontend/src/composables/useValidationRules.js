/**
 * Composable fournissant des règles de validation réutilisables pour Vuetify
 * Compatible avec v-text-field, v-select, etc. via la prop :rules
 */

export function useValidationRules() {
  /**
   * Règle : Champ requis
   */
  const required = (message = 'Ce champ est requis') => {
    return (value) => {
      // Pour les tableaux (comme v-select multiple)
      if (Array.isArray(value)) {
        return value.length > 0 || message
      }
      // Pour les valeurs primitives
      return !!value || value === 0 || message
    }
  }

  /**
   * Règle : Email valide
   */
  const email = (message = 'Email invalide') => {
    return (value) => {
      if (!value) return true // Permet les champs vides (utiliser required séparément)
      const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/
      return pattern.test(value) || message
    }
  }

  /**
   * Règle : Longueur minimum
   */
  const minLength = (min, message = null) => {
    return (value) => {
      if (!value) return true
      const msg = message || `Minimum ${min} caractères`
      return value.length >= min || msg
    }
  }

  /**
   * Règle : Longueur maximum
   */
  const maxLength = (max, message = null) => {
    return (value) => {
      if (!value) return true
      const msg = message || `Maximum ${max} caractères`
      return value.length <= max || msg
    }
  }

  /**
   * Règle : Nombre valide
   */
  const numeric = (message = 'Doit être un nombre') => {
    return (value) => {
      if (value === null || value === undefined || value === '') return true
      const stringValue = String(value).trim()
      const pattern = /^-?\d+(\.\d+)?$/
      if (!pattern.test(stringValue)) return message
      const numValue = Number(stringValue)
      return (!isNaN(numValue) && isFinite(numValue)) || message
    }
  }

  /**
   * Règle : Nombre positif
   */
  const positive = (message = 'Doit être positif') => {
    return (value) => {
      // Accepter uniquement si vide (sera géré par required si nécessaire)
      if (value === null || value === undefined || value === '') return true
      const numValue = Number(value)
      // Rejeter si NaN ou négatif
      if (isNaN(numValue) || !isFinite(numValue)) return message
      return numValue >= 0 || message
    }
  }

  /**
   * Règle : Valeur minimum
   */
  const min = (minValue, message = null) => {
    return (value) => {
      if (!value && value !== 0) return true
      const msg = message || `Doit être au moins ${minValue}`
      return parseFloat(value) >= minValue || msg
    }
  }

  /**
   * Règle : Valeur maximum
   */
  const max = (maxValue, message = null) => {
    return (value) => {
      if (!value && value !== 0) return true
      const msg = message || `Doit être au maximum ${maxValue}`
      return parseFloat(value) <= maxValue || msg
    }
  }

  /**
   * Règle : Téléphone français
   */
  const phone = (message = 'Numéro de téléphone invalide') => {
    return (value) => {
      if (!value) return true
      const pattern = /^(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}$/
      return pattern.test(value) || message
    }
  }

  /**
   * Règle : URL valide
   */
  const url = (message = 'URL invalide') => {
    return (value) => {
      if (!value) return true
      try {
        new URL(value)
        return true
      } catch {
        return message
      }
    }
  }

  /**
   * Règle : Date valide
   */
  const date = (message = 'Date invalide') => {
    return (value) => {
      if (!value) return true
      const d = new Date(value)
      return !isNaN(d.getTime()) || message
    }
  }

  /**
   * Règle : Date dans le futur
   */
  const futureDate = (message = 'La date doit être dans le futur') => {
    return (value) => {
      if (!value) return true
      const d = new Date(value)
      return d > new Date() || message
    }
  }

  /**
   * Règle : Date dans le passé
   */
  const pastDate = (message = 'La date doit être dans le passé') => {
    return (value) => {
      if (!value) return true
      const d = new Date(value)
      return d < new Date() || message
    }
  }

  /**
   * Règle : Correspondance avec une regex personnalisée
   */
  const pattern = (regex, message = 'Format invalide') => {
    return (value) => {
      if (!value) return true
      return regex.test(value) || message
    }
  }

  /**
   * Règle : Taille de fichier maximum (en Mo)
   */
  const fileSize = (maxSizeMB, message = null) => {
    return (file) => {
      if (!file) return true
      const msg = message || `Taille maximum : ${maxSizeMB}Mo`
      if (file instanceof File) {
        const sizeMB = file.size / 1024 / 1024
        return sizeMB <= maxSizeMB || msg
      }
      return true
    }
  }

  /**
   * Règle : Type de fichier autorisé
   */
  const fileType = (allowedTypes, message = null) => {
    return (file) => {
      if (!file) return true
      const msg = message || `Types autorisés : ${allowedTypes.join(', ')}`
      if (file instanceof File) {
        return allowedTypes.some((type) => file.type.includes(type)) || msg
      }
      return true
    }
  }

  /**
   * Règle : Correspondance entre deux champs (ex: confirmation mot de passe)
   */
  const match = (otherValue, fieldName = 'champ', message = null) => {
    return (value) => {
      const msg = message || `Doit correspondre au ${fieldName}`
      return value === otherValue || msg
    }
  }

  /**
   * Règle : Valeur unique dans une liste
   */
  const unique = (list, message = 'Cette valeur existe déjà') => {
    return (value) => {
      if (!value) return true
      return !list.includes(value) || message
    }
  }

  return {
    required,
    email,
    minLength,
    maxLength,
    numeric,
    positive,
    min,
    max,
    phone,
    url,
    date,
    futureDate,
    pastDate,
    pattern,
    fileSize,
    fileType,
    match,
    unique,
  }
}
