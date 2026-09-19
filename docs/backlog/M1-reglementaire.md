# Milestone M1 — Cycle de vie réglementaire du véhicule

**Objectif** : traçabilité documentaire et échéances légales, cœur de la réduction de risque/coût. Cf. `MILESTONES_PROPAL.md`.

**Dépendances entrantes** : M0 (`VehiculeProfile`, endpoints véhicule, RBAC véhicule).
**Bloque** : M4 (alertes permis réutilisent le système de notification créé ici), M7 (échéances consolidées au dashboard).

---

## TUS-010 — ✨ feat(reglementaire): modèle CarteGrise

**En tant que** développeur, **je veux** créer le modèle `CarteGrise` (immatriculation SIV, titulaire, date de première mise en circulation, date d'émission), **afin de** tracer l'identité administrative officielle du véhicule.

**Critères d'acceptation**
- Given un `VehiculeProfile`, When une `CarteGrise` lui est associée, Then l'historique est conservé si la plaque ou le titulaire change (pas d'écrasement silencieux — nouvelle entrée horodatée).

**Spécifications techniques**
- Fichier : `backend/equipement/models.py` (ou module dédié flotte selon arbitrage TUS-004).
- FK `VehiculeProfile` (1-N pour historiser les changements de plaque/titulaire).
- Migration Django.
- Admin : enregistrement dans `backend/equipement/admin.py`.

**Clean Code / TDD** : Tests `backend/tests/equipement/test_carte_grise_models.py` (création, historique multi-entrées, dernière carte grise active).

---

## TUS-011 — ✨ feat(reglementaire): modèle ControleTechnique

**En tant que** développeur, **je veux** créer le modèle `ControleTechnique` (date de passage, date d'échéance, résultat favorable/défavorable/contre-visite, centre de contrôle), **afin de** disposer d'un historique complet des contrôles réglementaires par véhicule.

**Critères d'acceptation**
- Given un `VehiculeProfile`, When un `ControleTechnique` est enregistré, Then il apparaît dans l'historique trié par date décroissante.
- Given un résultat "défavorable", When enregistré, Then le champ échéance de contre-visite est distinct de l'échéance normale (périodicité réglementaire différente).

**Spécifications techniques**
- Fichier : modèle dans l'app `equipement` (cohérent avec `CarteGrise`).
- Migration Django.
- Endpoints CRUD : `backend/equipement/api/{serializers,viewsets,urls}.py` (nouveau `ControleTechniqueViewSet`), pattern `/api/vehicules/<id>/controles-techniques/`.

**Clean Code / TDD** : Tests `backend/tests/equipement/test_controle_technique_models.py` + `test_controle_technique_viewset.py`.

---

## TUS-012 — ✨ feat(reglementaire): branchement CT sur le moteur Compteur/Declencher

**En tant que** développeur, **je veux** créer automatiquement un `Compteur` de type Calendaire + un `Declencher` lors de l'enregistrement d'un `ControleTechnique` favorable, **afin de** réutiliser le moteur de déclenchement préventif existant (`tasks/counterCron.py`) sans créer de nouveau moteur de règles.

**Critères d'acceptation**
- Given un `ControleTechnique` favorable avec échéance à J+N, When il est enregistré, Then un `Declencher` calendaire est créé/mis à jour avec `prochaineMaintenance` = échéance et `anticipationJours` = 60 (valeur configurable).
- Given le cron `update_counter` déjà existant, When l'échéance approche du seuil, Then il se comporte exactement comme pour tout autre `Declencher` calendaire (aucune modification du cron nécessaire).

**Spécifications techniques**
- Fichier : service dans `backend/equipement/services.py` (ou `backend/maintenance/services.py` selon domaine retenu), appelé depuis le serializer/viewset `ControleTechnique` (pas de logique dans le ViewSet, cf. règle Clean Code).
- Réutilisation stricte de `equipement.models.Compteur`/`Declencher` — **aucune migration de ces modèles**.

**Clean Code / TDD** : Test d'intégration `backend/tests/tasks/test_counter_cron.py` étendu (ou nouveau `test_ct_declenchement.py`) : création CT favorable → `Declencher` créé → cron déclenche BT préventif à échéance, en réutilisant les fixtures existantes de `tests/factories.py`.

---

## TUS-013 — ✨ feat(notif): système de notification email générique

**En tant que** développeur, **je veux** créer un service de notification (email a minima, interface extensible) déclenchable par un événement métier, **afin de** disposer d'un socle réutilisable pour toutes les alertes d'échéance du projet (CT, permis, contrat LLD, etc.).

**Critères d'acceptation**
- Given un événement "échéance à J-60", When le service est appelé, Then un email est envoyé au(x) destinataire(s) configuré(s) (responsable GMAO / gestionnaire de flotte selon RBAC), avec traçabilité de l'envoi (log).
- Le service est appelable de manière synchrone en V1 (M1) ; sa mise en file asynchrone (M6/ADR-002) ne doit pas nécessiter de réécriture de son interface publique.

**Spécifications techniques**
- Nouveau module `backend/notifications/` (app légère ou simple package selon taille) : `services.py` (interface `send_notification(event, recipients, context)`), templates email (Django `EmailMultiAlternatives` + template HTML minimal).
- Intégration au job cron existant `update_calendar_counters`/nouveau job `check_echeances` dans `tasks/`.
- Config SMTP : `backend/gimao/settings.py` (variables d'environnement, `.env.example` à compléter).

**Clean Code / TDD** : Tests `backend/tests/notifications/test_notification_service.py` (envoi mocké via `django.core.mail.outbox` en test), pas de dépendance réseau réelle dans les tests.

---

## US-010 — ✨ feat(reglementaire): saisir et consulter la carte grise d'un véhicule

**En tant que** gestionnaire de flotte, **je veux** enregistrer les informations de carte grise d'un véhicule et joindre le document scanné, **afin de** disposer d'une preuve administrative accessible sans devoir la rechercher physiquement.

**Critères d'acceptation**
- Given la fiche détail d'un véhicule (US-003), When j'ajoute une carte grise avec un fichier joint, Then elle apparaît dans un onglet "Réglementaire" avec lien de téléchargement du document.

**Spécifications techniques**
- Frontend : section dans `VehicleDetail.vue` ou sous-vue dédiée, réutilisant le composant d'upload de document déjà utilisé pour `DocumentEquipement` (`donnees.Document`).
- Backend : association via la table pivot `Document` existante (pas de nouveau modèle de stockage fichier, cf. `BILAN_EXISTANT.md` point fort n°3).

**Clean Code / TDD** : Tests Vitest (upload + affichage) et Pytest (association `Document`↔`CarteGrise`).

---

## US-011 — ✨ feat(reglementaire): enregistrer l'historique des contrôles techniques

**En tant que** gestionnaire de flotte, **je veux** enregistrer chaque passage au contrôle technique avec son résultat et joindre le PV, **afin de** garder un historique complet et prouvable en cas de contrôle routier ou de revente.

**Critères d'acceptation**
- Given un véhicule, When j'ajoute un contrôle technique avec résultat "défavorable", Then une échéance de contre-visite distincte m'est demandée.
- L'historique est affiché trié par date, avec badge visuel (favorable/défavorable/contre-visite).

**Spécifications techniques**
- Frontend : sous-vue `frontend/src/views/Vehicles/ControlesTechniques/` (liste + création), reprenant le pattern `views/Equipments/Counters/`.
- Backend : endpoints TUS-011.

**Clean Code / TDD** : Tests Vitest (formulaire, badges de statut) et Pytest (endpoints, contrainte contre-visite).

---

## US-012 — ✨ feat(notif): alerte email avant échéance de contrôle technique

**En tant que** gestionnaire de flotte, **je veux** recevoir un email lorsque le contrôle technique d'un véhicule arrive à échéance dans moins de 60 jours, **afin de** anticiper la prise de rendez-vous et éviter une immobilisation ou une infraction.

**Critères d'acceptation**
- Given un `Declencher` calendaire CT à J-60 ou moins, When le job de vérification tourne (cron quotidien), Then un email est envoyé une seule fois par échéance (pas de spam à chaque tick).

**Spécifications techniques**
- Backend : job `tasks/management/commands/check_ct_echeances.py` (ou intégré à un job existant), utilisant TUS-013.
- Anti-doublon : champ `notification_envoyee` (booléen) sur `Declencher` ou table de suivi dédiée — **à trancher lors de l'implémentation** (éviter de complexifier `Declencher`, générique à tous types de compteurs ; option : table `NotificationEnvoyee(declencher, date_envoi)`).

**Clean Code / TDD** : Test `backend/tests/tasks/test_check_ct_echeances.py` (échéance à J-60 déclenche un envoi, ré-exécution du job ne renvoie pas de doublon).

---

## US-013 — ✨ feat(reglementaire): BT préventif automatique à échéance CT

**En tant que** responsable GMAO, **je veux** qu'un `BonTravail` préventif soit généré automatiquement quand le contrôle technique arrive à échéance (si un `PlanMaintenance` est configuré pour ce véhicule), **afin de** déclencher la prise de rendez-vous sans intervention manuelle.

**Critères d'acceptation**
- Given un `PlanMaintenance` "Contrôle Technique" configuré pour un véhicule, When l'échéance calendaire est atteinte, Then le cron `update_counter` existant crée la DI+BT (comportement déjà couvert par le moteur générique, TUS-012 en est le prérequis).

**Spécifications techniques**
- Aucun nouveau code métier : ce ticket est un **test de bout en bout** validant que TUS-011/012 s'intègrent correctement avec le moteur existant `tasks/counterCron.py`.

**Clean Code / TDD** : Test d'intégration `backend/tests/tasks/test_ct_bt_auto_generation.py` couvrant le scénario complet CT créé → Declencher → cron → DI/BT créés.

---

**Critère de sortie du Milestone** : un CT arrivant à échéance (< 60 jours) génère une alerte et, si configuré, un `BonTravail` préventif via le moteur existant.
