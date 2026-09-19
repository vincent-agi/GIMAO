# Semantic Release — guide rapide

Ce depot utilise [semantic-release](https://semantic-release.gitbook.io/) pour automatiser :

- le calcul de version (SemVer),
- la generation du `CHANGELOG.md`,
- la creation de la Release GitHub,
- la fermeture des issues/PR et du Milestone lies au commit.

Le pipeline se declenche automatiquement sur `main`, apres succes du workflow `Tests`
(`.github/workflows/tests.yml`). Voir `.github/workflows/release.yml` et `.releaserc.json`.

## Convention de commit (Conventional Commits)

Format : `<type>[scope optionnel]: <description>`

| Type commit | Effet version |
|---|---|
| `fix: ...` | PATCH (1.0.0 -> 1.0.1) |
| `feat: ...` | MINOR (1.0.0 -> 1.1.0) |
| `feat!: ...` ou pied de page `BREAKING CHANGE: ...` | MAJOR (1.0.0 -> 2.0.0) |
| `docs:`, `chore:`, `style:`, `refactor:`, `test:`, `ci:`, `build:`, `perf:` | Pas de release (sauf `perf` -> PATCH) |

Exemples :

```
feat(maintenance): ajout du filtre par statut sur les plans de maintenance

fix(auth): corrige l'expiration prematuree du token

feat(stock)!: renomme l'endpoint /api/stock/items en /api/stock/articles

BREAKING CHANGE: les clients doivent utiliser /api/stock/articles
```

## Relier un commit/PR a une issue ou un Milestone

Dans le message de commit (ou la description de PR), ajouter un mot-cle GitHub suivi du
numero d'issue :

```
fix(equipement): corrige le calcul du compteur horaire

Fixes #123
```

Mots-cles reconnus par GitHub : `Fixes`, `Closes`, `Resolves` (+ variantes). L'issue est
fermee automatiquement au merge sur `main`, et le plugin `@semantic-release/github` ajoute
un commentaire indiquant la version de release concernee.

Pour le Milestone : nommer le Milestone GitHub exactement comme la version produite
(ex. Milestone `1.4.0`). Si un Milestone porte le meme nom que la version publiee,
`@semantic-release/github` le ferme automatiquement.

## Fonctionnement du pipeline automatique

1. Push/merge sur `main`.
2. Le workflow `Tests` (`tests.yml`) tourne (backend pytest + frontend vitest).
3. Si `Tests` reussit, le workflow `Release` (`release.yml`) se declenche via `workflow_run`.
4. `semantic-release` (`npx semantic-release`) :
   - analyse l'historique des commits depuis la derniere release (`commit-analyzer`),
   - determine le prochain numero de version,
   - genere les notes de version (`release-notes-generator`),
   - met a jour `CHANGELOG.md` (`changelog`),
   - cree le tag Git + la Release GitHub, commente/ferme les issues/PR et le Milestone
     correspondant (`github`),
   - commite `CHANGELOG.md` sur `main` avec le message
     `:bookmark: chore(release): ${nextRelease.version} [skip ci]` (`git`).
5. Le `[skip ci]` evite de redeclencher `Tests`/`Release` sur ce commit de release.

Si aucun commit eligible (`feat`/`fix`/`BREAKING CHANGE`) n'est trouve depuis la derniere
release, `semantic-release` ne publie rien (comportement normal, pas une erreur).

## Notes d'installation locale

Le depot n'a pas de `package.json` racine avant cette configuration : un `package.json`
minimal (`private: true`) a ete cree pour porter `semantic-release` et ses plugins, sans
toucher aux projets `backend/` (Python) et `frontend/` (Vue), qui gardent leurs propres
`package.json`.

`package-lock.json` racine n'a pas pu etre genere dans cet environnement (acces reseau
npm bloque). A generer avant premiere execution en CI :

```bash
npm install
git add package-lock.json
git commit -m "chore: ajoute le lockfile npm racine pour semantic-release"
```

Une fois le lockfile commite, remplacer dans `release.yml` l'etape `npm install` par
`npm ci` (plus rapide, deterministe) et reactiver le cache npm sur `setup-node`.
