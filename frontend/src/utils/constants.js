// ============================================
// CONSTANTES GÉNÉRALES
// ============================================

export const BASE_URL = process.env.VUE_APP_BACKEND_BASE_URL
export const API_BASE_URL = `${BASE_URL}/api/`
export const MEDIA_BASE_URL = '/media/'
export const DEFAULT_ITEMS_PER_PAGE = 10

// ============================================
// STATUTS D'ÉQUIPEMENT
// ============================================

export const EQUIPMENT_STATUS = {
  EN_FONCTIONNEMENT: 'En fonctionnement',
  A_LARRET: "À l'arrêt",
  DEGRADE: 'Dégradé',
  HORS_SERVICE: 'Hors service',
}

export const EQUIPMENT_STATUS_COLORS = {
  EN_FONCTIONNEMENT: 'green',
  A_LARRET: 'red',
  DEGRADE: 'orange',
  HORS_SERVICE: 'grey',
}

export const EQUIPMENT_CREATE_STEPS = [
  'Informations Générales',
  "Modèle d'Équipement",
  "Lieu d'Installation",
]

export const EQUIPMENT_TYPES = [
  { value: 'PEDAGOGIQUE', title: 'Pédagogique' },
  { value: 'INFRASTRUCTURE', title: 'Infrastructure' },
  { value: 'MECANIQUE', title: 'Mécanique' },
  { value: 'ELECTRIQUE', title: 'Électrique' },
  { value: 'HYDRAULIQUE', title: 'Hydraulique' },
  { value: 'PLURITECHNIQUE', title: 'Pluritechnique' },
]

// ============================================
// NIVEAUX DE DÉFAILLANCE
// ============================================

export const FAILURE_STATUS = {
  EN_ATTENTE: 'En attente',
  ACCEPTEE: 'Acceptée',
  REFUSEE: 'Rejetée',
  TRANSFORMEE: 'Transformée',
}

export const FAILURE_STATUS_COLORS = {
  EN_ATTENTE: 'orange',
  ACCEPTEE: 'green',
  REFUSEE: 'red',
  TRANSFORMEE: 'grey',
}

// ============================================
// STATUTS D'INTERVENTION (BT)
// ============================================
export const INTERVENTION_STATUS = {
  EN_ATTENTE: 'En attente',
  EN_COURS: 'En cours',
  TERMINE: 'Terminé',
  EN_RETARD: 'En retard',
  CLOTURE: 'Cloturé',
}

// Couleurs (tokens Vuetify) associées aux statuts de BT
export const INTERVENTION_STATUS_COLORS = {
  EN_ATTENTE: 'orange',
  EN_COURS: 'primary',
  TERMINE: 'green',
  EN_RETARD: 'red',
  CLOTURE: 'grey',
}

export const INTERVENTION_TYPE = {
  PREVENTIF: 'Préventif',
  CORRECTIF: 'Correctif',
}

// ============================================
// Unités pour les compteurs
// ============================================
export const COUNTER_UNITS = [
  { value: 'heures', title: 'Heures' },
  { value: 'km', title: 'Kilomètres' },
  { value: 'cycles', title: 'Cycles' },
  { value: 'jours', title: 'Jours' },
  { value: 'unites', title: 'Unités' },
  { value: 'pieces', title: 'Pièces' },
  { value: 'litres', title: 'Litres' },
  { value: 'tonnes', title: 'Tonnes' },
]

// ============================================
// HEADERS DE TABLEAUX
// ============================================

export const TABLE_HEADERS = {
  /********************************
   *  DEMANDES D'INTERVENTION
   *******************************/

  FAILURES_SUPER_LIGHT: [
    {
      title: 'N° DI',
      align: 'start',
      sortable: true,
      value: 'id',
    },
    {
      title: 'Désignation',
      align: 'start',
      sortable: false,
      value: 'commentaire',
    },
    {
      title: 'Equipement',
      value: 'equipement.designation',
      align: 'center',
      sortable: false,
    },
    {
      title: 'Statut',
      align: 'center',
      sortable: true,
      value: 'statut',
    },
  ],

  FAILURES_LIGHT: [
    {
      title: 'N° DI',
      align: 'start',
      sortable: true,
      value: 'id',
    },
    {
      title: 'Désignation',
      align: 'start',
      sortable: false,
      value: 'commentaire',
    },
    {
      title: 'Statut',
      align: 'center',
      sortable: true,
      value: 'statut',
    },
  ],

  FAILURES: [
    {
      title: 'N° DI',
      align: 'start',
      sortable: true,
      value: 'id',
    },
    {
      title: 'Désignation',
      align: 'start',
      sortable: false,
      value: 'commentaire',
    },
    {
      title: 'Statut',
      align: 'center',
      sortable: true,
      value: 'statut',
    },
    {
      title: 'Équipement',
      align: 'center',
      sortable: true,
      value: 'equipement',
    },
  ],

  /********************************
   *  BONS DE TRAVAIL
   *******************************/

  INTERVENTIONS: [
    {
      title: 'N° BT',
      align: 'center',
      sortable: true,
      value: 'id',
    },
    {
      title: 'Nom',
      align: 'start',
      sortable: true,
      value: 'nom',
    },
    {
      title: 'Équipement',
      align: 'center',
      sortable: true,
      value: 'equipement_designation',
    },
    {
      title: 'Diagnostic',
      align: 'center',
      sortable: true,
      value: 'diagnostic',
      width: '15%',
      maxWidth: '15%',
    },
    {
      title: "Date d'assignation",
      align: 'center',
      sortable: true,
      value: 'date_assignation',
    },
    {
      title: 'Date prévue',
      align: 'center',
      sortable: true,
      value: 'date_prevue',
    },
    {
      title: 'Statut',
      align: 'center',
      sortable: true,
      value: 'statut',
    },
    {
      title: 'Acquis',
      align: 'center',
      sortable: false,
      value: 'utilisateur_assigne',
    },
  ],

  INTERVENTIONS_LIGHT: [
    {
      title: 'Nom',
      align: 'start',
      sortable: true,
      value: 'nom',
    },
    {
      title: 'Équipement',
      align: 'center',
      sortable: true,
      value: 'equipement_designation',
    },
    {
      title: 'Diagnostic',
      align: 'center',
      sortable: true,
      value: 'diagnostic',
      width: '15%',
      maxWidth: '15%',
    },
    {
      title: 'Date prévue',
      align: 'center',
      sortable: true,
      value: 'date_prevue',
    },
    {
      title: 'Statut',
      align: 'center',
      sortable: true,
      value: 'statut',
    },
  ],

  INTERVENTIONS_MOBILE: [
    {
      title: 'N° BT',
      align: 'start',
      sortable: true,
      value: 'id',
    },
    {
      title: 'Désignation',
      align: 'start',
      sortable: true,
      value: 'nom',
    },
    {
      title: 'Équipement',
      align: 'center',
      sortable: true,
      value: 'equipement_designation',
    },
    {
      title: 'Statut',
      align: 'center',
      sortable: true,
      value: 'statut',
    },
  ],

  /********************************
   *  ÉQUIPEMENTS
   *******************************/

  EQUIPMENTS: [
    {
      title: 'Désignation',
      value: 'modeleEquipement.nomModeleEquipement',
      sortable: true,
      align: 'center',
    },
    {
      title: 'Lieu',
      value: 'lieu.nomLieu',
      sortable: true,
      align: 'center',
    },
    {
      title: 'Statut',
      value: 'statut.statutEquipement',
      sortable: true,
      align: 'center',
    },
  ],

  INTERVENTIONS_EQUIPMENT: [
    {
      title: 'N° BT',
      align: 'center',
      sortable: true,
      value: 'id',
    },
    {
      title: 'Nom',
      align: 'start',
      sortable: true,
      value: 'nom',
    },
    {
      title: "Date d'assignation",
      align: 'center',
      sortable: true,
      value: 'date_assignation',
    },
    {
      title: 'Statut',
      align: 'center',
      sortable: true,
      value: 'statut',
    },
    {
      title: 'Visualiser',
      align: 'center',
      sortable: false,
      value: 'action',
    },
  ],

  COUNTER: [
    {
      title: 'ID',
      value: 'id',
      sortable: true,
      align: 'center',
    },
    {
      title: 'Nom du compteur',
      value: 'nom',
      sortable: false,
      align: 'center',
    },
    {
      title: 'Valeur Courante',
      value: 'valeurCourante',
      sortable: false,
      align: 'center',
    },
    {
      title: 'Unité',
      value: 'unite',
      sortable: false,
      align: 'center',
    },
    {
      title: 'Type',
      value: 'type',
      sortable: false,
      align: 'center',
    },
    {
      title: 'Visualiser',
      value: 'action',
      sortable: false,
      align: 'center',
    },
  ],

  COUNTERS: [
    {
      title: 'Nom du compteur',
      value: 'nom',
      sortable: true,
      align: 'center',
    },
    {
      title: 'Intervalle de maintenance',
      value: 'intervalle',
      sortable: false,
      align: 'center',
    },
    {
      title: 'Unité',
      value: 'unite',
      sortable: false,
      align: 'center',
    },
    {
      title: 'Valeur actuelle',
      value: 'valeurCourante',
      sortable: false,
      align: 'center',
    },
    {
      title: 'Dernière intervention',
      value: 'derniereIntervention',
      sortable: false,
      align: 'center',
    },
    {
      title: 'Plan de maintenance',
      value: 'planMaintenance',
      sortable: false,
      align: 'center',
    },
    {
      title: 'Options',
      value: 'options',
      sortable: false,
      align: 'center',
    },
    {
      title: 'Actions',
      value: 'actions',
      sortable: false,
      align: 'center',
    },
  ],

  CONSUMABLES: [
    {
      title: 'Désignation',
      value: 'designation',
      sortable: true,
      align: 'center',
    },
    {
      title: 'Fabricant',
      value: 'fabricant',
      sortable: true,
      align: 'center',
    },
  ],

  /********************************
   * DOCUMENTS
   *******************************/
  DOCUMENTS: [
    {
      title: 'Document',
      value: 'nomDocument',
      sortable: false,
      align: 'center',
    },
    {
      title: 'Type',
      value: 'typeDocument',
      sortable: true,
      align: 'center',
    },
    {
      title: 'Actions',
      value: 'action',
      sortable: false,
      align: 'center',
    },
  ],

  /********************************
   * DONNEES SECONDAIRES
   *******************************/
  SUPPLIERS: [
    {
      title: 'Nom',
      value: 'nom',
      sortable: true,
      align: 'center',
    },
    {
      title: 'Email',
      value: 'email',
      sortable: true,
      align: 'center',
    },
    {
      title: 'Téléphone',
      value: 'numTelephone',
      sortable: true,
      align: 'center',
    },
    {
      title: 'SAV',
      value: 'serviceApresVente',
      sortable: true,
      align: 'center',
    },
    {
      title: 'Pays',
      value: 'adresse.pays',
      sortable: true,
      align: 'center',
    },
    {
      title: 'Actions',
      value: 'actions',
      sortable: false,
      align: 'center',
    },
  ],

  MANUFACTURERS: [
    {
      title: 'Nom',
      value: 'nom',
      sortable: true,
      align: 'center',
    },
    {
      title: 'Email',
      value: 'email',
      sortable: true,
      align: 'center',
    },
    {
      title: 'Téléphone',
      value: 'numTelephone',
      sortable: true,
      align: 'center',
    },
    {
      title: 'SAV',
      value: 'serviceApresVente',
      sortable: true,
      align: 'center',
    },
    {
      title: 'Pays',
      value: 'adresse.pays',
      sortable: true,
      align: 'center',
    },
    {
      title: 'Actions',
      value: 'actions',
      sortable: false,
      align: 'center',
    },
  ],

  MODEL_EQUIPMENTS: [
    {
      title: 'ID',
      value: 'id',
      sortable: true,
      align: 'center',
    },
    {
      title: 'Nom du modèle',
      value: 'nom',
      sortable: true,
      align: 'center',
    },
    {
      title: 'Fabricant',
      value: 'fabricant.nom',
      sortable: true,
      align: 'center',
    },
    {
      title: 'Visualiser',
      value: 'action',
      sortable: false,
      align: 'center',
    },
  ],
}
