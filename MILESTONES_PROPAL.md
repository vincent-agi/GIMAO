# Proposition de Milestones — Spécialisation Flotte

Séquencement proposé pour transformer GIMAO en GMAO flotte automobile/poids lourds. Chaque milestone est livrable et testable indépendamment. Détail des User Stories en Phase 2 (après GO).

## M0 — Fondations du sous-domaine Véhicule
**Objectif** : poser le socle de données et d'architecture sans rien casser de l'existant GMAO générique.
- ADR-001 (stratégie `Equipement`→`Vehicule`) et ADR-002 (file de tâches asynchrone) tranchés et rédigés.
- Modèle `VehiculeProfile` (ou équivalent retenu par l'ADR) créé et migré, branché sur `Equipement`.
- Nouveaux `Module`/`Permission` RBAC pour le domaine véhicule.
- Factorisation minimale d'`EquipementViewSet` pour permettre l'extension propre (services/selectors).
- `useApi.js` frontend finalisé et vue `views/Vehicles/VehicleList` de base (lecture seule) branchée dessus.
- **Critère de sortie** : un véhicule peut être créé/listé/édité avec ses champs spécifiques (VIN, immatriculation, genre, énergie), sans régression sur les équipements existants si possible, sinon ce n'est pas grave.

## M1 — Cycle de vie réglementaire du véhicule
**Objectif** : traçabilité documentaire et échéances légales, cœur de la réduction de risque/coût.
- Modèles `CarteGrise`, `ControleTechnique` (historique + échéance branchée sur `Compteur`/`Declencher` en mode calendaire).
- Rattachement au modèle `Document` existant pour les pièces jointes (carte grise scannée, PV de contrôle technique).
- Alerte automatique (email a minima) à l'approche d'une échéance CT — premier usage du système de notification (à créer).
- Vues frontend associées (détail véhicule enrichi, upload documents).
- **Critère de sortie** : un CT arrivant à échéance (< 60 jours) génère une alerte et, si configuré, un `BonTravail` préventif via le moteur existant.

## M2 — Signalement d'avaries, incidents & diagnostic véhicule
**Objectif** : couvrir tout le cycle de vie réactif du véhicule (pas seulement le réglementaire planifié) — voyants tableau de bord, bruits anormaux, accidents de la route, codes défaut remontés par capteurs/valise diagnostic, usure constatée hors plan préventif. Ce milestone étend le mécanisme existant `DemandeIntervention`/`BonTravail` (déjà générique, déjà en cycle CORRECTIF) plutôt que d'en recréer un.
- Profil `IncidentVehicule` (1-1 sur `DemandeIntervention`, même pattern que `VehiculeProfile` sur `Equipement`) : `type_avarie` (voyant allumé, bruit anormal, accident de la route, code défaut, usure signalée, autre), gravité, immobilisation du véhicule oui/non.
- Modèle `Sinistre` : date/lieu de l'accident, tiers impliqués, dégâts constatés, numéro de déclaration d'assurance, expertise — rattaché à l'`IncidentVehicule` de type "accident de la route".
- Modèle `CodeDefautOBD` : code DTC, description, date de lecture, source (`MANUEL` — saisie technicien après passage de la valise diagnostic, ou `AUTOMATIQUE` — remontée boîtier OBD, cette dernière source étant alimentée par M6 Intégrations) — rattaché à l'incident ou directement au véhicule.
- Formulaire de signalement enrichi côté frontend (`CreateFailure` existant étendu, ou nouvelle vue `CreateIncidentVehicule`) permettant à un conducteur de déclarer voyant/bruit/accident/code défaut sans changer le workflow DI→BT connu des utilisateurs.
- Nouveaux `Module`/`Permission` RBAC (`incident:*`, `sinistre:*`, `obd:*`).
- **Critère de sortie** : un conducteur signale un voyant allumé ou un accident via le même écran que les anomalies actuelles ; la DI générée porte les métadonnées véhicule (type d'avarie, sinistre le cas échéant) et suit le cycle DI→BT existant sans modification du moteur.

## M3 — Suivi kilométrique & carburant fiabilisé
**Objectif** : données de terrain fiables — base de tout calcul de coût et de maintenance prédictive.
- Normalisation de `Compteur.unite` (choix contraint) + règle de non-régression du relevé kilométrique.
- Modèle `PleinCarburant`/`Ravitaillement`, saisie manuelle en V1 (API télématique reportée à M6).
- Calcul de consommation moyenne (L/100km) et coût carburant par véhicule.
- **Critère de sortie** : historique des pleins consultable, consommation moyenne affichée sur la fiche véhicule.

## M4 — Conducteurs, permis & habilitations
**Objectif** : traçabilité conducteur ↔ véhicule ↔ droit de conduire, prérequis légal flotte entreprise.
- Modèles `PermisConduire`, `HabilitationConduite` (FIMO/FCO, visite médicale), rattachés à `Utilisateur`.
- Modèle `AffectationVehicule` (historique conducteur/véhicule).
- Alerte d'expiration de permis/habilitation (réutilise le système de notification de M1).
- Contrôle d'accès : un conducteur ne peut se voir affecter un véhicule nécessitant une catégorie de permis qu'il ne détient pas (règle métier + extension éventuelle de `PlanMaintenance.necessitePermisFeu`-like sur le véhicule).
- **Critère de sortie** : impossible d'affecter un conducteur sans permis valide de la bonne catégorie ; historique des affectations consultable.

## M5 — Maintenance préventive spécialisée automobile
**Objectif** : étendre le moteur de maintenance préventive existant aux spécificités auto (au lieu de le refaire).
- Modèle `Pneumatique` (historique pose/usure) + déclenchement préventif au kilométrage (réutilise `Compteur`/`Declencher`).
- Plans de maintenance type constructeur (vidange, courroie, filtres) pré-paramétrables par modèle de véhicule (`ModeleEquipement` déjà existant).
- Début de l'agrégation `CoutExploitationVehicule` (carburant + pièces + main d'œuvre, hors LLD à ce stade) — intègre déjà les coûts correctifs issus des incidents de M2.
- **Critère de sortie** : une vidange programmée au kilométrage génère automatiquement un BT préventif, comme c'est déjà le cas pour les équipements génériques.

## M6 — Intégrations API externes
**Objectif** : automatiser l'acquisition de données, réduire la saisie manuelle, fiabiliser les données.
- ADR-003 (fournisseur SIV/VIN) et ADR-004 (stratégie kilométrage) tranchés.
- App `integrations` créée, file de tâches asynchrone opérationnelle (issue de M0/ADR-002).
- Décodage VIN / lookup immatriculation à la création d'un véhicule (pré-remplissage marque/modèle/genre).
- Relevé kilométrique automatique si source télématique disponible côté client (sinon la saisie manuelle de M3 reste le mode nominal).
- Remontée automatique des codes défaut OBD (`CodeDefautOBD.source = AUTOMATIQUE`, alimente le modèle créé en M2) si boîtier disponible côté client.
- Veille alertes constructeur/rappels (best-effort selon disponibilité API par marque, périmètre à confirmer avec le client).
- **Critère de sortie** : création d'un véhicule accélérée par pré-remplissage automatique ; au moins une source de données externe alimente `Compteur` ou `CodeDefautOBD` sans saisie manuelle.

## M7 — Contrats, TCO & pilotage flotte
**Objectif** : objectif business final — visibilité coût complet et aide à la décision grâce aux données saisies et/ou temps réel grâce aux prises OBD (renouvellement, achat vs LLD).
- Modèles `ContratLLD`/`ContratLOA`, suivi de dépassement kilométrique contractuel.
- ADR-005 (modèle de calcul TCO) implémenté — `CoutExploitationVehicule` complet (carburant + entretien + assurance + LLD/LOA + sinistres).
- Dashboard flotte dédié (KPIs coût/km, disponibilité, échéances à venir consolidées, fréquence d'incidents par véhicule et/ou par conducteur) sur `apexcharts`.
- Exports enrichis (`ExportData.vue` existant) pour le reporting flotte.
- **Critère de sortie** : un gestionnaire de flotte visualise le coût complet au km de chaque véhicule et les échéances critiques à venir sur un seul écran et peut connait les métriques technique (remontées OBD) des véhicules quand disponible.

---

**Non couvert par ce séquencement (hors périmètre proposé, à confirmer)** : géolocalisation temps réel / cartographie de flotte, gestion des amendes/infractions routières, intégration carte carburant tierce (paiement), module éco-conduite. À arbitrer si le client en exprime le besoin — ajoutables en milestone M8+ sans remise en cause de l'architecture ci-dessus.
