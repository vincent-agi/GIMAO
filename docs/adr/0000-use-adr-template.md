# 0000. Utiliser des Architecture Decision Records (format Nygard)

## Statut

Accepté

## Contexte

Le projet GIMAO prend regulierement des decisions d'architecture (choix techniques,
structuration backend/frontend, strategie de deploiement, integrations tierces) sans
trace ecrite systematique. Cela rend difficile, pour un nouveau contributeur (humain ou
agent IA), de comprendre *pourquoi* une decision a ete prise, quelles alternatives ont
ete ecartees, et quelles consequences etaient anticipees.

Sans ADR, les decisions d'architecture ne sont retrouvables qu'en archeologie git ou par
transmission orale, ce qui coute cher en relecture de code et en revue de Pull Request,
et fait courir le risque de revenir sur une decision deja tranchee sans le savoir.

## Décision

Le projet adopte les Architecture Decision Records au format popularise par Michael
Nygard, stockes dans `docs/adr/`.

Regles :

1. Un fichier par decision : `docs/adr/NNNN-titre-court-en-kebab-case.md`, `NNNN` etant
   un numero sequentiel a 4 chiffres (ce fichier est le `0000`).
2. Chaque ADR suit strictement la structure : `Titre`, `Statut`, `Contexte`, `Decision`,
   `Consequences`.
3. Statuts possibles : `Proposé`, `Accepté`, `Rejeté`, `Déprécié`, `Remplacé par ADR-NNNN`.
4. Une ADR n'est jamais supprimée ni reecrite retroactivement : une decision qui change
   se traduit par une nouvelle ADR qui remplace l'ancienne (statut mis a jour en
   consequence sur l'ancienne).
5. Toute Pull Request qui introduit ou modifie une decision d'architecture doit creer ou
   referencer une ADR (voir `.github/pull_request_template.md`, section ADR).
6. Une ADR est courte (une page maximum) : elle documente une decision, pas une
   specification technique detaillee.

## Conséquences

**Positives**

- Traçabilité complète des decisions d'architecture, consultable sans archeologie git.
- Onboarding plus rapide des nouveaux contributeurs et des agents IA travaillant sur le
  depot.
- Les alternatives ecartees et leurs raisons restent documentees, evitant de re-debattre
  des decisions deja tranchees.

**Négatives / coûts**

- Discipline supplementaire requise : chaque decision structurante doit etre documentee
  au moment ou elle est prise, sinon l'ADR perd de sa valeur.
- Risque de proliferation d'ADR si le seuil "decision d'architecture" (vs. detail
  d'implementation) n'est pas applique avec jugement.
