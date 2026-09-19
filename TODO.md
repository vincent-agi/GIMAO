# TODO — Points de rupture & refactoring nécessaires

Complément actionnable de `BILAN_EXISTANT.md`. Classé par domaine, sans découpage en tickets (Phase 2). À valider avant écriture des User Stories.

## A. Modèle de données — Backend

- [ ] **Décider de la stratégie de spécialisation `Equipement` → `Vehicule`** (à trancher via ADR, cf. §D) :
  - Option 1 (recommandée pressenti) : `VehiculeProfile` en relation `OneToOneField(Equipement, primary_key=True)` — `Equipement` reste le socle générique (nom, lieu, statut, compteurs, documents, plan de maintenance), `VehiculeProfile` porte les champs spécifiques auto (VIN, immatriculation, genre, énergie, CO2, puissance fiscale, poids total autorisé en charge...). Non-régression maximale sur le reste de la GMAO (infrastructure/pédagogique inchangés).
  - Option 2 (rejetée a priori) : héritage multi-table Django (`Vehicule(Equipement)`) — plus lourd à migrer, moins flexible si un équipement change de nature.
  - Ajouter `'VEHICULE'` à `Equipement.TYPE_CHOICES` (ou remplacer l'enum figé par une FK vers une table de types — cohérent avec `FamilleEquipement` qui existe déjà et fait doublon partiel avec `type`).
- [ ] **Créer les modèles réglementaires/métier automobile manquants** :
  - `CarteGrise` (immatriculation SIV, titulaire, date de première mise en circulation, date d'émission du certificat) — 1-1 ou historique si changement de plaque/titulaire.
  - `ControleTechnique` (date de passage, date d'échéance, résultat favorable/défavorable/contre-visite, centre de contrôle) — historique 1-N sur `Vehicule`, brancher sur le moteur `Compteur`/`Declencher` existant en mode calendaire pour l'alerte d'échéance (réutilise le mécanisme déjà en place, pas de nouveau moteur de règle).
  - `Pneumatique` (position sur véhicule, dimension, DOT, date de pose, kilométrage de pose, usure/profondeur relevée) — historique 1-N.
  - `PleinCarburant`/`Ravitaillement` (date, kilométrage au relevé, quantité, prix unitaire, montant, type d'énergie, station) — sert de base à la conso réelle (L/100km) et au coût carburant.
  - `ContratLLD`/`ContratLOA` (loueur, date début/fin, loyer mensuel, plafond kilométrique contractuel, franchise) — nécessaire pour le calcul de dépassement kilométrique et le TCO.
  - `PermisConduire` (catégorie B/C/C1/CE/D, numéro, date d'obtention, date d'expiration, points restants optionnel) — rattaché à `Utilisateur`.
  - `HabilitationConduite` (FIMO/FCO, visite médicale d'aptitude, date d'expiration) — même logique que `PlanMaintenance.necessiteHabilitationElectrique` mais côté conducteur, à croiser avec le véhicule affecté.
  - `AffectationVehicule` (conducteur ↔ véhicule, période, kilométrage de début/fin d'affectation) — historique, base du "qui conduisait quoi quand" pour la traçabilité.
- [ ] **Créer les modèles d'avaries/incidents véhicule** (cycle de vie réactif, distinct du préventif) :
  - `IncidentVehicule` (profil 1-1 sur `DemandeIntervention`, même pattern que `VehiculeProfile` sur `Equipement`) : `type_avarie` (voyant tableau de bord, bruit anormal, accident de la route, code défaut, usure signalée, autre), gravité, immobilisation oui/non — étend la DI générique existante sans la polluer pour les équipements non-véhicule.
  - `Sinistre` (accident de la route) : date/lieu, tiers impliqués, dégâts constatés, numéro de déclaration assurance, expertise — rattaché à l'`IncidentVehicule` concerné.
  - `CodeDefautOBD` : code DTC, description, date de lecture, source (`MANUEL` via valise diagnostic / `AUTOMATIQUE` via boîtier OBD — cette dernière voie dépend de l'intégration télématique) — rattaché à l'incident ou au véhicule.
- [ ] **Normaliser `Compteur.unite`** : passer d'un `CharField` libre à un choix contraint (`km`, `heures`, `jours`, `litres`...) et ajouter une règle métier de non-régression (le relevé kilométrique ne doit pas diminuer, sauf correction explicite tracée). Point critique pour la fiabilité (facturation LLD, anti-fraude relevé).
- [ ] **Créer un modèle d'agrégation coût** (`CoutExploitationVehicule` ou vue/service calculé) consolidant carburant + pièces + main d'œuvre + LLD/LOA + assurance, ramené au km — objectif business n°1 du projet, actuellement absent.
- [ ] Revoir la pertinence de `x`/`y` sur `Equipement` pour le cas véhicule (champ sans usage, à laisser `null` sans forcer d'UI de positionnement plan pour ce sous-type).

## B. Backend — API, permissions, intégrations

- [ ] **Créer une app `integrations`** (client HTTP abstrait, gestion clés API/secrets par fournisseur, logs d'appel, gestion des erreurs/retry) — inexistante aujourd'hui. Prérequis pour :
  - Décodage VIN / lookup immatriculation (SIV) — vérifier le fournisseur retenu (accès direct SIV réservé aux professionnels agréés ; probable passage par un service tiers agréé).
  - Télématique/OBD (relevé kilométrique automatique, géolocalisation) — API par boîtier (Geotab, Webfleet, etc., à confirmer avec le client).
  - Alertes constructeur/rappels — pas d'API unifiée constructeurs en France ; à investiguer par marque ou via un agrégateur tiers.
- [ ] **Trancher la question de l'asynchrone** (ADR obligatoire) : `django-crontab` seul ne suffit plus dès qu'un appel API tiers à latence variable ou un webhook entrant existe. Introduire une file de tâches (Celery+Redis, ou RQ, ou django-q2 selon contrainte d'infra Docker déjà en place) avant le Milestone Intégrations.
- [ ] Ajouter les nouveaux `Module`/`Permission` RBAC pour chaque nouvelle entité (`veh:*`, `permis:*`, `ct:*`, `carburant:*`, `pneu:*`, `contrat:*`, `incident:*`, `sinistre:*`, `obd:*`) en respectant la convention `<module>:<action>` existante — pas de rupture, juste de l'extension.
- [ ] Sortir les labels `FULL_LABELS` de `Permission.__str__` (actuellement dict Python en dur) vers une fixture/table de traduction avant d'en ajouter ~30-40 de plus.
- [ ] **Factoriser `EquipementViewSet`** (~830 lignes) en services/selectors avant d'y greffer la logique véhicule — sinon la dette s'aggrave et contrevient à la consigne "logique métier hors ViewSet" dès le premier ticket flotte.
- [ ] Vérifier/renforcer la couche permission par requête (actuellement `REST_FRAMEWORK.DEFAULT_PERMISSION_CLASSES = []`, tout est géré à la main) — critique dès qu'un conducteur ne doit voir que son véhicule affecté / ses propres relevés.
- [ ] Ajouter un modèle de notification/rappel (email au minimum) pour échéances CT, assurance, permis, contrat LLD — aucun système d'alerte proactive n'existe aujourd'hui au-delà de la création automatique de BT.

## C. Frontend — Vue 3

- [ ] **Finaliser/réactiver `composables/useApi.js`** (actuellement majoritairement commenté) avant d'imposer son usage systématique sur les nouvelles vues flotte.
- [ ] Créer l'arborescence `views/Vehicles/` en miroir de `views/Equipments/` (`VehicleList`, `VehicleDetail`, `CreateVehicle`, `EditVehicle`) + sous-vues `ControlesTechniques/`, `Pneumatiques/`, `Carburant/`, `Contrats/`.
- [ ] Créer `views/Drivers/` (ou extension de `views/Users/`) pour la gestion des permis/habilitations et l'affectation véhicule-conducteur.
- [ ] Étendre le dashboard (`apexcharts`) avec les KPIs flotte : coût/km, échéances CT/assurance à venir, consommation moyenne, taux de disponibilité flotte.
- [ ] Étendre `router/` avec les nouvelles routes, en respectant la convention de nommage `PascalCase` déjà en place.
- [ ] Vérifier compatibilité `vue-cal` pour affichage combiné plan de maintenance + échéances réglementaires véhicule sur le même calendrier.

## D. ADR à rédiger avant Phase 2 (dans `/docs/adr/`)

- [ ] ADR-001 : Stratégie de modélisation `Equipement` → `Vehicule` (OneToOne profile vs héritage multi-table vs champs directs).
- [ ] ADR-002 : Choix de la file de tâches asynchrone (Celery/RQ/django-q2) et impact sur `docker-compose`en développement local et impact en production (usage sans docker).
- [ ] ADR-003 : Fournisseur(s) d'intégration SIV/immatriculation et décodage VIN (contraintes légales d'accès aux données SIV en France).
- [ ] ADR-004 : Stratégie de récupération du kilométrage (saisie manuelle vs télématique/OBD vs mixte) — impacte directement le modèle `Compteur` le mieux serait une récupération automatique des inforamtions mais plus contraignant si l'utilisateur doit brancher une prise OBD2. Un mixte serait parfait.
- [ ] ADR-005 : Modèle de calcul TCO/coût au km (périmètre des coûts inclus, fréquence de recalcul, stockage agrégé vs calculé à la volée).

## E. Migration / non-régression

- [ ] Script de migration de données pour les `Equipement` existants de type véhicule déjà saisis (si le client en a) vers le nouveau sous-type, sans perte d'historique (`StatutEquipement`, `Compteur`, `BonTravail` déjà liés).
- [ ] Vérifier l'impact sur `tasks/create_initial_data.py`, `tasks/perms_data.py` et les commandes `management/commands/init_data.py`/`seed_tp_data.py` (données de démo/seed à étendre pour la flotte).
