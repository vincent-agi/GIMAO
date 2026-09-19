# GIMAO - Gestion Informatisée de la Maintenance Assistée par Ordinateur

GIMAO est une application web de GMAO (Gestion de la Maintenance Assistée par Ordinateur) conçue pour centraliser et simplifier la gestion des interventions techniques au sein d'une organisation.

Le système couvre l'ensemble du cycle de maintenance :
- les **opérateurs** signalent les pannes via des Demandes d'Intervention (DI) ;
- le **responsable GMAO** analyse les DI, crée les Bons de Travail (BT) et les affecte aux techniciens ;
- les **techniciens** consultent, renseignent et clôturent leurs interventions ;
- le **magasinier** gère les stocks de consommables et les approvisionnements.

---

## Sommaire

- [Installation rapide](#installation-rapide)
- [Fonctionnalités](#fonctionnalités)
- [Architecture technique](#architecture-technique)
- [Prérequis](#prérequis)
- [Installation en développement](#installation-en-développement)
- [Déploiement en production](#déploiement-en-production)
- [Variables d'environnement](#variables-denvironnement)
- [Structure du projet](#structure-du-projet)
- [Commandes de gestion](#commandes-de-gestion)
- [Tests](#tests)
- [API](#api)
- [Contribuer](#contribuer)

---

## Installation rapide

Pour installer l'application sans passer par les commandes Docker manuelles, un script d'installation automatisé est fourni à la racine du projet.

### 1. Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop) installé et lancé (attendre que l'icône de la baleine soit stable).

### 2. Installation

**Windows**

1. Récupérer le projet (clone Git ou téléchargement du dossier).
2. Ouvrir le dossier du projet.
3. Double-cliquer sur **`install.bat`**.
4. Attendre la fin du script : l'application s'ouvre automatiquement dans le navigateur sur `http://localhost`.

**Linux / macOS**

1. Récupérer le projet (clone Git ou téléchargement du dossier).
2. Ouvrir un terminal dans le dossier du projet.
3. Exécuter :
   ```bash
   ./install.sh
   ```
   (rendre le script exécutable si besoin : `chmod +x install.sh`)
4. Attendre la fin du script : l'application s'ouvre automatiquement dans le navigateur sur `http://localhost`.

Un seul compte est créé automatiquement, avec le rôle Responsable GMAO :
- Identifiant : `responsable`
- Aucun mot de passe par défaut : il est défini à la première connexion.

Aucune donnée n'est préchargée. Un jeu de données de démonstration peut être chargé depuis l'application (bouton dédié sur le tableau de bord, réservé au Responsable GMAO), voir [Commandes de gestion](#commandes-de-gestion).

### 3. Mettre à jour l'application

Une fois installée, pour récupérer une nouvelle version :
- Windows : double-cliquer sur **`update.bat`**, à la racine du projet.
- Linux / macOS : exécuter **`./update.sh`**, à la racine du projet.

Les données existantes sont conservées.

### Aller plus loin

Les scripts `install.bat` (Windows) et `install.sh` (Linux / macOS) s'appuient sur Docker Compose et les images publiées sur Docker Hub. Pour comprendre en détail ce qu'ils font, les adapter, ou pour un déploiement manuel (variables d'environnement, initialisation des données, gestion des conteneurs), voir la section [Déploiement en production](#déploiement-en-production).

Pour repartir de zéro (données effacées), utiliser `reinstall.bat` (Windows) ou `./reinstall.sh` (Linux / macOS).

---

## Fonctionnalités

### Cycle de maintenance

- Création de Demandes d'Intervention (DI) par les opérateurs avec description de la panne et photo optionnelle.
- Validation ou refus des DI par le responsable.
- Génération de Bons de Travail (BT) à partir des DI validées.
- Affectation d'un ou plusieurs techniciens à un BT.
- Suivi des statuts : `assigné` → `en cours` → `terminé` → `clos`.
- Timeline calendaire des interventions planifiées.

### Gestion des équipements

- Catalogue d'équipements avec modèle, fabricant, localisation (site / bâtiment / salle).
- Statuts d'équipement (en service, en panne, en maintenance, hors service).
- Compteurs de maintenance (heures, kilomètres, cycles) avec seuils d'alerte.
- Historique des pannes et des interventions par équipement.

### Stocks et approvisionnements

- Gestion des consommables par magasin.
- Enregistrement des achats avec distribution par magasin.
- Suivi des entrées/sorties de stock à chaque BT.
- Alertes de seuil minimal de stock.

### Gestion des utilisateurs

- Rôles : `Opérateur prod`, `Technicien prod`, `Technicien maintenance`, `Magasinier`, `Responsable GMAO`.
- Gestion des permissions par module et par action (lecture, écriture, suppression).
- Journalisation des actions (table, type d'opération, utilisateur, champs modifiés, date).

### Exports et rapports

- Export des données (équipements, interventions, stocks) au format Excel.
- Swagger UI disponible à `/api/swagger/` pour explorer l'API.

---

## Architecture technique

| Couche | Technologie | Version |
|--------|-------------|---------|
| Backend | Python + Django + Django REST Framework | Python 3.9, Django 4.2 |
| Base de données | MariaDB | 10.6 |
| Frontend | Vue.js + Vuetify | Vue 3, Vuetify 3 |
| Serveur web | Nginx | alpine |
| Conteneurisation | Docker + Docker Compose | - |
| Authentification | Token personnalisé (middleware `ApiTokenMiddleware`) | - |

### Composants frontend notables

- `vue-cal` : calendrier/timeline des interventions
- `vue3-apexcharts` : graphiques et indicateurs du tableau de bord
- `vuex` : état global (utilisateur connecté, permissions)
- `vue-router` : navigation SPA

### Tâches planifiées (cron)

- `update_bt_status` : mise à jour automatique des statuts de BT (midi et minuit)
- `update_counter` : mise à jour des compteurs d'équipements (3h00)
- `update_calendar_counters` : actualisation des dates de prochaine maintenance (minuit)
- `delete_useless_tokens` : nettoyage des tokens expirés (minuit)

---

## Prérequis

### Pour le développement

- Python 3.9+
- Node.js 18+
- Docker et Docker Compose (pour lancer MariaDB localement)
- `mysqlclient` requiert `libmysqlclient-dev` sur Linux ou les Microsoft C++ Build Tools sur Windows

### Pour la production

- Docker et Docker Compose
- Un fichier `.env.prod` à la racine du projet (voir [Variables d'environnement](#variables-denvironnement))

---

## Installation en développement

### 1. Cloner le dépôt

```bash
git clone <url-du-depot>
cd GIMAO
```

### 2. Lancer l'environnement complet avec Docker

```bash
docker compose -f docker-compose.dev.yml up -d
```

Services disponibles :
- Frontend : `http://localhost:8081`
- Backend (API) : `http://localhost:8000`
- phpMyAdmin : `http://localhost:8080`
- Locust (tests de charge) : `http://localhost:8089`

### 3. Développement sans Docker

#### Backend

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py init_data       # Crée les rôles et permissions de base
python manage.py runserver
```

#### Frontend

```bash
cd frontend
npm install
npm run serve
```

Le frontend est configuré pour proxyfier les requêtes `/api` vers `http://localhost:8000` (via `vue.config.js`).

---

## Déploiement en production

### 1. Préparer le fichier d'environnement

Copier et adapter le fichier d'exemple :

```bash
cp .env.prod.example .env.prod   # si un exemple est fourni
# ou créer .env.prod manuellement (voir section Variables d'environnement)
```

Sous Windows, copier également le fichier pour la substitution Docker Compose :

```powershell
Copy-Item .env.prod .env
```

### 2. Construire et démarrer les conteneurs

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

L'application est accessible sur `http://localhost`.
phpMyAdmin est disponible sur `http://localhost:8080`.

### 3. Initialiser les données (premier lancement uniquement)

Si la base de données est vide, les migrations et l'initialisation sont exécutées automatiquement au démarrage du conteneur backend. En cas d'erreur de migration, exécuter dans l'ordre :

```bash
docker exec -it gimao-prod-backend-1 python manage.py migrate tasks --fake
docker exec -it gimao-prod-backend-1 python manage.py migrate
docker exec -it gimao-prod-backend-1 python manage.py init_data
```

### 4. Charger les données de démonstration (optionnel)

```bash
docker exec -it gimao-prod-backend-1 python manage.py seed_tp_data
```

Cette commande purge les données utilisateur existantes et recharge un jeu de données complet (utilisateurs, équipements, interventions, stocks).

### Persistance des données

Les données de la base sont stockées dans le volume Docker `db_data`. Elles survivent à `docker compose down` et sont restaurées au prochain `docker compose up`. Pour supprimer définitivement les données :

```bash
docker compose -f docker-compose.prod.yml down -v
```

---

## Variables d'environnement

Créer un fichier `.env.prod` à la racine du projet. Ce fichier ne doit **jamais être versionné** (il est dans `.gitignore`).

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Clé secrète Django. Générer avec `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `MYSQL_DATABASE` | Nom de la base de données |
| `MYSQL_USER` | Utilisateur MariaDB |
| `MYSQL_PASSWORD` | Mot de passe de l'utilisateur MariaDB |
| `MYSQL_ROOT_PASSWORD` | Mot de passe root MariaDB |
| `DJANGO_SUPERUSER_USERNAME` | Nom du compte Django Admin créé automatiquement au démarrage |
| `DJANGO_SUPERUSER_PASSWORD` | Mot de passe du compte Django Admin |
| `DJANGO_SUPERUSER_EMAIL` | Email du compte Django Admin |

Les variables `DB_HOST` et `DB_PORT` sont injectées directement par `docker-compose.prod.yml` (valeurs `db` et `3306`) et n'ont pas besoin d'être dans `.env.prod`.

---

## Structure du projet

```
GIMAO/
├── backend/                    # Application Django
│   ├── donnees/                # Données de référence (fabricants, fournisseurs, localisations)
│   ├── equipement/             # Équipements, compteurs, statuts, pannes
│   ├── exportData/             # Exports Excel
│   ├── gimao/                  # Configuration Django (settings, urls, middleware)
│   ├── maintenance/            # Demandes d'intervention (DI) et Bons de Travail (BT)
│   ├── security/               # Tokens d'authentification, logs d'activité
│   ├── stock/                  # Consommables, magasins, fournitures
│   ├── tasks/                  # Tâches planifiées (cron jobs)
│   │   └── management/commands/
│   │       ├── init_data.py    # Initialisation des rôles et permissions
│   │       └── seed_tp_data.py # Chargement d'un jeu de données de démonstration
│   ├── tests/                  # Tests unitaires et d'intégration (pytest)
│   ├── utilisateur/            # Modèle utilisateur, rôles, permissions, middleware
│   ├── Dockerfile.dev
│   ├── Dockerfile.prod
│   └── requirements.txt
│
├── frontend/                   # Application Vue.js
│   └── src/
│       ├── assets/             # Images, polices
│       ├── components/         # Composants réutilisables (formulaires, tableaux, etc.)
│       │   ├── common/         # BaseForm, FormField, FormSelect, DataTable…
│       │   └── Forms/          # Formulaires métier (équipements, BT, DI, stocks…)
│       ├── composables/        # Logique réutilisable (useApi, usePermissions…)
│       ├── store/              # Vuex (état global : utilisateur, permissions)
│       ├── router/             # Routes de l'application
│       ├── utils/              # Constantes, helpers
│       └── views/              # Pages de l'application
│           ├── Auth/           # Connexion
│           ├── Calendar/       # Timeline des interventions
│           ├── Dashboard/      # Tableau de bord
│           ├── DataManagement/ # Gestion des données de référence
│           ├── Equipments/     # Gestion des équipements
│           ├── Failures/       # Pannes
│           ├── Interventions/  # DI et BT
│           ├── Notices/        # Notices techniques
│           ├── Stocks/         # Stocks et approvisionnements
│           └── Users/          # Gestion des utilisateurs et permissions
│
├── nginx/
│   └── nginx.conf              # Configuration du reverse proxy
│
├── docker-compose.dev.yml      # Environnement de développement
└── docker-compose.prod.yml     # Environnement de production
```

### Architecture backend (Django apps)

Chaque application Django suit la structure standard DRF :

```
<app>/
├── models.py           # Modèles de données
├── api/
│   ├── serializers.py  # Sérialisation DRF
│   ├── viewsets.py     # Vues API (CRUD)
│   └── urls.py         # Routes de l'app
└── migrations/         # Migrations de base de données
```

---

## Commandes de gestion

### `init_data`

Crée les rôles (`Opérateur prod`, `Technicien prod`, `Technicien maintenance`, `Magasinier`, `Responsable GMAO`), les modules et les permissions associées. Idempotente : peut être relancée sans risque.

```bash
python manage.py init_data
```

---

## Tests

### Tests backend (pytest)

```bash
cd backend
pytest
```

Les tests utilisent une base de données SQLite en mémoire définie dans `gimao/settings_test.py`. La configuration pytest est dans `pytest.ini`.

Pour générer un rapport de couverture :

```bash
pytest --cov=. --cov-report=html
```

### Tests frontend (Vitest)

```bash
cd frontend
npm run test
```

---

## API

La documentation interactive de l'API est générée automatiquement par `drf-yasg` et disponible aux adresses suivantes lorsque l'application est en cours d'exécution :

- Swagger UI : `http://localhost/api/swagger/`
- ReDoc : `http://localhost/api/redoc/`
- Schéma JSON : `http://localhost/api/swagger.json`

### Authentification

Toutes les requêtes API (hors login) nécessitent un token dans l'en-tête HTTP :

```
Authorization: Token <votre-token>
```

Le token est obtenu via `POST /api/auth/login/` avec les identifiants de l'utilisateur.

### Principaux endpoints

| Ressource | Endpoint |
|-----------|----------|
| Authentification | `/api/auth/` |
| Utilisateurs | `/api/utilisateurs/` |
| Équipements | `/api/equipements/` |
| Demandes d'intervention | `/api/demandes/` |
| Bons de travail | `/api/bons-de-travail/` |
| Consommables | `/api/consommables/` |
| Fabricants / Fournisseurs | `/api/fabricants/`, `/api/fournisseurs/` |
| Stocks (fournitures) | `/api/fournitures/` |
| Exports | `/api/export/` |

---

## Contribuer

### Processus de contribution

1. Forker le dépôt et créer une branche depuis `main` :
   ```bash
   git checkout -b feature/nom-de-la-fonctionnalite
   ```

2. Respecter les conventions de nommage existantes (noms de variables en français côté Django, composants Vue en PascalCase).

3. Écrire ou mettre à jour les tests concernés.

4. S'assurer que tous les tests passent avant de soumettre une Pull Request.

5. Décrire clairement les changements apportés dans la Pull Request.

### Ajouter une nouvelle app Django

1. Créer l'app : `python manage.py startapp <nom>`
2. L'ajouter dans `INSTALLED_APPS` de `gimao/settings.py`
3. Créer la structure `api/serializers.py`, `api/viewsets.py`, `api/urls.py`
4. Inclure les URLs dans `gimao/urls.py`

### Conventions de code

- Python : PEP 8, noms de champs Django en `camelCase` par cohérence avec l'existant
- Vue.js : Options API ou Composition API selon le contexte du composant existant
- Pas de logique métier dans les vues Vue, utiliser les composables (`src/composables/`)
- Les appels API passent tous par le composable `useApi` (`src/composables/useApi.js`)

---

## Licence

Ce projet est distribué sous licence **GNU Affero General Public License v3 (AGPL-3.0)**.

Toute modification ou utilisation du code (y compris pour offrir le logiciel en tant que service en ligne) impose de publier le code source modifié sous la même licence. Voir le fichier [LICENSE](LICENSE) pour le texte complet.
