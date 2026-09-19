# Milestone M5 — Maintenance préventive spécialisée automobile

**Objectif** : étendre le moteur de maintenance préventive existant aux spécificités auto (pneumatiques, plans constructeur), sans le refaire. Cf. `MILESTONES_PROPAL.md`.

**Dépendances entrantes** : M0 (`VehiculeProfile`), M2 (les incidents correctifs alimentent le coût d'exploitation), M3 (`Compteur` kilométrique fiabilisé, `PleinCarburant`).
**Bloque** : M7 (`CoutExploitationVehicule` complet reprend la base posée ici).

---

## TUS-050 — ✨ feat(maintenance): modèle Pneumatique

**En tant que** développeur, **je veux** créer le modèle `Pneumatique` (position sur véhicule, dimension, DOT, date de pose, kilométrage de pose, usure/profondeur relevée), **afin de** tracer l'historique de montage et d'usure des pneus par véhicule.

**Critères d'acceptation**
- Given un véhicule à 4 positions de roue, When je pose un pneu sur une position déjà occupée, Then l'ancien pneu de cette position est automatiquement marqué comme déposé (date de dépose renseignée), pas de doublon silencieux sur une même position active.

**Spécifications techniques**
- Fichier : `backend/equipement/models.py` (ou module maintenance selon convention finale).
- FK `VehiculeProfile`, champ `position` (choix contraint : AV_G, AV_D, AR_G, AR_D, secours...).
- Migration Django.
- Endpoints CRUD.

**Clean Code / TDD** : Tests `backend/tests/equipement/test_pneumatique_models.py` (pose, dépose automatique de l'ancien pneu de même position, historique complet consultable).

---

## TUS-051 — ✨ feat(maintenance): déclenchement préventif pneus au kilométrage

**En tant que** développeur, **je veux** brancher le remplacement préventif des pneus sur le moteur `Compteur`/`Declencher` existant (seuil kilométrique d'usure théorique par modèle de pneu), **afin de** réutiliser le mécanisme déjà opérationnel plutôt que d'en créer un nouveau.

**Critères d'acceptation**
- Given un `PlanMaintenance` "Remplacement pneus" avec seuil kilométrique, When le kilométrage du véhicule atteint ce seuil depuis la pose, Then le cron `update_counter` génère la DI/BT préventive exactement comme pour toute autre maintenance préventive.

**Spécifications techniques**
- Réutilisation stricte de `Compteur`/`Declencher`/`PlanMaintenance` — pas de nouveau modèle de règle.
- Service de création du `Declencher` pneu déclenché à la pose (TUS-050), dans `backend/equipement/services.py`.

**Clean Code / TDD** : Test d'intégration `backend/tests/tasks/test_pneu_declenchement.py` (pose pneu → Declencher créé → cron déclenche BT préventif au seuil).

---

## TUS-052 — ✨ feat(maintenance): plans de maintenance constructeur par modèle

**En tant que** développeur, **je veux** permettre de pré-paramétrer un `PlanMaintenance` type (vidange, courroie, filtres) rattaché à un `ModeleEquipement` plutôt qu'à un `Equipement` individuel, et le dupliquer automatiquement à la création de chaque nouveau véhicule de ce modèle, **afin de** réduire la saisie manuelle répétitive pour une flotte homogène.

**Critères d'acceptation**
- Given un `ModeleEquipement` "Renault Trafic" avec un plan de maintenance type "Vidange 20 000 km" configuré, When un nouveau véhicule de ce modèle est créé (US-002), Then le plan est automatiquement dupliqué (avec ses `Declencher`) pour ce véhicule.

**Spécifications techniques**
- Fichier : nouveau modèle `PlanMaintenanceType` (FK `ModeleEquipement`, structure miroir de `PlanMaintenance` mais sans FK `Equipement`) dans `backend/maintenance/models.py`.
- Service de duplication appelé depuis le service de création véhicule (TUS-005), `backend/equipement/services.py`.
- Migration Django.

**Clean Code / TDD** : Tests `backend/tests/maintenance/test_plan_maintenance_type_models.py` (duplication correcte à la création d'un véhicule du modèle concerné, absence de duplication pour un autre modèle).

---

## TUS-053 — ✨ feat(maintenance): service CoutExploitationVehicule (V1)

**En tant que** développeur, **je veux** créer un service consolidant le coût carburant (M3) et le coût des pièces/main d'œuvre issus des `BonTravail` (existant), **afin de** poser la première brique du calcul de coût d'exploitation, complété en M7 (LLD/LOA, assurance).

**Critères d'acceptation**
- Given un véhicule avec historique de pleins et de BT clôturés avec consommables valorisés, When le service est appelé sur une période, Then il retourne un montant total et un coût au km (montant / kilométrage parcouru sur la période).

**Spécifications techniques**
- Fichier : `backend/equipement/services.py` (fonction `calculer_cout_exploitation(vehicule, periode)`), réutilisant TUS-033 (conso) et les données `BonTravailConsommable`/`PorterSur` déjà existantes pour la valorisation des pièces.
- Exposé via `GET /api/vehicules/<id>/cout-exploitation/`.

**Clean Code / TDD** : Tests `backend/tests/equipement/test_cout_exploitation_service.py` (cas nominal, cas sans BT clôturé sur la période, cohérence du coût/km avec TUS-033).

---

## US-050 — ✨ feat(maintenance): enregistrer la pose d'un pneu

**En tant que** technicien, **je veux** enregistrer la pose d'un pneu sur une position donnée d'un véhicule, **afin de** déclencher le suivi préventif de son remplacement et tracer l'historique pneumatique du véhicule.

**Critères d'acceptation**
- Given un véhicule, When j'enregistre la pose d'un pneu sur la position "avant gauche" alors qu'un pneu y était déjà monté, Then l'ancien est automatiquement archivé avec sa date de dépose (comportement de TUS-050).

**Spécifications techniques**
- Frontend : nouvelle vue `frontend/src/views/Vehicles/Pneumatiques/CreatePneumatique.vue` + affichage schématique 4 positions sur `VehicleDetail.vue`.
- Backend : TUS-050/051.

**Clean Code / TDD** : Tests Vitest (formulaire, affichage schéma positions) + Pytest (déjà couvert TUS-050, test d'intégration ici).

---

## US-051 — ✨ feat(maintenance): paramétrer un plan de maintenance constructeur par modèle

**En tant que** gestionnaire de flotte, **je veux** définir une seule fois les opérations de maintenance préventive type pour un modèle de véhicule donné, **afin de** ne pas ressaisir manuellement le même plan pour chaque véhicule de ce modèle.

**Critères d'acceptation**
- Given un modèle de véhicule sans plan type configuré, When j'en crée un (ex. "Vidange" tous les 20 000 km), Then tous les véhicules existants de ce modèle sans plan équivalent en héritent rétroactivement (option proposée à la création, pas automatique par défaut pour éviter les doublons non désirés).

**Spécifications techniques**
- Frontend : extension de `frontend/src/views/DataManagement/EquipmentsModels/` (gestion des modèles d'équipement existante) avec un onglet "Plans de maintenance type".
- Backend : TUS-052.

**Clean Code / TDD** : Tests Vitest (formulaire, option rétroactive) + Pytest (duplication rétroactive optionnelle, non-duplication par défaut).

---

## US-052 — ✨ feat(maintenance): consulter le coût d'exploitation cumulé d'un véhicule

**En tant que** gestionnaire de flotte, **je veux** consulter sur la fiche véhicule le coût d'exploitation cumulé (carburant + entretien) et le coût au kilomètre, **afin d'**identifier les véhicules les plus coûteux du parc et prioriser les arbitrages de renouvellement.

**Critères d'acceptation**
- Given un véhicule avec historique suffisant, When j'ouvre l'onglet "Coût d'exploitation" de sa fiche, Then je vois le montant total sur la période sélectionnée et le coût/km, avec répartition carburant vs entretien.

**Spécifications techniques**
- Frontend : onglet dans `VehicleDetail.vue`, appel `GET /api/vehicules/<id>/cout-exploitation/` (TUS-053).

**Clean Code / TDD** : Tests Vitest (affichage répartition, sélecteur de période).

---

**Critère de sortie du Milestone** : une vidange programmée au kilométrage génère automatiquement un BT préventif, comme c'est déjà le cas pour les équipements génériques.
