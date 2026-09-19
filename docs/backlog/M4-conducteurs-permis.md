# Milestone M4 — Conducteurs, permis & habilitations

**Objectif** : traçabilité conducteur ↔ véhicule ↔ droit de conduire, prérequis légal flotte entreprise. Cf. `MILESTONES_PROPAL.md`.

**Dépendances entrantes** : M0 (`VehiculeProfile`), M1 (système de notification pour les alertes d'expiration).
**Bloque** : M2 (filtrage strict "véhicule affecté" dans le formulaire de signalement, actuellement non filtré en attendant ce Milestone), M7 (dashboard incidents par conducteur).

---

## TUS-040 — ✨ feat(permis): modèle PermisConduire

**En tant que** développeur, **je veux** créer le modèle `PermisConduire` (catégorie B/C/C1/CE/D, numéro, date d'obtention, date d'expiration, points restants optionnel), rattaché à `Utilisateur`, **afin de** disposer de la donnée légale nécessaire à toute affectation de véhicule.

**Critères d'acceptation**
- Given un `Utilisateur`, When plusieurs `PermisConduire` de catégories différentes lui sont associés, Then chacun est individuellement consultable avec son statut de validité (calculé : `date_expiration > aujourd'hui`).

**Spécifications techniques**
- Fichier : `backend/utilisateur/models.py`.
- FK `Utilisateur`, `unique_together` sur (`utilisateur`, `categorie`) si un conducteur ne peut avoir qu'un permis actif par catégorie — **à valider avec le métier en Phase 3**.
- Migration Django.
- Endpoints CRUD : `backend/utilisateur/api/{serializers,viewsets,urls}.py`.

**Clean Code / TDD** : Tests `backend/tests/utilisateur/test_permis_conduire_models.py` (création, calcul de validité, unicité par catégorie).

---

## TUS-041 — ✨ feat(permis): modèle HabilitationConduite

**En tant que** développeur, **je veux** créer le modèle `HabilitationConduite` (type FIMO/FCO, visite médicale d'aptitude, date d'expiration), rattaché à `Utilisateur`, sur le même schéma que les flags `PlanMaintenance.necessiteHabilitationElectrique`/`necessitePermisFeu` déjà présents côté plan de maintenance, **afin de** couvrir les habilitations professionnelles spécifiques au transport routier.

**Critères d'acceptation**
- Given un conducteur PL, When une `HabilitationConduite` de type FCO expire, Then son statut de validité bascule automatiquement (calcul à la volée, pas de job dédié nécessaire pour ce seul calcul).

**Spécifications techniques**
- Fichier : `backend/utilisateur/models.py`.
- Migration Django, endpoints CRUD.

**Clean Code / TDD** : Tests `backend/tests/utilisateur/test_habilitation_conduite_models.py`.

---

## TUS-042 — ✨ feat(permis): modèle AffectationVehicule

**En tant que** développeur, **je veux** créer le modèle `AffectationVehicule` (conducteur, véhicule, date de début/fin, kilométrage de début/fin), **afin de** disposer d'un historique exploitable "qui conduisait quoi, quand" pour la traçabilité et l'imputation des incidents/coûts.

**Critères d'acceptation**
- Given un véhicule déjà affecté à un conducteur avec une période ouverte (`date_fin` nulle), When une nouvelle affectation est créée pour ce même véhicule, Then l'affectation précédente est automatiquement clôturée (`date_fin` = date de début de la nouvelle) — pas de chevauchement silencieux.

**Spécifications techniques**
- Fichier : `backend/equipement/models.py` ou `backend/utilisateur/models.py` (recommandation : `equipement`, l'affectation étant une propriété du cycle de vie véhicule).
- Migration Django, contrainte d'unicité sur affectation ouverte par véhicule (au niveau service, cf. règle Clean Code — logique dans le service, pas dans le ViewSet).

**Clean Code / TDD** : Tests `backend/tests/equipement/test_affectation_vehicule_models.py` (clôture automatique de l'affectation précédente, historique complet consultable).

---

## TUS-043 — ✨ feat(permis): règle métier de blocage d'affectation sans permis valide

**En tant que** développeur, **je veux** empêcher la création d'une `AffectationVehicule` si le conducteur ne détient pas de `PermisConduire` valide de la catégorie requise par le `VehiculeProfile` (genre du véhicule → catégorie de permis requise), **afin d'**éviter un risque juridique et de sécurité majeur pour l'entreprise.

**Critères d'acceptation**
- Given un véhicule de genre "Poids Lourd" nécessitant la catégorie C, When on tente d'affecter un conducteur ne détenant qu'un permis B valide, Then l'affectation est rejetée avec un message explicite citant la catégorie manquante.
- Given un conducteur avec permis valide mais `HabilitationConduite` FCO expirée sur un véhicule qui la requiert, When l'affectation est tentée, Then elle est également rejetée (double contrôle permis + habilitation).

**Spécifications techniques**
- Fichier : service `backend/equipement/services.py` (fonction `verifier_eligibilite_conducteur(utilisateur, vehicule)`), appelée par le serializer/viewset `AffectationVehicule`.
- Table de correspondance genre véhicule → catégorie de permis requise : constante applicative ou nouveau petit modèle de paramétrage selon complexité réelle (à trancher en Phase 3 — une constante suffit probablement en V1).

**Clean Code / TDD** : Tests `backend/tests/equipement/test_affectation_eligibilite.py` (rejet permis manquant, rejet habilitation expirée, acceptation cas nominal) — écrits avant l'implémentation de la règle (TDD strict, règle à risque juridique).

---

## US-040 — ✨ feat(permis): enregistrer le permis de conduire d'un utilisateur

**En tant que** gestionnaire de flotte (ou RH), **je veux** enregistrer les permis de conduire d'un utilisateur avec leurs catégories et dates d'expiration, **afin de** disposer de la donnée nécessaire aux affectations de véhicule.

**Critères d'acceptation**
- Given la fiche d'un utilisateur, When j'ajoute un permis avec une date d'expiration passée, Then il est enregistré mais visuellement marqué "expiré" (pas de blocage à la saisie, seulement à l'affectation — TUS-043).

**Spécifications techniques**
- Frontend : extension de `frontend/src/views/Users/` (nouvel onglet ou sous-vue "Permis & Habilitations" sur la fiche utilisateur existante).
- Backend : TUS-040.

**Clean Code / TDD** : Tests Vitest (affichage badge expiré) + Pytest (endpoint CRUD).

---

## US-041 — ✨ feat(permis): enregistrer une habilitation FIMO/FCO

**En tant que** gestionnaire de flotte, **je veux** enregistrer les habilitations professionnelles (FIMO/FCO, visite médicale) d'un conducteur, **afin de** garantir la conformité réglementaire du transport routier.

**Critères d'acceptation**
- Given la fiche utilisateur, When j'ajoute une habilitation FCO avec date d'expiration, Then elle apparaît dans le même onglet que les permis (US-040), avec son propre badge de validité.

**Spécifications techniques**
- Frontend : même onglet que US-040.
- Backend : TUS-041.

**Clean Code / TDD** : Tests Vitest + Pytest analogues à US-040.

---

## US-042 — ✨ feat(permis): affecter un véhicule à un conducteur

**En tant que** gestionnaire de flotte, **je veux** affecter un véhicule à un conducteur, **afin de** formaliser la responsabilité d'usage et permettre au conducteur de signaler des incidents sur "son" véhicule.

**Critères d'acceptation**
- Given un conducteur sans permis valide pour le genre du véhicule ciblé, When je tente l'affectation, Then je vois le message de rejet de TUS-043 avant toute soumission bloquante côté serveur (double validation front/back).
- Given une affectation réussie, When je consulte le véhicule ou l'utilisateur, Then l'affectation apparaît des deux côtés (fiche véhicule et fiche utilisateur).

**Spécifications techniques**
- Frontend : nouvelle vue `frontend/src/views/Vehicles/Affectations/CreateAffectation.vue`, section "Affectation actuelle" sur `VehicleDetail.vue` et sur la fiche utilisateur.
- Backend : TUS-042/043.

**Clean Code / TDD** : Tests Vitest (formulaire, message de rejet) + Pytest (déjà couvert par TUS-043, test d'intégration bout en bout ici incluant la double affichage véhicule/utilisateur).

---

## US-043 — ✨ feat(notif): alerte d'expiration de permis ou d'habilitation

**En tant que** gestionnaire de flotte, **je veux** être alerté par email lorsqu'un permis ou une habilitation d'un conducteur affecté approche de son expiration, **afin d'**anticiper le renouvellement et éviter qu'un conducteur circule non-conforme.

**Critères d'acceptation**
- Given un permis expirant dans 30 jours (seuil configurable) pour un conducteur actuellement affecté à un véhicule, When le job de vérification quotidien tourne, Then un email est envoyé (réutilisation du service TUS-013, pas de nouveau système de notification).

**Spécifications techniques**
- Backend : job `tasks/management/commands/check_permis_echeances.py`, réutilisant `backend/notifications/services.py` (TUS-013).

**Clean Code / TDD** : Tests `backend/tests/tasks/test_check_permis_echeances.py` (anti-doublon comme US-012, filtrage sur conducteurs actuellement affectés uniquement).

---

**Critère de sortie du Milestone** : impossible d'affecter un conducteur sans permis valide de la bonne catégorie ; historique des affectations consultable.
