/**
 * Outils de traduction d'erreurs Django REST Framework (DRF) -> messages lisibles en français.
 *
 * Objectif: exploiter err.response.data (axios) pour afficher un message utile à l'utilisateur.
 */

const FIELD_LABELS = {
  nomUtilisateur: "Nom d'utilisateur",
  prenom: 'Prénom',
  nomFamille: 'Nom de famille',
  email: 'Email',
  role: 'Rôle',
  actif: 'Compte actif',
  motDePasse: 'Mot de passe',
  motDePasse_confirmation: 'Confirmation du mot de passe',
}

function asStringArray(value) {
  if (value == null) return []
  if (Array.isArray(value)) return value.map((v) => String(v))
  if (typeof value === 'object') return []
  return [String(value)]
}

function normalizeDrfErrorData(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    return {}
  }
  const out = {}
  for (const [key, val] of Object.entries(data)) {
    out[key] = asStringArray(val)
  }
  return out
}

function anyMatch(messages, regex) {
  return (messages || []).some((m) => regex.test(String(m)))
}

function isUniqueViolation(messages) {
  return anyMatch(
    messages,
    /(unique|already exists|already used|has already|existe d[eé]j[aà]|d[eé]j[aà] utilis[eé]|duplicate)/i
  )
}

function isRequiredViolation(messages) {
  return anyMatch(
    messages,
    /(this field is required|required|obligatoire|may not be blank|ne peut pas [eê]tre vide)/i
  )
}

function isInvalidEmail(messages) {
  return anyMatch(messages, /(valid email|email address|adresse e-?mail invalide)/i)
}

function isInvalidPk(messages) {
  return anyMatch(messages, /(invalid pk|does not exist|n'existe pas|invalide)/i)
}

function firstMeaningfulMessage(errors) {
  for (const key of Object.keys(errors)) {
    const msgs = errors[key]
    if (Array.isArray(msgs) && msgs.length) {
      return msgs[0]
    }
  }
  return null
}

/**
 * Retourne un message en français adapté au POST /utilisateurs/.
 * Couvre notamment:
 * - nomUtilisateur déjà pris
 * - email déjà pris
 * - les deux à la fois
 * - champs requis manquants
 * - email invalide
 * - rôle invalide
 * - indisponibilité serveur
 */
export function getUserCreateErrorMessage(err) {
  const response = err?.response

  if (!response) {
    return "Impossible de contacter le serveur. Vérifiez votre connexion ou l'URL de l'API."
  }

  const status = response.status
  if (status >= 500) {
    return "Erreur serveur lors de la création de l'utilisateur. Réessayez plus tard."
  }

  const data = response.data
  const errors = normalizeDrfErrorData(data)

  // DRF peut renvoyer un format {detail: "..."}
  const detail = typeof data?.detail === 'string' ? data.detail : null

  const usernameErrors = errors.nomUtilisateur || []
  const emailErrors = errors.email || []

  const usernameTaken = isUniqueViolation(usernameErrors)
  const emailTaken = isUniqueViolation(emailErrors)

  if (usernameTaken && emailTaken) {
    return "Le nom d'utilisateur et l'email sont déjà utilisés."
  }
  if (usernameTaken) {
    return "Ce nom d'utilisateur est déjà utilisé."
  }
  if (emailTaken) {
    return 'Cet email est déjà utilisé.'
  }

  if (isInvalidEmail(emailErrors)) {
    return 'Adresse e-mail invalide.'
  }

  const roleErrors = errors.role || []
  if (roleErrors.length && isInvalidPk(roleErrors)) {
    return 'Rôle invalide. Veuillez sélectionner un rôle existant.'
  }

  // Erreurs mots de passe (si fournis) : mismatch / longueur
  const pwdConfirmErrors = errors.motDePasse_confirmation || []
  if (anyMatch(pwdConfirmErrors, /(ne correspondent pas|do not match|correspond)/i)) {
    return 'Les mots de passe ne correspondent pas.'
  }
  const pwdErrors = errors.motDePasse || []
  if (anyMatch(pwdErrors, /(at least|minimum|short|trop court|min_length)/i)) {
    return 'Le mot de passe est trop court.'
  }

  // Champs requis manquants
  const requiredFields = Object.entries(errors)
    .filter(([_, messages]) => isRequiredViolation(messages))
    .map(([field]) => FIELD_LABELS[field] || field)

  if (requiredFields.length) {
    // Petites améliorations d'UX
    if (requiredFields.length === 1) {
      return `Le champ ${requiredFields[0]} est obligatoire.`
    }
    return `Champs obligatoires manquants : ${requiredFields.join(', ')}.`
  }

  // non_field_errors (ou autre)
  const nonField = errors.non_field_errors || []
  if (nonField.length) {
    return nonField[0]
  }

  if (detail) {
    // On garde detail si déjà lisible. Sinon on met un fallback FR.
    if (/not found|not authenticated|permission/i.test(detail)) {
      return 'Accès refusé ou session expirée.'
    }
    return detail
  }

  const fallback = firstMeaningfulMessage(errors)
  if (fallback) {
    return `Impossible de créer l'utilisateur : ${fallback}`
  }

  return "Impossible de créer l'utilisateur. Vérifiez les informations saisies."
}
