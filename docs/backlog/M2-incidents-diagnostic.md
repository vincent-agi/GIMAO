# Milestone M2 — Signalement d'avaries, incidents & diagnostic véhicule

**Objectif** : couvrir tout le cycle de vie réactif du véhicule (voyants, bruits anormaux, accidents, codes défaut, usure hors plan préventif) en étendant `DemandeIntervention`/`BonTravail` plutôt qu'en recréant un workflow. Cf. `MILESTONES_PROPAL.md`.

**Dépendances entrantes** : M0 (`VehiculeProfile`).
**Bloque** : M5 (coût d'exploitation intègre les coûts correctifs issus des incidents), M6 (remontée automatique de codes défaut réutilise `CodeDefautOBD`).

---

## TUS-020 — ✨ feat(incident): modèle IncidentVehicule

**En tant que** développeur, **je veux** créer le modèle `IncidentVehicule` en relation 1-1 sur `DemandeIntervention` (même pattern que `VehiculeProfile` sur `Equipement`), **afin de** porter les métadonnées spécifiques véhicule (type d'avarie, gravité, immobilisation) sans modifier `DemandeIntervention` pour les autres types d'équipements.

**Critères d'acceptation**
- Given une `DemandeIntervention` créée sur un équipement de type VEHICULE, When elle est enrichie d'un `IncidentVehicule`, Then le champ `type_avarie` (voyant / bruit anormal / accident de la route / code défaut / usure signalée / autre) et le booléen `immobilisation` sont persistés.
- Given une `DemandeIntervention` sur un équipement non-véhicule, When on consulte l'API, Then aucun champ `IncidentVehicule` n'est exposé (pas de régression sur le workflow DI générique).

**Spécifications techniques**
- Fichier : `backend/maintenance/models.py` (ou module dédié incident si le fichier grossit trop).
- `OneToOneField(DemandeIntervention, primary_key=True)`.
- Migration Django.
- Serializer imbriqué dans `DemandeInterventionSerializer` (extension conditionnelle selon type d'équipement).

**Clean Code / TDD** : Tests `backend/tests/maintenance/test_incident_vehicule_models.py` (création, absence sur équipement non-véhicule).

---

## TUS-021 — ✨ feat(incident): modèle Sinistre

**En tant que** développeur, **je veux** créer le modèle `Sinistre` (date/lieu de l'accident, tiers impliqués, dégâts constatés, numéro de déclaration d'assurance, expertise), rattaché à un `IncidentVehicule` de type "accident de la route", **afin de** tracer les informations nécessaires à la déclaration d'assurance et au suivi de l'immobilisation.

**Critères d'acceptation**
- Given un `IncidentVehicule` de type `ACCIDENT_ROUTE`, When un `Sinistre` lui est associé, Then il n'est pas possible d'associer un `Sinistre` à un incident d'un autre type (contrainte métier au niveau service/validation, pas seulement UI).

**Spécifications techniques**
- Fichier : `backend/maintenance/models.py`.
- `OneToOneField(IncidentVehicule)`.
- Validation métier dans le service de création (cf. TUS-003 pattern service), pas dans le ViewSet.
- Migration Django.

**Clean Code / TDD** : Tests `backend/tests/maintenance/test_sinistre_models.py` (création valide, rejet si `type_avarie` ≠ accident).

---

## TUS-022 — ✨ feat(incident): modèle CodeDefautOBD

**En tant que** développeur, **je veux** créer le modèle `CodeDefautOBD` (code DTC, description, date de lecture, source `MANUEL`/`AUTOMATIQUE`), rattachable à un `IncidentVehicule` ou directement à un `VehiculeProfile`, **afin de** tracer les codes défaut relevés à la valise diagnostic dès aujourd'hui, et préparer la remontée automatique boîtier OBD prévue en M6.

**Critères d'acceptation**
- Given un technicien saisissant un code défaut après passage de la valise, When il l'enregistre avec `source=MANUEL`, Then le code est rattaché au véhicule et, optionnellement, à l'incident en cours.
- Le champ `source` est un choix contraint (`MANUEL`, `AUTOMATIQUE`) — `AUTOMATIQUE` n'est pas utilisable tant que M6 n'est pas livré (pas de blocage technique, juste absence de producteur automatique).

**Spécifications techniques**
- Fichier : `backend/maintenance/models.py` ou `backend/equipement/models.py` (à trancher selon que le code défaut est vu comme rattaché au véhicule ou à l'incident — recommandation : FK véhicule obligatoire + FK incident optionnelle).
- Migration Django.
- Endpoints CRUD standards.

**Clean Code / TDD** : Tests `backend/tests/maintenance/test_code_defaut_obd_models.py`.

---

## TUS-023 — ✨ feat(rbac): permissions incident/sinistre/obd

**En tant qu'** administrateur GMAO, **je veux** disposer des permissions `incident:*`, `sinistre:*`, `obd:*` (viewList/viewDetail/create/edit/delete selon pertinence), **afin de** contrôler qui peut déclarer un accident, consulter un dossier sinistre ou saisir un code défaut.

**Critères d'acceptation**
- Given un rôle "Conducteur", When configuré avec `incident:create` mais sans `sinistre:viewList`, Then il peut déclarer un incident mais pas consulter la liste des sinistres d'autres véhicules.

**Spécifications techniques**
- Fichier : `backend/tasks/perms_data.py`, `backend/utilisateur/models.py` (labels).

**Clean Code / TDD** : Tests `backend/tests/utilisateur/test_incident_permissions.py`.

---

## US-020 — ✨ feat(incident): signaler un voyant allumé ou un bruit anormal

**En tant que** conducteur, **je veux** signaler depuis l'application qu'un voyant s'est allumé ou qu'un bruit anormal est apparu sur le véhicule qui m'est affecté, **afin de** déclencher une prise en charge rapide avant que le problème ne s'aggrave.

**Critères d'acceptation**
- Given je suis conducteur affecté à un véhicule, When je crée un signalement de type "voyant" ou "bruit anormal", Then une `DemandeIntervention` + `IncidentVehicule` sont créées et visibles par le gestionnaire de flotte, avec le statut initial `EN_ATTENTE`.
- Given je ne suis affecté à aucun véhicule, When j'ouvre le formulaire, Then je ne peux sélectionner qu'un véhicule qui m'est effectivement affecté (dépend de M4 pour l'affectation stricte — en attendant M4, la liste de véhicules disponibles n'est pas filtrée mais le champ reste obligatoire).

**Spécifications techniques**
- Frontend : extension de `frontend/src/views/Failures/CreateFailure.vue` (déjà existant pour les équipements génériques) avec un champ `type_avarie` conditionnel si l'équipement sélectionné est un véhicule ; ou nouvelle vue `views/Vehicles/Incidents/CreateIncidentVehicule.vue` si la divergence UI est trop importante — **arbitrage à faire en Phase 3 selon complexité réelle du composant existant**.
- Backend : endpoint DI existant étendu pour accepter le payload `IncidentVehicule` imbriqué (TUS-020).

**Clean Code / TDD** : Tests Vitest (affichage conditionnel du champ type d'avarie) + Pytest (création DI+IncidentVehicule en une requête).

---

## US-021 — ✨ feat(incident): déclarer un accident de la route

**En tant que** conducteur, **je veux** déclarer un accident de la route en renseignant les circonstances (lieu, tiers impliqués, dégâts), **afin de** permettre au gestionnaire de flotte d'enclencher la déclaration d'assurance sans délai.

**Critères d'acceptation**
- Given je déclare un incident de type "accident de la route", When je soumets le formulaire, Then les champs `Sinistre` (tiers, dégâts, lieu) deviennent obligatoires et un flag `immobilisation` est proposé par défaut à "oui".
- Given un sinistre déclaré, When le gestionnaire de flotte consulte le véhicule, Then le statut du véhicule (`StatutEquipement`) peut être mis à jour vers "A_LARRET"/"HORS_SERVICE" en un clic depuis l'écran de traitement.

**Spécifications techniques**
- Frontend : extension du formulaire US-020 avec sous-formulaire conditionnel `Sinistre`.
- Backend : TUS-021, service de création transactionnelle DI+IncidentVehicule+Sinistre.

**Clean Code / TDD** : Tests Vitest (sous-formulaire conditionnel) + Pytest (transaction complète, rollback si Sinistre invalide).

---

## US-022 — ✨ feat(incident): saisir un code défaut OBD relevé à la valise diagnostic

**En tant que** technicien, **je veux** saisir un ou plusieurs codes défaut (DTC) après avoir branché la valise de diagnostic sur un véhicule, **afin de** documenter précisément la panne dans le dossier du `BonTravail` en cours.

**Critères d'acceptation**
- Given un `BonTravail` en cours sur un véhicule, When j'ajoute un code défaut avec sa description, Then il est rattaché au véhicule et visible dans l'historique diagnostic du véhicule (au-delà du seul BT courant).

**Spécifications techniques**
- Frontend : composant dans la vue détail du `BonTravail` (`views/Interventions/`) ou vue dédiée `views/Vehicles/Diagnostic/`.
- Backend : TUS-022.

**Clean Code / TDD** : Tests Vitest (formulaire ajout code défaut) + Pytest (persistance, association véhicule + incident optionnel).

---

**Critère de sortie du Milestone** : un conducteur signale un voyant allumé ou un accident via le même écran que les anomalies actuelles ; la DI générée porte les métadonnées véhicule (type d'avarie, sinistre le cas échéant) et suit le cycle DI→BT existant sans modification du moteur.
