# Guide de contribution

Merci de l'intérêt que vous portez au projet GIMAO. Ce document décrit les conventions et le processus à suivre pour contribuer.

---

## Sommaire

- [Prérequis](#prérequis)
- [Mettre en place l'environnement de développement](#mettre-en-place-lenvironnement-de-développement)
- [Workflow Git](#workflow-git)
- [Conventions de nommage des branches](#conventions-de-nommage-des-branches)
- [Conventions de commit](#conventions-de-commit)
- [Cycle TDD (Red-Green-Refactor)](#cycle-tdd-red-green-refactor)
- [Lancer les tests](#lancer-les-tests)
- [Qualité de code (lint & format)](#qualité-de-code-lint--format)
- [Soumettre une Pull Request](#soumettre-une-pull-request)
- [Signaler un bug](#signaler-un-bug)

---

## Prérequis

- Python 3.9+
- Node.js 18+
- Docker et Docker Compose
- Git

---

## Mettre en place l'environnement de développement

```bash
git clone <url-du-depot>
cd GIMAO
docker compose -f docker-compose.dev.yml up -d
```

L'environnement complet démarre en une commande. Voir le [README](README.md) pour le détail des services disponibles.

Pour travailler sans Docker sur le backend :

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py init_data
python manage.py runserver
```

Pour le frontend :

```bash
cd frontend
npm install
npm run serve
```

---

## Workflow Git

1. Créer une branche depuis `main` (voir conventions ci-dessous).
2. Développer et commiter sur cette branche.
3. S'assurer que les tests passent.
4. Ouvrir une Pull Request vers `main`.
5. La branche est supprimée après merge.

Ne jamais commiter directement sur `main`.

---

## Conventions de nommage des branches

| Type | Format | Exemple |
|------|--------|---------|
| Fonctionnalité liée à un ticket | `SCRUM-<id>-<description-courte>` | `SCRUM-42-export-pdf-bt` |
| Correction de bug | `BUG-<description-courte>` | `BUG-fix-calcul-seuil` |
| Refactoring / technique | `TECH-<description-courte>` | `TECH-refactor-useApi` |

La description est en minuscules, mots séparés par des tirets, sans accents.

---

## Conventions de commit

Les messages de commit suivent le format [Conventional Commits](https://www.conventionalcommits.org/),
prefixe d'un [gitmoji](https://gitmoji.dev/) correspondant au type. Ce format est **obligatoire** :
il pilote `semantic-release` (voir [docs/SEMANTIC_RELEASE.md](docs/SEMANTIC_RELEASE.md)) pour calculer
la version, generer le `CHANGELOG.md` et publier la release GitHub.

```
<gitmoji> <type>(<scope>): <description courte en français>
```

Types et gitmojis :

| Type | Gitmoji | Usage | Effet version (semantic-release) |
|------|---------|-------|------|
| `feat` | ✨ `:sparkles:` | Nouvelle fonctionnalité | MINOR |
| `fix` | 🐛 `:bug:` | Correction de bug | PATCH |
| `docs` | 📝 `:memo:` | Documentation uniquement | aucun |
| `style` | 🎨 `:art:` | Formatage, sans impact fonctionnel | aucun |
| `refactor` | ♻️ `:recycle:` | Refactoring sans changement de comportement | aucun |
| `perf` | ⚡️ `:zap:` | Amélioration de performance | PATCH |
| `test` | ✅ `:white_check_mark:` | Ajout ou modification de tests | aucun |
| `build` | 📦️ `:package:` | Build, dépendances | aucun |
| `ci` | 👷 `:construction_worker:` | Configuration CI/CD | aucun |
| `chore` | 🔧 `:wrench:` | Tâche technique diverse | aucun |

Breaking change : ajouter `!` après le type/scope (`feat(stock)!: ...`) et/ou un pied de
page `BREAKING CHANGE: <explication>` → déclenche une version MAJOR.

Exemples :

```
✨ feat(maintenance): ajouter le filtrage des BT par technicien

Fixes #42

🐛 fix(stock): corriger le calcul du stock disponible après distribution

Closes #57

📝 docs(readme): mettre à jour la section déploiement
```

La description est en français, commence par un verbe à l'infinitif, sans majuscule ni point final.
Quand le commit clôt une issue, ajouter `Fixes #NNN` / `Closes #NNN` / `Resolves #NNN` en pied de
message : GitHub ferme l'issue au merge et la relie automatiquement au Milestone en cours.

---

## Cycle TDD (Red-Green-Refactor)

Le TDD est **obligatoire** pour toute nouvelle fonctionnalité ou correction de bug non triviale.

1. **Red** — écrire un test qui décrit le comportement attendu et qui échoue (le code
   n'existe pas encore, ou reproduit le bug).
2. **Green** — écrire le code minimal nécessaire pour faire passer ce test, sans se
   soucier de l'élégance à ce stade.
3. **Refactor** — nettoyer le code (et/ou le test) sans changer le comportement observable ;
   les tests doivent rester au vert à chaque étape du refactor.

Répéter ce cycle par petites itérations plutôt que d'écrire toute l'implémentation puis
tous les tests a posteriori. La checklist TDD du template d'issue "Feature Request" et la
section "Impact sur les tests" du template de Pull Request tracent le respect de ce cycle.

---

## Lancer les tests

### Tests backend

```bash
cd backend
pytest
```

Pour voir la couverture :

```bash
pytest --cov=. --cov-report=html
```

Le rapport HTML est généré dans `backend/htmlcov/index.html`.

### Tests frontend

```bash
cd frontend
npm run test
```

Tous les tests doivent passer avant de soumettre une Pull Request.

---

## Qualité de code (lint & format)

### Backend (Ruff)

```bash
cd backend
ruff check .
ruff format --check .
```

### Frontend (ESLint + Prettier)

```bash
cd frontend
npm run lint
npm run format:check
```

Ces mêmes vérifications tournent dans le pipeline CI (`.github/workflows/ci.yml`) sur
chaque Pull Request : une PR avec un lint en échec ne peut pas être mergée.

---

## Soumettre une Pull Request

1. S'assurer que la branche est à jour avec `main` :
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. Vérifier que les tests et le lint passent en local (voir sections ci-dessus).

3. Ouvrir la Pull Request en utilisant le [template fourni](.github/pull_request_template.md) :
   - Titre au format Conventional Commits (ex. `feat(fleet): add VIN decoder integration`).
   - Description claire du contexte, de ce qui a changé et pourquoi.
   - Lien vers l'issue résolue via `Fixes #NNN` / `Closes #NNN` / `Resolves #NNN`
     (ferme l'issue et le Milestone associé au merge).
   - Section ADR renseignée si la PR introduit ou modifie une décision d'architecture
     (voir [docs/adr/0000-use-adr-template.md](docs/adr/0000-use-adr-template.md)).

4. La CI (lint, tests, couverture, audit de sécurité) doit être au vert avant revue.

5. Toute PR doit être relue (via `CODEOWNERS`) avant d'être mergée dans `main`.

6. Au merge sur `main`, `semantic-release` calcule automatiquement la version, met à
   jour le `CHANGELOG.md` et publie la Release GitHub (voir
   [docs/SEMANTIC_RELEASE.md](docs/SEMANTIC_RELEASE.md)).

---

## Signaler un bug

Ouvrir une issue via le template [🐛 Rapport de bug](.github/ISSUE_TEMPLATE/bug_report.yml),
qui demande :

- Le comportement attendu et le comportement observé.
- Les étapes de reproduction.
- Les logs ou captures d'écran.
- L'environnement (OS, navigateur, version/commit).

Pour une vulnérabilité de sécurité, ne pas ouvrir d'issue publique : voir [SECURITY.md](SECURITY.md).
