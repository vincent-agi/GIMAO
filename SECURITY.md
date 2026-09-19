# Politique de sécurité

## Versions supportées

GIMAO suit [Semantic Versioning](https://semver.org/) via `semantic-release`. Seule la
dernière version MAJOR publiée reçoit des correctifs de sécurité actifs.

| Version | Supportée |
| ------- | --------- |
| Dernière version `x.y.z` (voir [Releases](https://github.com/vincent-agi/GIMAO/releases)) | ✅ |
| Versions antérieures | ❌ |

## Signaler une vulnérabilité

**Ne pas ouvrir d'issue publique** pour signaler une faille de sécurité : cela expose la
vulnérabilité avant qu'un correctif soit disponible.

Signaler de préférence via l'onglet [Security Advisories](https://github.com/vincent-agi/GIMAO/security/advisories/new)
du dépôt (divulgation privée GitHub). À défaut, contacter directement le mainteneur
([@vincent-agi](https://github.com/vincent-agi)) avec :

- Une description claire de la vulnérabilité et de son impact potentiel.
- Les étapes de reproduction (POC si possible, sans exploitation destructive).
- La version / le commit concerné.
- Toute suggestion de correctif, si disponible.

## Délais de traitement

| Étape | Délai cible |
| --- | --- |
| Accusé de réception | 72h |
| Évaluation de la sévérité (CVSS) | 7 jours |
| Correctif ou plan de mitigation | Selon sévérité (critique : sous 30 jours) |
| Publication du correctif + advisory | À la disponibilité du correctif |

## Divulgation responsable

- Merci de laisser un délai raisonnable pour corriger avant toute divulgation publique.
- Les rapports valides et responsables sont crédités dans l'advisory GitHub publié (sauf
  demande d'anonymat explicite).
- GIMAO n'opère pas de programme de bug bounty rémunéré à ce jour.

## Périmètre

Sont concernés : le backend Django/DRF (`backend/`), le frontend Vue.js (`frontend/`),
la configuration Docker/Nginx (`docker-compose*.yml`, `nginx/`) et les workflows
GitHub Actions (`.github/workflows/`).

Hors périmètre : vulnérabilités nécessitant un accès physique, ingénierie sociale, ou
dépendances tierces déjà signalées en amont (à reporter directement au projet concerné).
