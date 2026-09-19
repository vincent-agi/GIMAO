# 0001. Modélisation du sous-type Véhicule

## Statut

Accepté

## Contexte

La spécialisation de GIMAO vers la gestion de flotte automobile nécessite d'ajouter des
champs spécifiques (VIN, immatriculation, genre VL/PL/utilitaire, énergie, CO2, puissance
fiscale, PTAC) qui n'ont de sens que pour un sous-ensemble des `Equipement` existants
(cf. `BILAN_EXISTANT.md` §4.1 et `TODO.md` §A).

Trois options ont été évaluées :

1. **Profil `VehiculeProfile` en relation 1-1** (`OneToOneField(Equipement,
   primary_key=True)`) : `Equipement` reste le socle générique (nom, lieu, statut,
   compteurs, documents, plan de maintenance), `VehiculeProfile` porte les champs
   spécifiques automobile.
2. **Héritage multi-table Django** (`class Vehicule(Equipement)`) : Django gère la
   jointure automatiquement, mais impose une table par sous-classe, complique les
   requêtes cross-type (`Equipement.objects.all()` ne retourne pas les champs
   spécifiques), et rend un changement de "nature" d'un équipement plus lourd
   (suppression/recréation de la ligne fille).
3. **Champs directs sur `Equipement`** : ajout de tous les champs véhicule directement
   sur le modèle générique, avec `null=True` pour les équipements non-véhicule.

L'option 3 est écartée d'emblée : elle pollue le modèle générique pour tous les autres
types d'équipements (pédagogique, infrastructure, mécanique...) et rend le modèle
`Equipement` toujours plus large à mesure que d'autres spécialisations métier
apparaîtraient (dette de conception).

## Décision

Le projet adopte l'**option 1 : profil `VehiculeProfile` en relation `OneToOneField`
vers `Equipement`**, avec `Equipement.id` comme clé primaire du profil
(`primary_key=True`).

Conséquences directes sur le modèle de données :

- `Equipement.TYPE_CHOICES` reçoit une nouvelle valeur `'VEHICULE'`.
- La création d'un véhicule crée systématiquement les deux lignes (`Equipement` +
  `VehiculeProfile`) dans une seule transaction atomique (service dédié, cf. TUS-005).
- Toutes les entités réglementaires/métier automobile ultérieures (`CarteGrise`,
  `ControleTechnique`, `Pneumatique`, `PleinCarburant`, `ContratLLD/LOA`) sont rattachées
  à `VehiculeProfile`, jamais directement à `Equipement`.
- `Equipement` continue de porter tout ce qui est déjà générique et transversal :
  `lieu`, `StatutEquipement`, `Compteur`/`Declencher`, `Document`, `PlanMaintenance`.
- Le champ `type` de `Equipement` reste l'enum figé existant (pas de migration vers une
  table de types dynamique dans le cadre de cette ADR — hors périmètre, non bloquant
  pour la spécialisation flotte).

## Conséquences

**Positives**

- Aucune régression sur les équipements non-véhicule : `Equipement` n'est pas modifié
  en profondeur, seul un choix supplémentaire est ajouté à `TYPE_CHOICES`.
- Requêtes génériques (`Equipement.objects.filter(archive=False)`) restent valables
  pour tous les types, y compris les véhicules.
- `VehiculeProfile` peut être étendu librement (nouveaux champs automobile) sans
  jamais impacter le modèle `Equipement` ni les autres apps qui le consomment
  (`maintenance`, `stock`).
- Le pattern est réutilisable pour une future spécialisation métier (ex. un jour
  "Machine industrielle" avec ses propres champs) sans repenser l'architecture.

**Négatives / coûts**

- Une jointure supplémentaire (`select_related('vehiculeprofile')`) est nécessaire pour
  toute vue consolidée véhicule — à discipliner dans les serializers/services pour
  éviter le N+1 (cf. règle Clean Code, TUS-005).
- Deux objets à créer/supprimer de façon cohérente (transaction atomique obligatoire à
  la création ; la suppression en cascade est gérée nativement par Django via la FK
  1-1, donc sans risque d'orphelin).
- Un `Equipement` dont le type passe de `VEHICULE` à autre chose (cas rare, non prévu
  dans le périmètre métier actuel) laisserait un `VehiculeProfile` orphelin
  fonctionnellement ; non traité par cette ADR faute de besoin identifié — à réévaluer
  si ce cas se présente.
