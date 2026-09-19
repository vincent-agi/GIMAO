"""
Import en masse d'équipements (et de leurs données de référence) depuis un
classeur Excel généré via le modèle fourni par `template.py`.

Principe : le classeur contient un onglet par type de donnée (Lieux,
Fabricants, Fournisseurs, Familles, Modèles, Équipements). Les onglets sont
traités dans cet ordre car chaque niveau peut dépendre du précédent (un
équipement a besoin d'un lieu, d'un fabricant... qui doivent exister avant).

Les données de référence sont associées par nom (insensible à la casse et
aux espaces superflus) ; si le nom n'existe pas encore, il est créé
automatiquement (comportement "get or create"), ce qui évite d'obliger
l'utilisateur à créer manuellement chaque fabricant/lieu avant l'import.

Chaque ligne est traitée indépendamment (une ligne en erreur n'annule pas
les autres lignes du fichier) grâce à une savepoint de transaction par ligne.
"""

import datetime

from django.db import transaction
from django.utils import timezone

from donnees.models import Adresse, Fabricant, Fournisseur, Lieu
from equipement.models import Equipement, FamilleEquipement, ModeleEquipement, StatutEquipement
from utilisateur.models import Utilisateur

SHEET_LIEUX = "Lieux"
SHEET_FABRICANTS = "Fabricants"
SHEET_FOURNISSEURS = "Fournisseurs"
SHEET_FAMILLES = "Familles"
SHEET_MODELES = "Modeles"
SHEET_EQUIPEMENTS = "Equipements"

TYPE_LIEU_PAR_DEFAUT = "Autre"

# Marqueur utilisé dans la ligne d'exemple du modèle (voir template.py) :
# toute ligne contenant ce texte est ignorée à l'import, qu'elle ait été
# supprimée par l'utilisateur ou non.
EXEMPLE_MARQUEUR = "(EXEMPLE)"


def _normalize(value):
    """Nettoie une valeur de cellule : espaces superflus retirés, None si vide."""
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _parse_date(value):
    """Convertit une valeur de cellule (date Excel ou texte JJ/MM/AAAA) en
    datetime "timezone aware" (le champ dateMiseEnService est un DateTimeField)."""
    parsed_date = None
    if isinstance(value, datetime.datetime):
        parsed_date = value.date()
    elif isinstance(value, datetime.date):
        parsed_date = value
    elif value not in (None, ""):
        text = str(value).strip()
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                parsed_date = datetime.datetime.strptime(text, fmt).date()
                break
            except ValueError:
                continue

    if parsed_date is None:
        return None
    return timezone.make_aware(datetime.datetime.combine(parsed_date, datetime.time.min))


def _parse_decimal(value):
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def _parse_bool(value):
    """Interprete Oui/Non (ou true/false/1/0) ; None/vide => False (comportement
    par défaut du formulaire de création manuelle)."""
    if value is None:
        return False
    return str(value).strip().lower() in ("oui", "true", "1", "yes")


class ImportResult:
    """Accumule le résultat de l'import (compteurs + erreurs) pour un onglet."""

    def __init__(self, sheet_name):
        self.sheet_name = sheet_name
        self.created = 0
        self.existing = 0
        self.errors = []

    def add_error(self, row_number, message):
        self.errors.append({"ligne": row_number, "message": message})

    def as_dict(self):
        return {
            "onglet": self.sheet_name,
            "crees": self.created,
            "existants_reutilises": self.existing,
            "erreurs": self.errors,
        }


class EquipementImporter:
    """
    Traite un classeur Excel (openpyxl Workbook) et crée les enregistrements
    correspondants en base. Retourne la liste des ImportResult, un par onglet
    traité.
    """

    def __init__(self, workbook, utilisateur=None):
        self.workbook = workbook
        self.utilisateur = utilisateur or Utilisateur.objects.first()
        # Caches nom -> instance, pour éviter de refaire une requête par ligne
        # et pour retrouver les objets créés/mis à jour au sein du même import.
        self._lieux = {}
        self._fabricants = {}
        self._fournisseurs = {}
        self._familles = {}
        self._modeles = {}

    def run(self):
        results = []

        if SHEET_LIEUX in self.workbook.sheetnames:
            results.append(self._import_lieux())
        if SHEET_FABRICANTS in self.workbook.sheetnames:
            results.append(self._import_fabricants())
        if SHEET_FOURNISSEURS in self.workbook.sheetnames:
            results.append(self._import_fournisseurs())
        if SHEET_FAMILLES in self.workbook.sheetnames:
            results.append(self._import_familles())
        if SHEET_MODELES in self.workbook.sheetnames:
            results.append(self._import_modeles())
        if SHEET_EQUIPEMENTS in self.workbook.sheetnames:
            results.append(self._import_equipements())

        return results

    # ------------------------------------------------------------------
    # Utilitaires communs
    # ------------------------------------------------------------------

    def _rows(self, sheet_name):
        """Itère les lignes de données (hors en-tête) d'un onglet, avec leur numéro Excel."""
        sheet = self.workbook[sheet_name]
        for row_number, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            if all(cell is None or str(cell).strip() == "" for cell in row):
                continue  # ligne vide, on l'ignore silencieusement
            if any(EXEMPLE_MARQUEUR in str(cell) for cell in row if cell is not None):
                continue  # ligne d'exemple du modèle, on l'ignore silencieusement
            yield row_number, row

    def _get_or_create_lieu(self, nom, result=None):
        if not nom:
            return None
        key = nom.lower()
        if key in self._lieux:
            return self._lieux[key]
        lieu = Lieu.objects.filter(nomLieu__iexact=nom).first()
        if not lieu:
            lieu = Lieu.objects.create(nomLieu=nom, typeLieu=TYPE_LIEU_PAR_DEFAUT)
        self._lieux[key] = lieu
        return lieu

    def _get_or_create_fabricant(self, nom):
        if not nom:
            return None
        key = nom.lower()
        if key in self._fabricants:
            return self._fabricants[key]
        fabricant = Fabricant.objects.filter(nom__iexact=nom).first()
        if not fabricant:
            fabricant = Fabricant.objects.create(nom=nom)
        self._fabricants[key] = fabricant
        return fabricant

    def _get_or_create_fournisseur(self, nom):
        if not nom:
            return None
        key = nom.lower()
        if key in self._fournisseurs:
            return self._fournisseurs[key]
        fournisseur = Fournisseur.objects.filter(nom__iexact=nom).first()
        if not fournisseur:
            fournisseur = Fournisseur.objects.create(nom=nom)
        self._fournisseurs[key] = fournisseur
        return fournisseur

    def _get_or_create_famille(self, nom):
        if not nom:
            return None
        key = nom.lower()
        if key in self._familles:
            return self._familles[key]
        famille = FamilleEquipement.objects.filter(nom__iexact=nom).first()
        if not famille:
            famille = FamilleEquipement.objects.create(nom=nom)
        self._familles[key] = famille
        return famille

    def _get_or_create_modele(self, nom, fabricant):
        if not nom:
            return None
        key = (nom.lower(), fabricant.id if fabricant else None)
        if key in self._modeles:
            return self._modeles[key]
        modele = ModeleEquipement.objects.filter(nom__iexact=nom).first()
        if not modele and fabricant:
            modele = ModeleEquipement.objects.create(nom=nom, fabricant=fabricant)
        self._modeles[key] = modele
        return modele

    # ------------------------------------------------------------------
    # Import par onglet
    # ------------------------------------------------------------------
    # Colonnes attendues : Nom | Type de lieu | Lieu parent | Lien du plan (tous optionnels sauf Nom)

    def _import_lieux(self):
        result = ImportResult(SHEET_LIEUX)
        for row_number, row in self._rows(SHEET_LIEUX):
            nom = _normalize(row[0] if len(row) > 0 else None)
            type_lieu = _normalize(row[1] if len(row) > 1 else None) or TYPE_LIEU_PAR_DEFAUT
            parent_nom = _normalize(row[2] if len(row) > 2 else None)
            lien_plan = _normalize(row[3] if len(row) > 3 else None)

            if not nom:
                result.add_error(row_number, "Le nom du lieu est obligatoire.")
                continue

            try:
                with transaction.atomic():
                    existing = Lieu.objects.filter(nomLieu__iexact=nom).first()
                    if existing:
                        self._lieux[nom.lower()] = existing
                        result.existing += 1
                        continue

                    parent = self._get_or_create_lieu(parent_nom) if parent_nom else None
                    lieu = Lieu.objects.create(
                        nomLieu=nom, typeLieu=type_lieu, lieuParent=parent, lienPlan=lien_plan
                    )
                    self._lieux[nom.lower()] = lieu
                    result.created += 1
            except Exception as exc:
                result.add_error(row_number, str(exc))

        return result

    # Colonnes attendues : Nom | Email (optionnel) | Telephone (optionnel)

    # Colonnes attendues :
    # Nom | Email | Telephone | Service apres-vente (Oui/Non)
    # | N adresse | Rue | Ville | Code postal | Pays | Complement adresse

    def _import_fabricants(self):
        return self._import_contact_sheet(SHEET_FABRICANTS, Fabricant, self._fabricants)

    def _import_fournisseurs(self):
        return self._import_contact_sheet(SHEET_FOURNISSEURS, Fournisseur, self._fournisseurs)

    def _build_adresse_si_renseignee(self, row):
        """Construit une Adresse à partir des colonnes 4 à 9 (N°, Rue, Ville, CP,
        Pays, Complément), seulement si au moins un champ est rempli."""
        numero = _normalize(row[4] if len(row) > 4 else None)
        rue = _normalize(row[5] if len(row) > 5 else None)
        ville = _normalize(row[6] if len(row) > 6 else None)
        code_postal = _normalize(row[7] if len(row) > 7 else None)
        pays = _normalize(row[8] if len(row) > 8 else None)
        complement = _normalize(row[9] if len(row) > 9 else None)

        if not any([numero, rue, ville, code_postal, pays, complement]):
            return None

        return Adresse.objects.create(
            numero=numero or "",
            rue=rue or "",
            ville=ville or "",
            code_postal=code_postal or "",
            pays=pays or "",
            complement=complement,
        )

    def _import_contact_sheet(self, sheet_name, model, cache):
        """Import générique pour Fabricants/Fournisseurs (mêmes colonnes)."""
        result = ImportResult(sheet_name)
        for row_number, row in self._rows(sheet_name):
            nom = _normalize(row[0] if len(row) > 0 else None)
            if not nom:
                result.add_error(row_number, "Le nom est obligatoire.")
                continue

            try:
                with transaction.atomic():
                    existing = model.objects.filter(nom__iexact=nom).first()
                    if existing:
                        cache[nom.lower()] = existing
                        result.existing += 1
                        continue

                    email = _normalize(row[1] if len(row) > 1 else None)
                    telephone = _normalize(row[2] if len(row) > 2 else None)
                    service_apres_vente = _parse_bool(row[3] if len(row) > 3 else None)
                    adresse = self._build_adresse_si_renseignee(row)

                    obj = model.objects.create(
                        nom=nom,
                        email=email,
                        numTelephone=telephone,
                        serviceApresVente=service_apres_vente,
                        adresse=adresse,
                    )
                    cache[nom.lower()] = obj
                    result.created += 1
            except Exception as exc:
                result.add_error(row_number, str(exc))

        return result

    # Colonnes attendues : Nom | Famille parente (optionnelle)

    def _import_familles(self):
        result = ImportResult(SHEET_FAMILLES)
        for row_number, row in self._rows(SHEET_FAMILLES):
            nom = _normalize(row[0] if len(row) > 0 else None)
            parent_nom = _normalize(row[1] if len(row) > 1 else None)

            if not nom:
                result.add_error(row_number, "Le nom de la famille est obligatoire.")
                continue

            try:
                with transaction.atomic():
                    existing = FamilleEquipement.objects.filter(nom__iexact=nom).first()
                    if existing:
                        self._familles[nom.lower()] = existing
                        result.existing += 1
                        continue

                    parent = self._get_or_create_famille(parent_nom) if parent_nom else None
                    famille = FamilleEquipement.objects.create(nom=nom, familleParente=parent)
                    self._familles[nom.lower()] = famille
                    result.created += 1
            except Exception as exc:
                result.add_error(row_number, str(exc))

        return result

    # Colonnes attendues : Nom | Fabricant

    def _import_modeles(self):
        result = ImportResult(SHEET_MODELES)
        for row_number, row in self._rows(SHEET_MODELES):
            nom = _normalize(row[0] if len(row) > 0 else None)
            fabricant_nom = _normalize(row[1] if len(row) > 1 else None)

            if not nom:
                result.add_error(row_number, "Le nom du modèle est obligatoire.")
                continue
            if not fabricant_nom:
                result.add_error(row_number, "Le fabricant est obligatoire pour créer un modèle.")
                continue

            try:
                with transaction.atomic():
                    existing = ModeleEquipement.objects.filter(nom__iexact=nom).first()
                    if existing:
                        self._modeles[(nom.lower(), existing.fabricant_id)] = existing
                        result.existing += 1
                        continue

                    fabricant = self._get_or_create_fabricant(fabricant_nom)
                    modele = ModeleEquipement.objects.create(nom=nom, fabricant=fabricant)
                    self._modeles[(nom.lower(), fabricant.id)] = modele
                    result.created += 1
            except Exception as exc:
                result.add_error(row_number, str(exc))

        return result

    # Colonnes attendues :
    # Code GMAO | Designation | Type | Statut | Lieu | Fabricant | Fournisseur
    # | Famille | Modele | Date de mise en service (JJ/MM/AAAA) | Prix d'achat | N de serie
    #
    # Code GMAO et Statut sont obligatoires ici, à l'image du formulaire de
    # création d'un équipement (CreateEquipment.vue impose déjà ces deux
    # champs). Le Code GMAO sert aussi de clé pour éviter les doublons si le
    # même fichier est importé plusieurs fois par erreur.

    def _import_equipements(self):
        result = ImportResult(SHEET_EQUIPEMENTS)
        equipement_types = {choice[0] for choice in Equipement.TYPE_CHOICES}
        statuts_valides = {choice[0] for choice in StatutEquipement.STATUTS_CHOICES}

        for row_number, row in self._rows(SHEET_EQUIPEMENTS):

            def cell(i, row=row):
                return row[i] if len(row) > i else None

            reference = _normalize(cell(0))
            designation = _normalize(cell(1))
            type_eq = _normalize(cell(2))
            statut_eq = _normalize(cell(3))
            lieu_nom = _normalize(cell(4))
            fabricant_nom = _normalize(cell(5))
            fournisseur_nom = _normalize(cell(6))
            famille_nom = _normalize(cell(7))
            modele_nom = _normalize(cell(8))
            date_mise_en_service = _parse_date(cell(9))
            prix_achat = _parse_decimal(cell(10))
            num_serie = _normalize(cell(11))

            if not reference:
                result.add_error(row_number, "Le Code GMAO est obligatoire.")
                continue
            if not designation:
                result.add_error(row_number, "La désignation est obligatoire.")
                continue
            if not statut_eq:
                result.add_error(row_number, "Le statut est obligatoire.")
                continue
            if statut_eq.upper() not in statuts_valides:
                result.add_error(
                    row_number,
                    f"Statut inconnu : '{statut_eq}'. Valeurs possibles : "
                    f"{', '.join(sorted(statuts_valides))}.",
                )
                continue
            if not lieu_nom:
                result.add_error(row_number, "Le lieu est obligatoire.")
                continue
            if type_eq and type_eq.upper() not in equipement_types:
                result.add_error(
                    row_number,
                    f"Type d'équipement inconnu : '{type_eq}'. Valeurs possibles : "
                    f"{', '.join(sorted(equipement_types))}.",
                )
                continue

            if Equipement.objects.filter(reference__iexact=reference).exists():
                result.existing += 1
                continue

            try:
                with transaction.atomic():
                    lieu = self._get_or_create_lieu(lieu_nom)
                    fabricant = (
                        self._get_or_create_fabricant(fabricant_nom) if fabricant_nom else None
                    )
                    fournisseur = (
                        self._get_or_create_fournisseur(fournisseur_nom)
                        if fournisseur_nom
                        else None
                    )
                    famille = self._get_or_create_famille(famille_nom) if famille_nom else None
                    modele = (
                        self._get_or_create_modele(modele_nom, fabricant) if modele_nom else None
                    )

                    equipement = Equipement.objects.create(
                        reference=reference,
                        designation=designation,
                        type=type_eq.upper() if type_eq else None,
                        dateMiseEnService=date_mise_en_service,
                        prixAchat=prix_achat,
                        numSerie=num_serie or "",
                        createurEquipement=self.utilisateur,
                        lieu=lieu,
                        fabricant=fabricant,
                        fournisseur=fournisseur,
                        famille=famille,
                        modele=modele,
                    )
                    StatutEquipement.objects.create(equipement=equipement, statut=statut_eq.upper())
                    result.created += 1
            except Exception as exc:
                result.add_error(row_number, str(exc))

        return result
