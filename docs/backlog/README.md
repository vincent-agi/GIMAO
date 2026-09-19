# Backlog Phase 2 — Spécialisation Flotte

Index du plan de découpage détaillé issu de `MILESTONES_PROPAL.md` (Phase 1). Chaque fichier `M<n>-*.md` correspond à un Milestone GitHub à créer, et contient la liste ordonnée des issues (US/TUS) à créer dans ce Milestone.

## Conventions

**Nommage des issues** (titre GitHub) : `<gitmoji> <type>(<scope>): <titre court>`, identique à la convention de commit imposée.

| Type | Gitmoji | Usage |
|---|---|---|
| `feat` | ✨ `:sparkles:` | nouvelle fonctionnalité |
| `fix` | 🐛 `:bug:` | correction de bug |
| `refactor` | ♻️ `:recycle:` | refactoring sans changement de comportement |
| `test` | ✅ `:white_check_mark:` | ajout/renfort de tests |
| `docs` | 📝 `:memo:` | documentation, ADR |
| `chore` | 🔧 `:wrench:` | outillage, config, migration technique |
| `perf` | ⚡ `:zap:` | optimisation |

**Scopes utilisés** : `fondations`, `vehicule`, `reglementaire`, `incident`, `carburant`, `permis`, `maintenance`, `integrations`, `contrat`, `dashboard`, `rbac`, `notif`.

**US vs TUS** :
- **US** (User Story) : valeur métier visible par un rôle utilisateur (conducteur, technicien, gestionnaire de flotte, responsable GMAO, direction).
- **TUS** (Technical User Story) : fondation technique (modèle, migration, service, ADR, infra) nécessaire aux US qui en dépendent — formulée avec un rôle technique ("l'équipe technique" / "le développeur") pour respecter la même rigueur de structure.

**Ordre d'exécution** : au sein d'un même Milestone, les issues sont listées dans l'ordre de dépendance logique (TUS de socle avant US qui les consomment). Cet ordre est celui à respecter en Phase 3.

**Règle TDD** (rappel, valable pour toute issue) : tests Pytest (backend) ou Vitest (frontend) écrits avant ou en parallèle immédiat du code métier. Aucune PR n'est mergée sans couverture de test sur le nouveau code.

**Règle Clean Code** (rappel) : modèles Django explicites (pas de logique métier dans `models.py` au-delà des méthodes d'instance simples), logique métier dans des services/selectors (pas dans les ViewSets DRF), composants Vue sans appel API direct (toujours via `useApi`), SOLID/DRY/KISS.

## Table des Milestones

| Milestone | Fichier | Objectif |
|---|---|---|
| M0 | [M0-fondations.md](./M0-fondations.md) | Socle technique `Vehicule`, sans régression sur l'existant |
| M1 | [M1-reglementaire.md](./M1-reglementaire.md) | Carte grise, contrôle technique, alertes d'échéance |
| M2 | [M2-incidents-diagnostic.md](./M2-incidents-diagnostic.md) | Signalement d'avaries, sinistres, codes défaut OBD |
| M3 | [M3-kilometrage-carburant.md](./M3-kilometrage-carburant.md) | Fiabilisation kilométrage, suivi carburant |
| M4 | [M4-conducteurs-permis.md](./M4-conducteurs-permis.md) | Permis, habilitations, affectation conducteur/véhicule |
| M5 | [M5-maintenance-preventive.md](./M5-maintenance-preventive.md) | Pneumatiques, plans constructeur, coût d'exploitation V1 |
| M6 | [M6-integrations-api.md](./M6-integrations-api.md) | SIV/VIN, télématique, file asynchrone |
| M7 | [M7-contrats-tco-pilotage.md](./M7-contrats-tco-pilotage.md) | Contrats LLD/LOA, TCO complet, dashboard flotte |

Chaque Milestone GitHub doit être créé avec la description "Objectif" reprise de `MILESTONES_PROPAL.md`, et chaque issue de ce backlog doit être créée en y étant rattachée (`gh issue create --milestone "<nom>"`).
