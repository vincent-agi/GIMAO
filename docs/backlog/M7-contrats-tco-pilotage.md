# Milestone M7 — Contrats, TCO & pilotage flotte

**Objectif** : objectif business final — visibilité coût complet et aide à la décision (renouvellement, achat vs LLD), incluant les données temps réel remontées par OBD quand disponibles. Cf. `MILESTONES_PROPAL.md`.

**Dépendances entrantes** : M3 (consommation/carburant), M5 (coût d'exploitation V1), M6 (données automatiques disponibles quand boîtier présent).
**Bloque** : aucun (dernier Milestone du périmètre proposé).

---

## TUS-070 — 📝 docs(contrat): ADR-005 modèle de calcul TCO

**En tant qu'** équipe technique, **je veux** définir précisément le périmètre des coûts inclus dans le TCO (carburant, entretien, assurance, LLD/LOA, sinistres), la fréquence de recalcul, et le choix entre stockage agrégé (recalcul périodique persisté) ou calcul à la volée, **afin de** cadrer une implémentation cohérente et performante de `CoutExploitationVehicule` V2.

**Critères d'acceptation**
- Given les coûts déjà modélisés (M3 carburant, M5 pièces/MO), When l'ADR est rédigé, Then il tranche explicitement : périmètre exact des coûts inclus/exclus, stratégie de recalcul (à la volée vs job périodique + cache), et impact sur les endpoints existants (TUS-053).

**Spécifications techniques**
- Fichier : `docs/adr/0005-modele-calcul-tco.md`.

**Clean Code / TDD** : N/A (documentation).

---

## TUS-071 — ✨ feat(contrat): modèles ContratLLD/ContratLOA

**En tant que** développeur, **je veux** créer les modèles `ContratLLD` et `ContratLOA` (loueur, date début/fin, loyer mensuel, plafond kilométrique contractuel, franchise), **afin de** tracer les engagements contractuels liés à chaque véhicule loué.

**Critères d'acceptation**
- Given un véhicule sous contrat LLD, When le contrat est enregistré, Then son plafond kilométrique et sa date de fin sont exploitables par TUS-072.

**Spécifications techniques**
- Fichier : `backend/equipement/models.py` (ou `backend/maintenance/models.py` selon convention finale — recommandation : `equipement`, propriété du véhicule).
- FK `VehiculeProfile`.
- Migration Django, endpoints CRUD.
- Rattachement `Document` existant pour le contrat scanné.

**Clean Code / TDD** : Tests `backend/tests/equipement/test_contrat_lld_loa_models.py`.

---

## TUS-072 — ✨ feat(contrat): service de suivi de dépassement kilométrique contractuel

**En tant que** développeur, **je veux** un service comparant le kilométrage projeté en fin de contrat (extrapolation linéaire depuis la mise en service ou le début du contrat) au plafond contractuel, **afin d'**alerter en amont d'un dépassement coûteux.

**Critères d'acceptation**
- Given un véhicule sous contrat LLD avec un rythme kilométrique constaté supérieur au rythme contractuel théorique, When le service est appelé, Then il retourne le kilométrage projeté à échéance et l'écart avec le plafond.
- Given un écart projeté positif (dépassement) supérieur à un seuil configurable, When détecté par le job périodique, Then une notification est envoyée (réutilisation de TUS-013).

**Spécifications techniques**
- Fichier : `backend/equipement/services.py` (fonction `projeter_depassement_km(contrat)`).
- Job : `tasks/management/commands/check_depassement_km.py`.

**Clean Code / TDD** : Tests `backend/tests/equipement/test_depassement_km_service.py` (projection correcte, seuil de notification, anti-doublon comme US-012/US-043).

---

## TUS-073 — ✨ feat(contrat): CoutExploitationVehicule complet

**En tant que** développeur, **je veux** étendre le service TUS-053 pour intégrer le coût LLD/LOA (loyer mensuel proraté sur la période) et le coût des sinistres (M2), selon le périmètre tranché par l'ADR-005, **afin de** fournir le TCO complet exigé par l'objectif business du projet.

**Critères d'acceptation**
- Given un véhicule sous contrat LLD avec historique carburant, entretien et un sinistre enregistré sur la période, When le service est appelé, Then le montant total et le coût/km reflètent les 4 postes (carburant, entretien, LLD, sinistres), avec le détail de chaque poste disponible séparément.

**Spécifications techniques**
- Fichier : `backend/equipement/services.py` (extension de `calculer_cout_exploitation`).
- Selon décision ADR-005 : ajout éventuel d'un modèle de cache/agrégat (`CoutExploitationSnapshot`) si le calcul à la volée s'avère trop coûteux sur de gros historiques — **conditionnel à l'ADR**.

**Clean Code / TDD** : Tests `backend/tests/equipement/test_cout_exploitation_complet.py` (4 postes, détail par poste, cohérence avec TUS-053 sur les postes déjà couverts — non-régression).

---

## TUS-074 — ✨ feat(dashboard): dashboard flotte

**En tant que** développeur, **je veux** créer les endpoints d'agrégation nécessaires au dashboard flotte (coût/km moyen du parc, échéances à venir consolidées tous types confondus, fréquence d'incidents par véhicule/conducteur, disponibilité flotte), **afin d'**alimenter la vue pilotage frontend sans logique d'agrégation côté client.

**Critères d'acceptation**
- Given un parc de véhicules avec données variées, When l'endpoint dashboard est appelé, Then il retourne en une seule requête : coût/km moyen, top 5 véhicules les plus coûteux, échéances (CT/permis/contrats) à venir sous 30/60/90 jours, taux de disponibilité (véhicules non "A_LARRET"/"HORS_SERVICE").

**Spécifications techniques**
- Fichier : `backend/maintenance/api/viewsets.py` (existant `test_dashboard_stats_viewset.py` déjà présent côté équipement générique — étendre selon le même pattern), nouveau endpoint `GET /api/dashboard/flotte/`.

**Clean Code / TDD** : Tests `backend/tests/maintenance/test_dashboard_flotte_viewset.py` (chaque agrégat vérifié indépendamment avec jeu de données de test).

---

## US-070 — ✨ feat(contrat): enregistrer un contrat LLD/LOA

**En tant que** gestionnaire de flotte, **je veux** enregistrer les termes d'un contrat de location pour un véhicule, **afin de** pouvoir suivre le respect du plafond kilométrique et intégrer le loyer au TCO.

**Critères d'acceptation**
- Given un véhicule, When j'enregistre un contrat LLD avec loyer mensuel et plafond kilométrique, Then il apparaît dans un onglet "Contrat" de la fiche véhicule avec le document contractuel joint.

**Spécifications techniques**
- Frontend : nouvelle vue `frontend/src/views/Vehicles/Contrats/CreateContrat.vue`, onglet sur `VehicleDetail.vue`.
- Backend : TUS-071.

**Clean Code / TDD** : Tests Vitest (formulaire, upload document) + Pytest (endpoint CRUD).

---

## US-071 — ✨ feat(notif): alerte de dépassement kilométrique contractuel

**En tant que** gestionnaire de flotte, **je veux** être alerté quand un véhicule sous contrat LLD est projeté à dépasser son plafond kilométrique avant l'échéance, **afin de** pouvoir renégocier le contrat ou ajuster l'usage du véhicule avant de payer des pénalités.

**Critères d'acceptation**
- Given un véhicule en rythme de dépassement projeté, When le job périodique le détecte, Then je reçois un email avec le kilométrage projeté et l'écart au plafond (réutilisation de TUS-072).

**Spécifications techniques**
- Backend : déjà couvert par TUS-072 ; ce ticket valide le scénario côté utilisateur final (email reçu, contenu compréhensible).

**Clean Code / TDD** : Test d'intégration `backend/tests/tasks/test_alerte_depassement_km_e2e.py`.

---

## US-072 — ✨ feat(dashboard): visualiser le TCO par véhicule sur le dashboard

**En tant que** direction (ou gestionnaire de flotte), **je veux** visualiser sur un dashboard dédié le coût/km de chaque véhicule et identifier les plus coûteux, **afin de** prendre des décisions éclairées de renouvellement (achat vs LLD) ou de réforme.

**Critères d'acceptation**
- Given des données de coût disponibles pour plusieurs véhicules, When j'ouvre le dashboard flotte, Then je vois un graphique comparatif coût/km par véhicule (via `apexcharts`, cohérent avec le dashboard générique existant) et un classement des véhicules les plus coûteux.

**Spécifications techniques**
- Frontend : nouvelle vue `frontend/src/views/Dashboard/FleetDashboard.vue` (ou extension du `Dashboard.vue` existant avec un onglet flotte), composants `vue3-apexcharts`.
- Backend : TUS-074.

**Clean Code / TDD** : Tests Vitest (rendu graphique avec données mockées, cas parc vide géré proprement).

---

## US-073 — ✨ feat(dashboard): exporter les données flotte

**En tant que** gestionnaire de flotte, **je veux** exporter les données de coûts et d'échéances de la flotte, **afin de** les partager en réunion de pilotage ou les injecter dans un tableur de suivi externe.

**Critères d'acceptation**
- Given le dashboard flotte affiché, When je déclenche l'export, Then un fichier (CSV/Excel, format déjà géré par `ExportData.vue` existant) est généré avec les données de coût et d'échéances par véhicule.

**Spécifications techniques**
- Frontend : extension de `frontend/src/views/DataManagement/ExportData.vue` existant avec un nouveau type d'export "Flotte".
- Backend : endpoint d'export dédié réutilisant l'infrastructure d'export déjà en place (à localiser précisément en Phase 3 selon l'implémentation actuelle d'`ExportData`).

**Clean Code / TDD** : Tests Vitest (déclenchement export) + Pytest (contenu du fichier généré, colonnes attendues).

---

**Critère de sortie du Milestone** : un gestionnaire de flotte visualise le coût complet au km de chaque véhicule et les échéances critiques à venir sur un seul écran, et peut consulter les métriques techniques (remontées OBD) des véhicules quand disponibles.
