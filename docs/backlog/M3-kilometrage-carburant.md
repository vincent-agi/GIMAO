# Milestone M3 — Suivi kilométrique & carburant fiabilisé

**Objectif** : données de terrain fiables — base de tout calcul de coût et de maintenance prédictive. Cf. `MILESTONES_PROPAL.md`.

**Dépendances entrantes** : M0 (`VehiculeProfile`, `Compteur` déjà existant côté `equipement`).
**Bloque** : M5 (coût d'exploitation carburant), M6 (relevé kilométrique automatique remplace/complète la saisie manuelle ici), M7 (TCO).

---

## TUS-030 — ♻️ refactor(carburant): normaliser Compteur.unite

**En tant que** développeur, **je veux** remplacer le `CharField` libre `Compteur.unite` par un choix contraint (`km`, `heures`, `jours`, `litres`...), **afin d'**éliminer les incohérences de saisie ("km"/"Km"/"kilomètres") qui rendraient tout calcul de coût/consommation non fiable.

**Critères d'acceptation**
- Given les `Compteur` existants en base, When la migration est appliquée, Then leurs valeurs `unite` sont normalisées vers le choix contraint le plus proche (script de migration de données, pas seulement de schéma) sans perte de données.
- Given une tentative de création d'un `Compteur` avec une unité hors liste, When la requête est envoyée, Then elle est rejetée avec une erreur de validation explicite.

**Spécifications techniques**
- Fichier : `backend/equipement/models.py` (`Compteur.unite` → `CharField(choices=...)`), migration Django en deux temps (ajout du choix contraint + migration de données `RunPython`, puis suppression de l'ancien libre si nécessaire).
- Script de normalisation : mapping des valeurs libres existantes vers les choix contraints (à établir à partir d'un audit des données réelles — première étape de la migration).

**Clean Code / TDD** : Tests `backend/tests/equipement/test_compteur_unite_migration.py` (données legacy correctement mappées) + tests de validation sur le modèle.

---

## TUS-031 — ✨ feat(carburant): règle de non-régression du relevé kilométrique

**En tant que** développeur, **je veux** empêcher qu'un nouveau relevé de `Compteur` de type kilométrique soit inférieur au relevé précédent (sauf correction explicite tracée), **afin de** garantir la fiabilité des données utilisées pour la facturation LLD et la détection de fraude.

**Critères d'acceptation**
- Given un `Compteur` kilométrique à 50 000 km, When un relevé à 49 000 km est soumis sans flag "correction", Then il est rejeté avec un message explicite.
- Given le même cas avec le flag "correction" activé et un commentaire de justification obligatoire, When soumis, Then le relevé est accepté et tracé dans `Log` (audit existant, `utilisateur.models.Log`).

**Spécifications techniques**
- Fichier : service `backend/equipement/services.py` (validation dans le service de mise à jour de `Compteur`, pas dans le ViewSet).
- Champ additionnel éventuel sur le payload de mise à jour : `is_correction: bool`, `commentaire_correction: str`.

**Clean Code / TDD** : Tests `backend/tests/equipement/test_compteur_non_regression.py` (rejet sans flag, acceptation avec flag + log créé).

---

## TUS-032 — ✨ feat(carburant): modèle PleinCarburant

**En tant que** développeur, **je veux** créer le modèle `PleinCarburant` (date, kilométrage au relevé, quantité, prix unitaire, montant, type d'énergie, station), **afin de** capturer l'historique de ravitaillement nécessaire au calcul de consommation et de coût.

**Critères d'acceptation**
- Given un véhicule, When un plein est enregistré avec un kilométrage inférieur au dernier plein connu, Then la même règle de non-régression que TUS-031 s'applique (réutilisation du service, pas duplication de la règle).

**Spécifications techniques**
- Fichier : `backend/equipement/models.py` ou `backend/maintenance/models.py` (à trancher — recommandation : `equipement`, car rattaché au véhicule et non à une intervention).
- FK `VehiculeProfile`.
- Migration Django.
- Endpoints CRUD.

**Clean Code / TDD** : Tests `backend/tests/equipement/test_plein_carburant_models.py`.

---

## TUS-033 — ✨ feat(carburant): service de calcul de consommation moyenne

**En tant que** développeur, **je veux** un service calculant la consommation moyenne (L/100km) et le coût carburant d'un véhicule sur une période donnée à partir de l'historique `PleinCarburant`, **afin d'**alimenter la fiche véhicule et, plus tard, le TCO (M7).

**Critères d'acceptation**
- Given au moins deux pleins consécutifs avec kilométrage croissant, When le service est appelé, Then il retourne la consommation moyenne en L/100km et le coût total carburant sur la période.
- Given un seul plein enregistré, When le service est appelé, Then il retourne un résultat explicite "donnée insuffisante" plutôt qu'une division par zéro ou une erreur.

**Spécifications techniques**
- Fichier : `backend/equipement/services.py` (fonction pure, testable indépendamment du ViewSet).
- Exposé via un endpoint dédié ou un champ calculé du serializer véhicule (`GET /api/vehicules/<id>/consommation/`).

**Clean Code / TDD** : Tests `backend/tests/equipement/test_consommation_service.py` (cas nominal, cas données insuffisantes, cas kilométrage non-croissant).

---

## US-030 — ✨ feat(carburant): saisir un relevé kilométrique

**En tant que** conducteur, **je veux** saisir le kilométrage actuel de mon véhicule affecté, **afin de** maintenir à jour le compteur qui pilote la maintenance préventive.

**Critères d'acceptation**
- Given je suis sur la fiche de mon véhicule affecté, When je saisis un nouveau relevé, Then il est immédiatement pris en compte par le moteur `Declencher` existant (aucune modification du moteur nécessaire).
- Given un relevé incohérent (inférieur au précédent), When je le soumets, Then je vois le message d'erreur de TUS-031.

**Spécifications techniques**
- Frontend : composant réutilisant/étendant `views/Equipments/Counters/` existant, adapté pour affichage simplifié côté conducteur (accès restreint à son véhicule affecté).
- Backend : endpoint `Compteur` existant + règle TUS-031.

**Clean Code / TDD** : Tests Vitest (formulaire, message d'erreur non-régression) + Pytest (déjà couvert par TUS-031, test d'intégration bout en bout ici).

---

## US-031 — ✨ feat(carburant): saisir un plein de carburant

**En tant que** conducteur, **je veux** enregistrer un plein de carburant (quantité, prix, kilométrage), **afin de** permettre le suivi de consommation et de coût de mon véhicule.

**Critères d'acceptation**
- Given je saisis un plein avec un kilométrage cohérent, When je soumets, Then il apparaît dans l'historique des pleins du véhicule, trié par date décroissante.

**Spécifications techniques**
- Frontend : nouvelle vue `frontend/src/views/Vehicles/Carburant/CreatePlein.vue` + `PleinList.vue`.
- Backend : TUS-032.

**Clean Code / TDD** : Tests Vitest (formulaire, affichage historique) + Pytest (endpoint CRUD).

---

## US-032 — ✨ feat(carburant): consulter l'historique des pleins et la consommation moyenne

**En tant que** gestionnaire de flotte, **je veux** consulter sur la fiche véhicule l'historique des pleins et la consommation moyenne calculée, **afin d'**identifier rapidement un véhicule anormalement consommateur (indice d'usure ou de conduite inadaptée).

**Critères d'acceptation**
- Given un véhicule avec historique de pleins, When j'ouvre sa fiche, Then je vois un onglet "Carburant" avec la liste des pleins et un indicateur de consommation moyenne (L/100km) sur les 90 derniers jours.

**Spécifications techniques**
- Frontend : onglet dans `VehicleDetail.vue`, appel au endpoint TUS-033.

**Clean Code / TDD** : Tests Vitest (affichage indicateur, cas données insuffisantes affichant un message clair plutôt qu'un chiffre erroné).

---

**Critère de sortie du Milestone** : historique des pleins consultable, consommation moyenne affichée sur la fiche véhicule.
