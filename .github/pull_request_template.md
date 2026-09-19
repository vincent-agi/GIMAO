<!--
Merci pour cette contribution !
Ce template garantit une tracabilite complete pour semantic-release (versioning, CHANGELOG,
fermeture auto des issues/milestones). Remplis chaque section, supprime les blocs qui ne
s'appliquent vraiment pas, et laisse les commentaires HTML : ils ne s'affichent pas dans la PR.
-->

## Type de changement (Conventional Commits)

<!-- Coche le(s) type(s) correspondant au contenu de cette PR. Le titre de la PR doit
     utiliser ce meme type, ex: feat(fleet): add VIN decoder integration -->

- [ ] `feat` — nouvelle fonctionnalite
- [ ] `fix` — correction de bug
- [ ] `docs` — documentation uniquement
- [ ] `style` — formatage, sans impact fonctionnel (espaces, points-virgules, etc.)
- [ ] `refactor` — refactorisation sans changement de comportement
- [ ] `perf` — amelioration de performance
- [ ] `test` — ajout/correction de tests
- [ ] `build` — systeme de build, dependances
- [ ] `ci` — configuration CI/CD
- [ ] `chore` — taches diverses (sans impact sur le code applicatif)

> [!WARNING]
> - [ ] **Cette PR contient un BREAKING CHANGE** (ex: `feat!:` ou pied de page `BREAKING CHANGE:`)
>   <!-- Si coche, decris precisement l'impact et la migration necessaire ci-dessous -->

<!-- Si BREAKING CHANGE coche, detaille ici : -->

## Description & Contexte

<!-- Resume clair : quel probleme est resolu, ou quelle fonctionnalite est ajoutee, et pourquoi. -->



### Issues liees

<!-- Obligatoire pour la tracabilite et la fermeture auto du Milestone en cours.
     Utilise un mot-cle GitHub par issue : Fixes #123 / Closes #123 / Resolves #123 -->

Fixes #

## Changements techniques principaux

<!-- Liste les modifications cles : migrations BD, nouveaux endpoints, composants UI,
     scripts, config, etc. -->

-
-

## Architecture Decision Records (ADR)

Cette PR introduit ou modifie une decision d'architecture ? **Oui / Non**

<!-- Si Oui : cree/mets a jour un fichier dans docs/adr/ et renseigne le lien ci-dessous. -->

- Lien ADR : `docs/adr/`

## Impact sur les tests & Couverture (TDD)

- [ ] Tests unitaires et/ou d'integration ajoutes ou mis a jour

<!-- Comment verifier manuellement ce changement (etapes, donnees de test, endpoints, ecrans) -->

**Comment tester manuellement :**



## Checklist de validation finale (Reviewer & Author)

- [ ] Le titre de la PR respecte strictement la norme Conventional Commits (ex: `feat(fleet): add VIN decoder integration`)
- [ ] Le code respecte les regles de Clean Code et le linter passe sans erreur
- [ ] Les tests (TDD) passent avec succes (`pytest` / `npm run test`)
- [ ] La documentation (`README.md`, PHPDoc/JSDoc, OpenAPI/Swagger si pertinent) a ete mise a jour
