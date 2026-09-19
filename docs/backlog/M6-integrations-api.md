# Milestone M6 — Intégrations API externes

**Objectif** : automatiser l'acquisition de données, réduire la saisie manuelle, fiabiliser les données. Cf. `MILESTONES_PROPAL.md`.

**Dépendances entrantes** : M0 (ADR-002 file asynchrone tranchée), M2 (`CodeDefautOBD` existe déjà pour recevoir la source automatique), M3 (`Compteur` kilométrique normalisé, cible de la mise à jour automatique).
**Bloque** : aucun Milestone (les intégrations sont un enrichissement, pas un prérequis strict de M7).

---

## TUS-060 — 📝 docs(integrations): ADR-003 fournisseur SIV/VIN

**En tant qu'** équipe technique, **je veux** identifier et choisir le(s) fournisseur(s) d'accès aux données SIV/immatriculation et de décodage VIN, en tenant compte du fait que l'accès direct au SIV est réservé aux professionnels agréés en France, **afin de** sécuriser juridiquement et techniquement l'intégration prévue en TUS-064.

**Critères d'acceptation**
- Given le contexte réglementaire français (accès SIV restreint), When l'ADR est rédigé, Then il documente au moins 2 options de fournisseurs tiers agréés évalués, la décision retenue, le coût estimé, et les données réellement récupérables (immatriculation seule vs VIN complet vs historique).

**Spécifications techniques**
- Fichier : `docs/adr/0003-fournisseur-siv-vin.md`.

**Clean Code / TDD** : N/A (documentation).

---

## TUS-061 — 📝 docs(integrations): ADR-004 stratégie de récupération du kilométrage

**En tant qu'** équipe technique, **je veux** trancher la stratégie de récupération du kilométrage (saisie manuelle seule, télématique/OBD2 seule, ou mixte avec la saisie manuelle en repli), **afin de** cadrer le développement de TUS-065 sans sur-ingénierie ni sous-dimensionnement.

**Critères d'acceptation**
- Given les contraintes évoquées (contraignant si l'utilisateur doit brancher une prise OBD2), When l'ADR est rédigé, Then il retient une stratégie mixte : la saisie manuelle (M3) reste le mode nominal, la télématique vient l'enrichir/la fiabiliser quand disponible côté client, sans jamais bloquer le flux si le boîtier est absent.

**Spécifications techniques**
- Fichier : `docs/adr/0004-strategie-kilometrage.md`.

**Clean Code / TDD** : N/A (documentation).

---

## TUS-062 — ✨ feat(integrations): app integrations (client HTTP abstrait)

**En tant que** développeur, **je veux** créer une app Django `integrations` avec un client HTTP abstrait (gestion des clés API par fournisseur, retry/backoff, logging structuré des appels sortants), **afin de** disposer d'un socle commun réutilisable pour toutes les intégrations tierces (SIV, télématique, constructeurs).

**Critères d'acceptation**
- Given un appel à un fournisseur externe qui échoue (timeout, 5xx), When le client HTTP abstrait est utilisé, Then il applique une politique de retry configurable et journalise l'échec (sans exposer la clé API dans les logs).

**Spécifications techniques**
- Nouvelle app : `backend/integrations/` (`client.py` classe de base, `models.py` pour `AppelIntegration` — log d'appel avec statut/latence, `exceptions.py`).
- Stockage des clés API : variables d'environnement (`.env`), jamais en base en clair.
- Ajout dans `INSTALLED_APPS` (`backend/gimao/settings.py`).

**Clean Code / TDD** : Tests `backend/tests/integrations/test_client_http_abstrait.py` (retry, logging, non-exposition de la clé dans les logs — test explicite sur ce point de sécurité).

---

## TUS-063 — 🔧 chore(integrations): file de tâches asynchrone opérationnelle

**En tant que** développeur, **je veux** mettre en place l'outil retenu par l'ADR-002 (Celery/RQ/django-q2) avec son broker, **afin de** pouvoir exécuter les appels API tiers à latence variable et traiter les webhooks entrants sans bloquer un worker Gunicorn.

**Critères d'acceptation**
- Given une tâche asynchrone de test, When elle est déclenchée, Then elle s'exécute dans le worker dédié (pas dans le process web) et son résultat est consultable.
- Given l'environnement Docker existant, When `docker-compose.dev.yml`/`docker-compose.prod.yml` sont mis à jour, Then les nouveaux services (worker + broker) démarrent correctement avec `docker-compose up`.
- Given un déploiement sans Docker (scripts `install.sh`), When ils sont mis à jour, Then la documentation d'installation du broker/worker est ajoutée (`GUIDE_INSTALLATION.md`).

**Spécifications techniques**
- Fichiers : `docker-compose.dev.yml`, `docker-compose.prod.yml` (nouveaux services), `backend/gimao/celery.py` (ou équivalent selon outil retenu), `backend/requirements.txt`.
- `GUIDE_INSTALLATION.md` mis à jour pour le mode sans Docker.

**Clean Code / TDD** : Test `backend/tests/tasks/test_async_worker_setup.py` (tâche factice exécutée de bout en bout en environnement de test, avec broker en mode "eager"/synchrone pour les tests si l'outil le permet — éviter la dépendance à un broker réel dans la CI).

---

## TUS-064 — ✨ feat(integrations): décodage VIN / lookup immatriculation à la création véhicule

**En tant que** développeur, **je veux** appeler le fournisseur retenu (ADR-003) lors de la création d'un véhicule pour pré-remplir marque/modèle/genre/énergie à partir du VIN ou de l'immatriculation saisie, **afin de** réduire la saisie manuelle et fiabiliser les données véhicule.

**Critères d'acceptation**
- Given un VIN valide saisi, When l'appel au fournisseur réussit, Then les champs marque/modèle/genre sont pré-remplis dans le formulaire, modifiables avant validation.
- Given le fournisseur indisponible (timeout, erreur), When l'appel échoue, Then la création du véhicule reste possible en saisie 100% manuelle (pas de blocage fonctionnel sur une dépendance externe).

**Spécifications techniques**
- Backend : `backend/integrations/vin_lookup.py` (utilise le client TUS-062), endpoint `POST /api/integrations/vin-lookup/`.
- Frontend : appel déclenché depuis `CreateVehicle.vue` (US-002) au blur du champ VIN, via `useApi`.

**Clean Code / TDD** : Tests `backend/tests/integrations/test_vin_lookup.py` (succès, échec fournisseur → dégradation gracieuse, mock de l'appel HTTP externe — jamais d'appel réseau réel en test).

---

## TUS-065 — ✨ feat(integrations): endpoint entrant relevé kilométrique télématique

**En tant que** développeur, **je veux** exposer un endpoint webhook authentifié recevant des relevés kilométriques poussés par un boîtier télématique, **afin d'**alimenter automatiquement `Compteur` quand le client dispose de cet équipement, en complément de la saisie manuelle (M3).

**Critères d'acceptation**
- Given un webhook reçu avec une signature/clé valide, When traité, Then il met à jour le `Compteur` kilométrique du véhicule concerné via le même service de non-régression que la saisie manuelle (TUS-031, pas de règle dupliquée).
- Given un webhook avec une signature invalide, When reçu, Then il est rejeté (401/403) et journalisé sans traitement.
- Le traitement du payload est délégué à la file asynchrone (TUS-063) — l'endpoint accuse réception immédiatement (202) et traite en tâche de fond.

**Spécifications techniques**
- Fichier : `backend/integrations/webhooks.py` (vue Django simple, hors DRF ViewSet classique si authentification par signature spécifique), tâche asynchrone associée.
- Authentification : signature HMAC partagée avec le fournisseur télématique (clé en variable d'environnement).

**Clean Code / TDD** : Tests `backend/tests/integrations/test_webhook_kilometrage.py` (signature valide/invalide, mise à jour effective du compteur via réutilisation du service TUS-031, rejet si régression sans flag correction).

---

## TUS-066 — ✨ feat(integrations): endpoint entrant codes défaut OBD automatique

**En tant que** développeur, **je veux** exposer un webhook équivalent à TUS-065 pour les codes défaut OBD remontés automatiquement par un boîtier, **afin de** peupler `CodeDefautOBD` avec `source=AUTOMATIQUE` (modèle déjà créé en M2, sans migration ici).

**Critères d'acceptation**
- Given un webhook reçu avec un code DTC, When traité, Then un `CodeDefautOBD` est créé avec `source=AUTOMATIQUE`, et si le code correspond à une gravité configurée comme critique, une `DemandeIntervention`+`IncidentVehicule` est créée automatiquement (réutilisation du service TUS-020, pas de nouveau workflow).

**Spécifications techniques**
- Fichier : `backend/integrations/webhooks.py` (même pattern que TUS-065).
- Table de correspondance code DTC → gravité : constante applicative en V1 (paramétrage plus fin hors périmètre de ce ticket).

**Clean Code / TDD** : Tests `backend/tests/integrations/test_webhook_obd.py` (création code défaut, création DI automatique si gravité critique, absence de DI si gravité mineure).

---

## US-060 — ✨ feat(integrations): pré-remplissage automatique à la saisie du VIN

**En tant que** gestionnaire de flotte, **je veux** voir les champs marque/modèle/genre se pré-remplir automatiquement quand je saisis le VIN d'un nouveau véhicule, **afin de** gagner du temps et éviter les erreurs de saisie manuelle.

**Critères d'acceptation**
- Given je saisis un VIN valide dans `CreateVehicle.vue` (US-002), When je quitte le champ, Then les champs concernés se pré-remplissent avec un indicateur visuel "pré-rempli automatiquement, à vérifier".
- Given le service est indisponible, When je saisis le VIN, Then aucun blocage n'apparaît, je continue en saisie manuelle.

**Spécifications techniques**
- Frontend : `frontend/src/views/Vehicles/CreateVehicle.vue`, appel `useApi` vers TUS-064 au `@blur` du champ VIN, état de chargement visible.

**Clean Code / TDD** : Tests Vitest (pré-remplissage, dégradation gracieuse en cas d'échec API mocké en erreur).

---

## US-061 — ✨ feat(integrations): mise à jour automatique du kilométrique via télématique

**En tant que** gestionnaire de flotte disposant de véhicules équipés d'un boîtier télématique, **je veux** que le kilométrage de ces véhicules se mette à jour automatiquement, **afin de** ne plus dépendre de la saisie manuelle du conducteur pour ces véhicules-là.

**Critères d'acceptation**
- Given un véhicule équipé (flag à ajouter sur `VehiculeProfile` ou déduit de la présence de relevés automatiques récents), When un relevé télématique est reçu (TUS-065), Then la fiche véhicule affiche la source du dernier relevé (manuel vs automatique) et sa date.

**Spécifications techniques**
- Frontend : indicateur de source sur l'onglet kilométrage de `VehicleDetail.vue` (dépend de M3).
- Backend : champ `source` à ajouter au modèle `Compteur` ou à un historique de relevés si absent — **à vérifier en Phase 3** : si `Compteur` ne conserve que la valeur courante sans historique, envisager une table `RelevesCompteur` légère pour tracer source/date de chaque relevé (arbitrage technique, impact potentiel sur TUS-030/031).

**Clean Code / TDD** : Tests Vitest (affichage source) + Pytest (si nouvelle table d'historique introduite, tests de non-régression sur le comportement existant de `Compteur.valeurCourante`).

---

**Critère de sortie du Milestone** : création d'un véhicule accélérée par pré-remplissage automatique ; au moins une source de données externe alimente `Compteur` ou `CodeDefautOBD` sans saisie manuelle.
