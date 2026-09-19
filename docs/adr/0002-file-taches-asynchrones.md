# 0002. File de tâches asynchrone

## Statut

Accepté

## Contexte

L'exécution des tâches planifiées de GIMAO repose aujourd'hui exclusivement sur
`django-crontab` (`CRONJOBS` dans `backend/gimao/settings.py`), qui exécute chaque job
de façon **synchrone**, au moment du tick cron, dans un process séparé du serveur
applicatif (cf. `BILAN_EXISTANT.md` §4.5).

La spécialisation flotte introduit deux besoins que ce mécanisme ne peut pas couvrir
proprement :

1. **Appels sortants vers des API tierces à latence variable** (décodage VIN/SIV,
   futurs fournisseurs télématiques ou constructeurs, M6) : un appel HTTP externe lent
   ou en timeout ne doit jamais bloquer un worker Gunicorn qui sert des requêtes
   utilisateur.
2. **Webhooks entrants** (relevé kilométrique télématique, codes défaut OBD
   automatiques, M6) : le traitement métier (mise à jour `Compteur`, création
   `CodeDefautOBD`, éventuelle création de `DemandeIntervention`) doit être découplé de
   la réception HTTP, qui doit accuser réception immédiatement (`202 Accepted`).

Options évaluées :

- **Celery + Redis** : standard de facto pour Django, écosystème mature (retry,
  monitoring via Flower, planification via `celery beat`), mais ajoute deux services
  d'infrastructure (worker + broker Redis).
- **RQ (Redis Queue)** : plus simple que Celery, toujours dépendant de Redis, moins
  riche en fonctionnalités de planification/retry avancées.
- **django-q2** : intégration Django native, supporte plusieurs brokers (y compris ORM
  comme broker, sans dépendance externe), plus léger à déployer.

## Décision

Le projet adopte **Celery avec Redis comme broker**.

Justification du choix face aux alternatives : le projet dispose déjà d'une
infrastructure Docker Compose (`docker-compose.dev.yml`/`docker-compose.prod.yml`)
capable d'accueillir un service Redis supplémentaire sans friction, et Celery est
l'écosystème le plus documenté pour les besoins identifiés (retry avec backoff
exponentiel sur les appels API tierces, visibilité des tâches en échec, extensible à
`celery beat` si des jobs cron doivent progressivement migrer hors de
`django-crontab`). django-q2, bien que plus léger, offre un écosystème de monitoring et
de documentation moins étendu pour un projet appelé à grandir sur ce périmètre
(intégrations M6 multiples).

Impact infrastructure :

- **Docker (dev/prod)** : ajout d'un service `redis` et d'un service `worker`
  (`celery -A gimao worker`) dans `docker-compose.dev.yml` et
  `docker-compose.prod.yml`. Le service `worker` partage l'image backend existante.
- **Déploiement sans Docker** (`install.sh`, `scripts/install.sh`) : ajout d'une étape
  d'installation de Redis (paquet système ou binaire) et d'un service systemd (ou
  équivalent) pour le worker Celery, documentée dans `GUIDE_INSTALLATION.md`.
- **`django-crontab` n'est pas remplacé** : les jobs déjà en place
  (`update_bt_status`, `update_counter`, `update_calendar_counters`,
  `delete_useless_tokens`) restent tels quels. Celery est réservé aux nouveaux besoins
  identifiés ci-dessus (appels API tierces, webhooks). Une migration complète vers
  `celery beat` pourra faire l'objet d'une ADR ultérieure si la coexistence des deux
  systèmes devient une source de confusion opérationnelle.
- **Tests** : Celery est configuré en mode `task_always_eager=True` dans
  `backend/gimao/settings_test.py`, pour que les tâches s'exécutent de façon
  synchrone pendant les tests, sans dépendance à un broker Redis réel dans la CI.

## Conséquences

**Positives**

- Les appels API tiers lents ou en échec n'impactent plus la disponibilité du serveur
  applicatif.
- Les webhooks entrants (M6) peuvent répondre immédiatement et déléguer le traitement,
  avec retry automatique en cas d'échec transitoire.
- Écosystème mature : supervision, retry/backoff, et extensibilité (`celery beat`) déjà
  disponibles sans développement supplémentaire.

**Négatives / coûts**

- Deux nouveaux services d'infrastructure à opérer (Redis, worker Celery), avec impact
  sur la procédure d'installation on-premise sans Docker (documentation à tenir à jour).
- Complexité opérationnelle supplémentaire (supervision du worker, gestion des tâches
  en échec) à intégrer aux procédures d'exploitation existantes.
- Coexistence temporaire de deux systèmes de tâches planifiées (`django-crontab` pour
  l'existant, Celery pour les nouveaux besoins) — acceptée sciemment pour limiter le
  risque de régression sur les jobs déjà en production, à réévaluer si elle devient une
  source de confusion.
