# Milestone M0 — Fondations du sous-domaine Véhicule

**Objectif** : poser le socle de données et d'architecture sans rien casser de l'existant GMAO générique. Cf. `MILESTONES_PROPAL.md`.

**Dépendances entrantes** : aucune (premier Milestone).
**Bloque** : tous les Milestones suivants (M1 à M7 dépendent de `VehiculeProfile`).

---

## TUS-001 — 📝 docs(fondations): ADR-001 stratégie de modélisation Equipement→Vehicule

**En tant qu'** équipe technique, **je veux** trancher formellement entre profil 1-1 (`VehiculeProfile`), héritage multi-table Django, ou champs directs sur `Equipement`, **afin de** figer une architecture de données stable avant tout développement dépendant.

**Critères d'acceptation**
- Given les 3 options évaluées dans `TODO.md` §A, When l'ADR est rédigé, Then il documente le contexte, les options, la décision retenue et ses conséquences (format ADR standard : Contexte / Décision / Conséquences).
- Le document est validé (relu) avant le démarrage de TUS-004.

**Spécifications techniques**
- Fichier : `docs/adr/0001-modelisation-vehicule.md`.
- Pas de code impacté à ce stade.

**Clean Code / TDD** : N/A (documentation). Revue par un second regard technique recommandée avant merge.

---

## TUS-002 — 📝 docs(fondations): ADR-002 choix de la file de tâches asynchrone

**En tant qu'** équipe technique, **je veux** choisir l'outil de file de tâches asynchrone (Celery+Redis, RQ, ou django-q2) et son impact sur `docker-compose.dev.yml`/`docker-compose.prod.yml` et sur un déploiement sans Docker, **afin de** préparer l'introduction de traitements différés (M1 notifications, M6 intégrations) sans dette d'architecture.

**Critères d'acceptation**
- Given les contraintes d'infra actuelles (Docker + Nginx + Gunicorn), When l'ADR est rédigé, Then il couvre : outil retenu, impact `docker-compose` (nouveau service worker + broker), impact déploiement non-Docker (`install.sh`/scripts), stratégie de repli si le broker est indisponible.

**Spécifications techniques**
- Fichier : `docs/adr/0002-file-taches-asynchrones.md`.

**Clean Code / TDD** : N/A (documentation).

---

## TUS-003 — ♻️ refactor(vehicule): factoriser EquipementViewSet avant extension

**En tant que** développeur, **je veux** extraire la logique métier d'`EquipementViewSet` (~830 lignes) vers des services/selectors dédiés, **afin de** pouvoir y greffer les besoins véhicule sans aggraver la dette et en respectant la consigne "logique métier hors ViewSet".

**Critères d'acceptation**
- Given le comportement actuel de `EquipementViewSet` couvert par les tests existants (`backend/tests/equipement/`), When la factorisation est terminée, Then tous les tests existants passent sans modification de leurs assertions (non-régression stricte).
- Le ViewSet ne contient plus que : routage, sérialisation, appel service, gestion de la réponse HTTP.

**Spécifications techniques**
- Fichiers : `backend/equipement/api/viewsets.py`, nouveau `backend/equipement/services.py` (ou `backend/equipement/selectors.py` + `services.py` selon convention retenue).
- Aucune migration.
- Aucun changement d'endpoint (contrat API inchangé).

**Clean Code / TDD** : Tests de non-régression exécutés avant/après (rouge impossible ici car refactor pur) ; ajouter des tests unitaires ciblés sur les nouveaux services si la couverture actuelle ne les exerçait qu'indirectement via l'API.

---

## TUS-004 — ✨ feat(vehicule): modèle VehiculeProfile

**En tant que** développeur, **je veux** créer le modèle `VehiculeProfile` (`OneToOneField(Equipement, primary_key=True)`) selon la décision de l'ADR-001, **afin de** porter les champs spécifiques automobile sans polluer `Equipement`.

**Critères d'acceptation**
- Given un `Equipement` existant, When un `VehiculeProfile` lui est associé, Then les champs VIN, immatriculation, genre (VL/PL/utilitaire/remorque), énergie, CO2, puissance fiscale, PTAC sont persistés et validés (VIN 17 caractères, immatriculation format SIV FR).
- Given un `Equipement` sans `VehiculeProfile`, When on interroge l'API équipement, Then le comportement est strictement identique à avant (pas de régression).

**Spécifications techniques**
- Fichier : `backend/equipement/models.py` (ou nouveau `backend/equipement/models_vehicule.py` si le fichier devient trop volumineux — à trancher selon taille finale).
- Migration Django associée.
- Ajout `'VEHICULE'` à `Equipement.TYPE_CHOICES`.
- Validation VIN/immatriculation : validators Django (`RegexValidator`) au niveau modèle.
- Admin : enregistrer `VehiculeProfile` dans `backend/equipement/admin.py`.

**Clean Code / TDD** : Tests Pytest dans `backend/tests/equipement/test_vehicule_profile_models.py` écrits en premier (création valide, validation VIN invalide, cascade suppression `Equipement`→`VehiculeProfile`).

---

## TUS-005 — ✨ feat(vehicule): endpoints CRUD VehiculeProfile

**En tant que** développeur, **je veux** exposer `VehiculeProfile` via l'API REST (`serializer`, `viewset`, `urls`) selon le pattern `api/{serializers,urls,views,viewsets}.py` déjà en place dans les autres apps, **afin de** permettre au frontend de créer/consulter/modifier les données véhicule.

**Critères d'acceptation**
- Given une requête POST valide sur l'endpoint véhicule, When elle est traitée, Then un `Equipement` (type=VEHICULE) et son `VehiculeProfile` sont créés en une seule transaction atomique.
- Given une requête sur un équipement non-véhicule, When on tente d'accéder aux champs véhicule, Then l'API retourne une 404 explicite (pas d'exception 500).

**Spécifications techniques**
- Fichiers : `backend/equipement/api/serializers.py` (nouveau `VehiculeSerializer` imbriquant `VehiculeProfile`), `backend/equipement/api/viewsets.py` (nouveau `VehiculeViewSet` héritant `ArchivableViewSetMixin`), `backend/equipement/api/urls.py`.
- Endpoint : `/api/vehicules/` (CRUD standard DRF router).
- Transaction : `django.db.transaction.atomic` dans le service (cf. TUS-003).

**Clean Code / TDD** : Tests `backend/tests/equipement/test_vehicule_viewset.py` (création, lecture, mise à jour, 404 sur équipement non-véhicule) écrits avant le viewset.

---

## TUS-006 — ✨ feat(rbac): permissions RBAC domaine véhicule

**En tant qu'** administrateur GMAO, **je veux** disposer de permissions `veh:viewList`, `veh:viewDetail`, `veh:create`, `veh:edit`, `veh:delete` rattachées à un nouveau `Module` "Véhicule", **afin de** pouvoir contrôler finement l'accès aux données flotte comme pour toute autre entité du système.

**Critères d'acceptation**
- Given un rôle sans permission `veh:create`, When un utilisateur de ce rôle tente de créer un véhicule via l'API, Then la requête est rejetée (403).
- Given le seed de données (`tasks/perms_data.py`), When il est exécuté, Then les nouvelles permissions sont créées et rattachées au module `veh`.

**Spécifications techniques**
- Fichiers : `backend/tasks/perms_data.py` (ajout des permissions), `backend/utilisateur/models.py` (`FULL_LABELS` — ajout des libellés, ou migration vers fixture si TUS dédiée traitée avant, cf. `TODO.md` §B).
- Vérification des permissions dans le service `VehiculeViewSet` (décorateurs/mixins existants du projet, à identifier dans `gimao/mixins.py` ou équivalent utilisé par les autres viewsets).

**Clean Code / TDD** : Tests `backend/tests/utilisateur/test_vehicule_permissions.py` (accès refusé sans permission, accès autorisé avec permission).

---

## TUS-007 — ♻️ refactor(fondations): finaliser le composable useApi

**En tant que** développeur frontend, **je veux** que tout appel HTTP passe par `composables/useApi.js`, **afin de** disposer d'un point d'entrée HTTP unique conforme à la consigne "aucun appel API direct dans les vues".

**Constat en réalisant le ticket** : `useApi.js` était déjà fonctionnel et utilisé dans 63 fichiers (l'évaluation initiale du bilan, basée sur une lecture partielle du fichier — d'anciens brouillons commentés en tête de fichier — était erronée ; corrigée dans `BILAN_EXISTANT.md`/`TODO.md`). Seuls 2 écarts réels trouvés par grep sur `axios`/`@/composables/http` :
- `SetPassword.vue` : import `axios` mort (l'appel réel utilisait déjà `useApi`) — supprimé.
- `ExportData.vue` : accès direct à `http.js` pour le téléchargement de fichier (`responseType: 'blob'` + lecture de l'en-tête `content-disposition` pour le nom de fichier), fonctionnalité que `useApi` n'exposait pas (`get`/`post`... ne retournent que `response.data`).

**Résolution** : ajout de `useApi().getRaw(url, params, extraConfig)`, qui retourne la réponse Axios complète (headers inclus) et accepte des options Axios additionnelles (`responseType`), pour couvrir ce cas sans dérogation à la règle. `ExportData.vue` migré dessus.

**Spécifications techniques**
- Fichier : `frontend/src/composables/useApi.js` (ajout de `getRaw`, JSDoc mise à jour).
- Fichiers migrés : `frontend/src/views/DataManagement/ExportData.vue` (`http.get` → `api.getRaw`), `frontend/src/views/Auth/SetPassword.vue` (suppression de l'import `axios` mort).

**Clean Code / TDD** : Tests Vitest `frontend/src/composables/__tests__/useApi.spec.js` (7 tests : get/post/remove, gestion loading/error, `getRaw` avec headers et query params). Suite complète frontend exécutée sans régression (110 tests passent, 5 skip pré-existants).

---

## US-001 — ✨ feat(vehicule): liste des véhicules (lecture seule)

**En tant que** gestionnaire de flotte, **je veux** consulter la liste des véhicules de mon parc, **afin de** avoir une vue d'ensemble de la flotte sans naviguer par la liste générique des équipements.

**Critères d'acceptation**
- Given des véhicules existants, When j'ouvre la vue liste, Then je vois immatriculation, marque/modèle, genre, statut, lieu, pour chaque véhicule.
- Given aucun véhicule créé, When j'ouvre la vue, Then un état vide explicite s'affiche (pas d'erreur, pas de tableau vide sans contexte).
- Le filtrage/tri respecte le pattern déjà en place dans `EquipmentList.vue`/`usePaginatedList.js`.

**Spécifications techniques**
- Fichier : `frontend/src/views/Vehicles/VehicleList.vue` (nouveau dossier `views/Vehicles/`).
- Composable réutilisé : `composables/usePaginatedList.js`, `composables/useApi.js` (TUS-007).
- Route : `router/index.js` (ou fichier routes équivalent), path `/VehicleList`, guard de permission `veh:viewList`.

**Clean Code / TDD** : Tests Vitest `frontend/src/components/__tests__/` ou `views/Vehicles/__tests__/VehicleList.test.js` (rendu liste, état vide, appel API via `useApi` mocké).

---

## US-002 — ✨ feat(vehicule): création d'un véhicule

**En tant que** gestionnaire de flotte, **je veux** créer une fiche véhicule avec ses caractéristiques (VIN, immatriculation, genre, énergie), **afin de** commencer à tracer un nouvel actif de la flotte dans la GMAO.

**Critères d'acceptation**
- Given un formulaire rempli avec des données valides, When je soumets, Then le véhicule est créé et je suis redirigé vers sa fiche détail.
- Given un VIN ou une immatriculation au mauvais format, When je soumets, Then une erreur de validation contextuelle s'affiche sans appel API (validation frontend) puis est re-vérifiée côté serveur.

**Spécifications techniques**
- Fichier : `frontend/src/views/Vehicles/CreateVehicle.vue`, inspiré de `views/Equipments/CreateEquipment.vue`.
- Composables : `useFormValidation.js`, `useValidationRules.js` (ajout règles VIN/immatriculation), `useApi.js`.
- Route : `/CreateVehicle`, guard `veh:create`.

**Clean Code / TDD** : Tests Vitest sur la validation de formulaire (VIN/immatriculation invalides) + test d'intégration soumission réussie (API mockée).

---

## US-003 — ✨ feat(vehicule): fiche détail et édition d'un véhicule

**En tant que** gestionnaire de flotte, **je veux** consulter et modifier la fiche complète d'un véhicule, **afin de** tenir les données à jour au fil du cycle de vie de l'actif.

**Critères d'acceptation**
- Given un véhicule existant, When j'ouvre sa fiche détail, Then je vois toutes les données `Equipement` + `VehiculeProfile` consolidées sur un seul écran.
- Given une modification valide, When je sauvegarde, Then les changements sont persistés et un accusé de succès s'affiche.

**Spécifications techniques**
- Fichiers : `frontend/src/views/Vehicles/VehicleDetail.vue`, `frontend/src/views/Vehicles/EditVehicle.vue`, inspirés de `EquipmentDetail.vue`/`EditEquipment.vue`.
- Routes : `/VehicleDetail/:id`, `/EditVehicle/:id`, guards `veh:viewDetail`/`veh:edit`.

**Clean Code / TDD** : Tests Vitest (affichage des champs consolidés, soumission de modification, gestion d'erreur serveur).

---

**Critère de sortie du Milestone** : un véhicule peut être créé/listé/édité avec ses champs spécifiques (VIN, immatriculation, genre, énergie), sans régression sur les équipements existants si possible, sinon ce n'est pas grave.
