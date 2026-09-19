# Bilan de l'existant — GMAO GIMAO

Date : 2026-09-19
Auteur : Analyse Lead Architect (Phase 1 — Diagnostic)

## 1. Stack technique

**Backend** : Django (DRF), architecture multi-app classique.
- Apps métier : `equipement`, `maintenance`, `stock`, `donnees`, `utilisateur`, `security`, `tasks`.
- Chaque app suit le pattern `api/{serializers,urls,views,viewsets}.py` — convention cohérente et déjà en place.
- ORM par défaut (SQLite/MySQL selon `.env`), pas de couche cache visible (pas de Redis).
- Authentification **custom** (pas de `django.contrib.auth.User` utilisé côté métier) : modèle `Utilisateur` propre, tokens opaques stockés hashés (SHA-256) dans `security.ApiToken`, durée de vie fixe 24h, portés via header `Authorization: Bearer`. Résolution de l'utilisateur courant faite par thread-local (`utilisateur/middleware.py`, `CurrentUserMiddleware`) — permet le logging d'audit (`Log`) sans passer l'utilisateur explicitement partout.
- `REST_FRAMEWORK.DEFAULT_AUTHENTICATION_CLASSES` et `DEFAULT_PERMISSION_CLASSES` sont **vides** — tout le contrôle d'accès repose sur le middleware custom + un système de permissions applicatif (`Module` / `Permission` / `RolePermission` / `UtilisateurPermission`), avec convention `<module>:<action>` (ex : `eq:edit`, `bt:start`). Système granulaire et déjà pensé pour extension modulaire.
- Tâches planifiées : `django-crontab` (`CRONJOBS` dans `settings.py`), 100% synchrone, pas de file de tâches asynchrone (pas de Celery/RQ/Dramatiq). 4 jobs actifs : `update_bt_status`, `update_counter`, `update_calendar_counters`, `delete_useless_tokens`.
- Tests : Pytest, bonne couverture par app (`backend/tests/<app>/...`), fixtures/factories centralisées (`tests/factories.py`). Base de tests saine pour du TDD.

**Frontend** : Vue 3 + Vuetify 3 + Vuex + Vue Router 4, build Vue CLI, tests Vitest + Testing Library.
- `apexcharts` / `vue3-apexcharts` pour le dashboard.
- `vue-cal` pour la vue calendrier (plans de maintenance).
- Composable `useApi` (via `composables/http.js`, wrapper axios) — le point d'entrée HTTP prévu par les consignes utilisateur existe déjà, mais son fichier actuel est presque entièrement **commenté/mort** (code désactivé) : à vérifier/réactiver avant d'imposer la règle "aucun appel API direct dans les vues".
- Arborescence `views/` très proche du découpage métier actuel (`Equipments`, `Interventions`, `Failures`, `Stocks`, `Users`, `DataManagement`, `PreventiveMaintenance`, `Calendar`).

**Infra** : Docker + docker-compose (dev/prod séparés), Nginx en frontal, scripts d'installation (`install.sh`, `reinstall.sh`, `update.sh`) — bonne base pour packaging on-premise chez un client flotte.

## 2. Modèle de données existant (cœur métier)

### App `equipement`
- `Equipement` (mixin `ArchivableMixin` → soft-delete via `archive`) : `numSerie`, `reference`, `designation`, `type` (enum figé : PEDAGOGIQUE/INFRASTRUCTURE/MECANIQUE/ELECTRIQUE/HYDRAULIQUE/PLURITECHNIQUE — **aucune valeur "véhicule"**), `dateMiseEnService`, `prixAchat`, `lienImage`, `lieu` (FK), `fabricant`/`fournisseur`/`modele`/`famille` (FK), coordonnées `x`/`y` (positionnement sur plan — **non pertinent pour un actif mobile**).
- `ModeleEquipement` (nom + `Fabricant`) — réutilisable tel quel comme "Marque + Modèle véhicule".
- `FamilleEquipement` (arbre auto-référencé) — réutilisable pour catégoriser VL / PL / utilitaires / remorques.
- `StatutEquipement` : historique de statuts (EN_FONCTIONNEMENT / DEGRADE / A_LARRET / HORS_SERVICE) — générique, réutilisable.
- **`Compteur`** : `nomCompteur`, `valeurCourante` (float), `unite` (texte libre), `estPrincipal`, `type` (texte libre, ex. "Calendaire") — **c'est déjà un modèle générique de relevé** (jours, heures machine...). C'est l'atout majeur pour la spécialisation flotte : le kilométrage peut s'y brancher **sans nouveau modèle**, juste une valeur métier `unite="km"`.
- **`Declencher`** : seuil de déclenchement liant un `Compteur` à un `PlanMaintenance` (valeur cible, écart moyen, anticipation en jours pour le calendaire, seuil glissant). Moteur de déclenchement déjà opérationnel et testé (`tasks/counterCron.py`) : crée automatiquement `DemandeIntervention` + `BonTravail` quand le seuil est atteint. **Directement réutilisable pour la vidange/CT/révision au kilométrage.**
- `Constituer` (M2M Equipement↔Consommable), `DocumentEquipement` (M2M via table pivot).

### App `maintenance`
- `DemandeIntervention` (DI) : cycle EN_ATTENTE → ACCEPTEE/REFUSEE → TRANSFORMEE, avec `statut_suppose` (perception opérateur).
- `BonTravail` (BT) : cycle EN_ATTENTE → EN_COURS → TERMINE → CLOTURE (+ EN_RETARD auto), type CORRECTIF/PREVENTIF, gestion pièces (`pieces_recuperees`), M2M consommables/documents, responsable de clôture.
- `PlanMaintenance` : rattaché à un `Equipement` + `TypePlanMaintenance`, flags `necessiteHabilitationElectrique` / `necessitePermisFeu` (première trace d'habilitations dans le modèle — précédent direct pour "permis de conduire requis").
- Tables pivot pour consommables/documents (BT, DI, PlanMaintenance) avec `Stocker`/`Magasin` (réservation par magasin, `BonTravailConsommableReservation`).

### App `stock`
- `Magasin` (fixe ou mobile — `estMobile`, déjà pensé pour "camion de technicien").
- `Consommable`, `PorterSur` (achat : fournisseur, fabricant, prix, date), `Stocker` (niveau par magasin), `EstCompatible` (compatibilité consommable ↔ modèle d'équipement).

### App `donnees` (référentiels transverses)
- `Lieu` (arbre), `Document` + `TypeDocument`, `Fabricant`, `Fournisseur`, `Adresse`. Modèle `Document` déjà générique et attachable à n'importe quelle entité via table pivot — réutilisable tel quel pour carte grise / attestation CT / attestation d'assurance.

### App `utilisateur`
- `Utilisateur` (auth custom, mot de passe hashé maison), `Role`, `Log` (audit générique par table/champ), `Module`/`Permission`/`RolePermission`/`UtilisateurPermission` (RBAC fin, convention `<module>:<action>`, ~90 permissions déjà nommées en dur dans `Permission.__str__` — **dette technique** : labels FR codés dans le modèle plutôt que dans un fichier de traduction/fixture).
- **Aucune notion de permis de conduire / habilitation de conduite** sur `Utilisateur` à ce jour — uniquement les flags booléens `necessiteHabilitationElectrique`/`necessitePermisFeu` côté `PlanMaintenance`, qui ne vérifient rien côté utilisateur.

### App `security`
- `ApiToken` (token opaque, hash SHA-256, expiration 24h, révocation manuelle). Pas de refresh token, pas de rotation, pas de notion de scope/portée.

## 3. Points forts à capitaliser

1. **`Compteur` + `Declencher` + cron `update_counter`** : moteur de maintenance préventive déjà générique et testé — c'est exactement le mécanisme nécessaire pour kilométrage → vidange/pneus/révision. Pas besoin de réinventer, juste d'enrichir (unités strictes, non-régression des relevés).
2. **`ArchivableMixin`** : soft-delete uniforme, déjà appliqué à `Equipement`, `Magasin`, `Consommable`, `DemandeIntervention`, `BonTravail`.
3. **`Document` générique + tables pivot** : couvre nativement carte grise, CT, attestation d'assurance, sans nouveau modèle de stockage fichier.
4. **RBAC modulaire `<module>:<action>`** : extension naturelle avec de nouveaux modules (`veh`, `permis`, `ct`, `carburant`, `pneu`, `contrat`) sans changer l'architecture de permissions.
5. **`ModeleEquipement`/`FamilleEquipement`/`Fabricant`** : couvrent déjà "Marque + Modèle" et "catégorie de véhicule" sans modification structurelle.
5bis. **`DemandeIntervention` (statut, `statut_suppose`, cycle EN_ATTENTE→ACCEPTEE→TRANSFORMEE) est déjà un mécanisme générique de signalement d'anomalie** par un opérateur/conducteur, avec transformation en `BonTravail` de type CORRECTIF déjà existant. C'est le point d'extension naturel pour la déclaration d'avaries véhicule (voyant, bruit anormal, accident, code défaut) — pas besoin d'un nouveau workflow, seulement d'un profil de métadonnées véhicule greffé dessus (cf. `TODO.md` / Milestone dédié).
6. **Découpage `api/{serializers,urls,views,viewsets}`** homogène par app — convention claire à reproduire pour une future app `vehicule`/`flotte`.
7. Couverture de tests Pytest correcte par domaine — base saine pour le TDD imposé en Phase 2/3.

## 4. Limites structurelles pour la spécialisation flotte

1. **`Equipement.TYPE_CHOICES` est un enum figé sans branche "véhicule"**, et aucune notion de sous-type polymorphe (pas de `VehiculeProfile` en 1-1). Ajouter des champs spécifiques (VIN, immatriculation, genre VL/PL, énergie, CO2, puissance fiscale) directement dans `Equipement` polluerait le modèle générique pour tous les autres types d'équipements pédagogiques/infrastructure.
2. **Champs `x`/`y` (position sur plan)** n'ont aucun sens pour un actif mobile — à rendre optionnels/nullables logiquement pour les véhicules (déjà nullable techniquement, mais sémantiquement à clarifier).
3. **`Compteur.unite` est un `CharField` libre** : aucune contrainte d'intégrité (ex. rien n'empêche un kilométrage de décroître, ni de mélanger "km"/"kilomètres"/"Km"). Pour un usage flotte fiable (facturation LLD, contrôle fraude), il faut une validation métier (monotonie du relevé, unité normalisée).
4. **Aucune app d'intégration externe** (pas de dossier `integrations`, pas de client HTTP abstrait pour API tierces). Toute automatisation SIV/immatriculation, télématique (relevé kilométrique auto), ou alertes constructeur devra être bâtie from scratch.
5. **Pas de file de tâches asynchrone** (`django-crontab` seulement, exécution synchrone within le process web au moment du tick cron). Un webhook entrant (télématique, notification constructeur) ou un appel API tiers avec latence/rate-limit ne peut pas être backgroundé proprement en l'état — **risque de bloquer un worker Gunicorn**. Nécessite l'introduction d'une file de tâches (Celery/RQ) — décision d'architecture à trancher via ADR.
6. **Pas de modèle de coût consolidé** : `prixAchat` existe sur `Equipement`, et le coût des pièces est indirectement traçable via `PorterSur`/`BonTravailConsommable`, mais **aucune agrégation TCO** (coût carburant + entretien + assurance + LLD ramené au km) n'existe. C'est pourtant l'objectif business n°1 ("réduire les coûts d'exploitation").
7. **Aucune notion de permis de conduire/habilitation** côté `Utilisateur` — seulement des flags côté `PlanMaintenance`. Il faudra un modèle `PermisConduire` (catégories B/C/C1/CE/D, FIMO/FCO, date d'expiration, visite médicale) et une règle métier reliant conducteur ↔ véhicule ↔ permis requis.
8. **`EquipementViewSet` (equipement/api/viewsets.py) concentre ~830 lignes de logique** dans le ViewSet — contrevient déjà à la directive "séparer la logique métier des ViewSets DRF" demandée pour la suite du projet. À factoriser (services/selectors) avant/pendant l'extension flotte, sinon la dette s'aggrave avec les nouveaux champs véhicule.
9. **`useApi.js` (frontend) largement commenté/inactif** — la règle "aucun appel API direct dans les vues, toujours via `useApi`" ne peut pas être appliquée en l'état ; le composable doit être finalisé/réactivé en priorité.
10. **`REST_FRAMEWORK` sans `DEFAULT_PERMISSION_CLASSES`** : le contrôle d'accès est entièrement custom et manuel dans chaque viewset (à vérifier au cas par cas) — pas de garde-fou déclaratif DRF. Point de vigilance pour toute nouvelle donnée sensible (ex. restreindre un conducteur à ne voir que son véhicule affecté).
11. **Pas de webhook / endpoint entrant public** pour recevoir des données poussées par un tiers (télématique, SIV) — uniquement des endpoints CRUD classiques.
12. **Labels de permissions codés en dur** dans `Permission.__str__` (`FULL_LABELS` dict) — pas industrialisable pour ~30+ nouvelles permissions flotte sans alourdir encore ce dictionnaire.

## 5. Synthèse

L'existant est **une base GMAO générique solide et bien testée**, avec un moteur de déclenchement préventif (`Compteur`/`Declencher`) directement réutilisable pour le kilométrique, un système documentaire et un RBAC extensibles sans refonte. Les vrais chantiers sont : **(a)** modéliser le sous-type "Véhicule" proprement (sans polluer `Equipement`), **(b)** construire une couche d'intégration API externe inexistante à ce jour (SIV, télématique, constructeurs) avec la question de l'asynchrone à trancher, **(c)** ajouter les entités réglementaires/métier automobile manquantes (carte grise, CT, pneus, permis, contrats LLD/LOA), **(d)** construire l'agrégation coût/TCO qui n'existe pas. Voir `TODO.md` pour le détail actionnable et `MILESTONES_PROPAL.md` pour le séquencement proposé.
