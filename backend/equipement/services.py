"""Couche service du domaine Equipement.

Concentre la logique metier historiquement portee par ``EquipementViewSet``
(creation/mise a jour d'un equipement avec ses compteurs et plans de
maintenance imbriques, archivage en cascade, calcul de KPI, ajout de
document) afin que le ViewSet DRF ne fasse plus que routage, serialisation
et traduction HTTP des erreurs (cf. ADR-001, TUS-003).

Les fonctions de ce module ne connaissent pas la couche HTTP : elles
recoivent des types Python simples (dict, fichiers Django ``UploadedFile``,
instances de modele) et retournent des instances de modele ou des dict
serialisables, jamais un objet ``rest_framework.response.Response``. Les cas
d'erreur metier sont signales par des exceptions dediees (voir plus bas),
charge au ViewSet appelant de les traduire en reponse HTTP appropriee.
"""

from __future__ import annotations

import datetime
import logging

from django.db import transaction
from django.utils import timezone

from donnees.models import Document, Fabricant, Fournisseur, Lieu
from maintenance.models import (
    BonTravail,
    DemandeIntervention,
    PlanMaintenance,
    PlanMaintenanceConsommable,
    PlanMaintenanceDocument,
)
from utilisateur.models import Utilisateur

from .models import (
    Compteur,
    Constituer,
    Declencher,
    DocumentEquipement,
    Equipement,
    FamilleEquipement,
    ModeleEquipement,
    StatutEquipement,
    VehiculeProfile,
)

VEHICULE_PROFILE_FIELDS = frozenset(
    {"vin", "immatriculation", "genre", "energie", "co2", "puissanceFiscale", "ptac"}
)

logger = logging.getLogger(__name__)


class EquipementServiceError(Exception):
    """Erreur metier de base du domaine Equipement.

    Attributes:
        message: Description humaine de l'erreur, destinee a etre relayee
            telle quelle dans le corps de la reponse HTTP par le ViewSet
            appelant.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UtilisateurCreateurIntrouvable(EquipementServiceError):
    """Levee quand aucun utilisateur createur ne peut etre resolu.

    Le ViewSet appelant doit traduire cette exception en reponse
    ``401 Unauthorized`` (comportement identique a celui du ViewSet avant
    factorisation, cf. TUS-003).
    """


class DocumentRequisManquant(EquipementServiceError):
    """Levee quand un fichier ou une metadonnee obligatoire de document manque.

    Le ViewSet appelant doit traduire cette exception en reponse
    ``400 Bad Request``.
    """


def date_to_ordinal_days(date_str: str | None) -> int:
    """Convertit une date ``YYYY-MM-DD`` en nombre de jours depuis 0001-01-01.

    Utilise pour stocker les compteurs de type ``Calendaire`` comme une
    valeur numerique ordinale (cf. ``Compteur.type``), afin de pouvoir les
    comparer avec le meme operateur que les compteurs numeriques.

    Args:
        date_str: Date au format ``YYYY-MM-DD``, ou ``None``/valeur invalide.

    Returns:
        Le nombre de jours ecoules depuis le 1er janvier de l'an 1
        (``datetime.date.toordinal()`` moins 1). Retourne ``0`` si
        ``date_str`` est ``None`` ou dans un format non reconnu.
    """
    try:
        date_value = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        base_date = datetime.datetime(1, 1, 1)
        delta = date_value - base_date
        return delta.days
    except (TypeError, ValueError):
        logger.debug("Conversion de date impossible pour %r, retour 0", date_str)
        return 0


def create_declencher_for_plan(
    compteur: Compteur, plan: PlanMaintenance, seuil_data: dict
) -> Declencher:
    """Cree le seuil de declenchement (``Declencher``) liant un compteur a un plan.

    Args:
        compteur: Compteur sur lequel porte le seuil.
        plan: Plan de maintenance declenche lorsque le seuil est atteint.
        seuil_data: Dict optionnellement fourni par le client, avec les cles
            ``estGlissant``, ``ecartInterventions``, ``derniereIntervention``
            et ``prochaineMaintenance``. Les dates sont attendues au format
            ``YYYY-MM-DD`` lorsque ``compteur.type == "Calendaire"``.

    Returns:
        Le ``Declencher`` cree.
    """
    est_glissant = seuil_data.get("estGlissant", False)
    ecart = float(seuil_data.get("ecartInterventions", 0))

    if compteur.type == "Calendaire":
        derniere = date_to_ordinal_days(seuil_data.get("derniereIntervention"))
        prochaine = date_to_ordinal_days(seuil_data.get("prochaineMaintenance"))
    else:
        derniere = float(seuil_data.get("derniereIntervention", 0))
        prochaine = derniere + ecart

    return Declencher.objects.create(
        compteur=compteur,
        planMaintenance=plan,
        derniereIntervention=derniere,
        prochaineMaintenance=prochaine,
        ecartInterventions=ecart,
        estGlissant=est_glissant,
    )


def _resoudre_utilisateur_createur(request_user, data: dict) -> Utilisateur:
    """Resout l'``Utilisateur`` createur a partir de l'utilisateur HTTP authentifie.

    Args:
        request_user: Objet ``request.user`` de Django (peut etre anonyme).
        data: Donnees de la requete de creation, utilisees en repli via la
            cle ``createurEquipement`` si l'utilisateur HTTP ne peut pas
            etre resolu en ``Utilisateur`` metier.

    Returns:
        L'``Utilisateur`` createur resolu.

    Raises:
        UtilisateurCreateurIntrouvable: Si aucun utilisateur ne peut etre
            resolu ni via la session HTTP, ni via le repli explicite.
    """
    utilisateur = None
    if request_user is not None and getattr(request_user, "is_authenticated", False):
        utilisateur = Utilisateur.objects.filter(nomUtilisateur=request_user.username).first()
        if not utilisateur and hasattr(request_user, "utilisateur"):
            utilisateur = request_user.utilisateur

    if not utilisateur and data.get("createurEquipement"):
        utilisateur = Utilisateur.objects.filter(id=data["createurEquipement"]).first()

    if not utilisateur:
        raise UtilisateurCreateurIntrouvable("Utilisateur non authentifie ou introuvable")

    return utilisateur


@transaction.atomic
def create_equipement(data: dict, files, request_user) -> Equipement:
    """Cree un equipement avec ses consommables, compteurs et plans de maintenance imbriques.

    Reproduit a l'identique le comportement historique de
    ``EquipementViewSet.create`` (cf. TUS-003) : creation de l'``Equipement``,
    de son ``StatutEquipement`` initial optionnel, des liaisons
    ``Constituer`` (consommables), des ``Compteur`` puis des
    ``PlanMaintenance``/``Declencher`` qui les referencent par index, avec
    leurs consommables et documents propres.

    Args:
        data: Donnees de la requete de creation (deja normalisees : listes a
            un element extraites, champs JSON deja parses par l'appelant).
        files: ``request.FILES`` — fichiers uploades pour les documents des
            plans de maintenance (cles ``pm_{index}_document_{doc_index}``).
        request_user: ``request.user`` Django, utilise pour resoudre le
            createur (cf. ``_resoudre_utilisateur_createur``).

    Returns:
        L'``Equipement`` cree, avec ses relations deja persistees.

    Raises:
        UtilisateurCreateurIntrouvable: Si aucun createur ne peut etre resolu.
        DocumentRequisManquant: Si un document de plan de maintenance
            reference dans ``data`` n'a pas de fichier correspondant dans
            ``files``, ou si son type est invalide.
    """
    utilisateur = _resoudre_utilisateur_createur(request_user, data)

    modele_id = data.get("modeleEquipement")
    modele = ModeleEquipement.objects.get(id=modele_id) if modele_id else None
    fabricant = Fabricant.objects.get(id=data["fabricant"])
    fournisseur = Fournisseur.objects.get(id=data["fournisseur"])
    famille = FamilleEquipement.objects.get(id=data["famille"])
    lieu = Lieu.objects.get(id=data["lieu"])

    equipement = Equipement.objects.create(
        reference=data["reference"],
        designation=data["designation"],
        dateMiseEnService=data.get("dateMiseEnService"),
        prixAchat=data.get("prixAchat", 0),
        createurEquipement=utilisateur,
        lieu=lieu,
        modele=modele,
        famille=famille,
        fournisseur=fournisseur,
        fabricant=fabricant,
        numSerie=data.get("numSerie", ""),
        type=data.get("type") or None,
        lienImage=data.get("lienImageEquipement"),
    )

    statut = data.get("statut")
    if statut:
        StatutEquipement.objects.create(
            equipement=equipement,
            statut=statut,
            dateChangement=timezone.now(),
        )

    for consommable_id in data.get("consommables", []):
        Constituer.objects.create(equipement=equipement, consommable_id=consommable_id)

    compteurs_crees = []
    for compteur_data in data.get("compteurs", []):
        compteur = Compteur.objects.create(
            equipement=equipement,
            nomCompteur=compteur_data["nom"],
            valeurCourante=compteur_data.get("valeurCourante", 0),
            unite=compteur_data.get("unite", "heures"),
            estPrincipal=compteur_data.get("estPrincipal", False),
            type=compteur_data.get("type", "Numérique"),
        )
        compteurs_crees.append(compteur)

    for pm_index, pm_data in enumerate(data.get("plansMaintenance", [])):
        compteur_index = pm_data.get("compteurIndex")
        if compteur_index is None or compteur_index >= len(compteurs_crees):
            continue

        compteur = compteurs_crees[compteur_index]

        plan = PlanMaintenance.objects.create(
            equipement=equipement,
            nom=pm_data.get("nom", f"Plan {compteur.nomCompteur}"),
            type_plan_maintenance_id=pm_data.get("type_id"),
            commentaire=pm_data.get("description", ""),
            necessiteHabilitationElectrique=pm_data.get("necessiteHabilitationElectrique", False),
            necessitePermisFeu=pm_data.get("necessitePermisFeu", False),
        )

        create_declencher_for_plan(compteur, plan, pm_data.get("seuil", {}))

        for consommable_data in pm_data.get("consommables", []):
            if isinstance(consommable_data, dict):
                consommable_id = consommable_data.get("consommable_id")
                quantite = consommable_data.get("quantite_necessaire", 1)
            else:
                consommable_id = consommable_data
                quantite = 1

            if consommable_id:
                PlanMaintenanceConsommable.objects.create(
                    plan_maintenance=plan,
                    consommable_id=consommable_id,
                    quantite_necessaire=quantite,
                )

        for doc_index, doc_data in enumerate(pm_data.get("documents", []) or []):
            file_key = f"pm_{pm_index}_document_{doc_index}"
            uploaded_file = files.get(file_key)
            if not uploaded_file:
                raise DocumentRequisManquant(
                    f"Fichier manquant pour le document #{doc_index + 1} (clé attendue: {file_key})"
                )

            doc_data = doc_data or {}
            nom_document = doc_data.get("titre") or uploaded_file.name

            try:
                type_document_id = int(doc_data.get("type"))
            except (TypeError, ValueError) as exc:
                raise DocumentRequisManquant(
                    f"Type de document invalide pour le document '{nom_document}'"
                ) from exc

            document = Document.objects.create(
                nomDocument=nom_document,
                typeDocument_id=type_document_id,
                cheminAcces=uploaded_file,
            )
            PlanMaintenanceDocument.objects.create(plan_maintenance=plan, document=document)

    return equipement


@transaction.atomic
def update_equipement(equipement: Equipement, changes: dict, files) -> Equipement:
    """Applique un diff de modifications a un equipement existant.

    Reproduit a l'identique le comportement historique de
    ``EquipementViewSet.update`` (cf. TUS-003) : mise a jour des champs
    simples, changement de statut (avec creation d'un ``StatutEquipement``
    si la valeur differe), ajout/retrait de consommables, remplacement de
    l'image.

    Args:
        equipement: Instance a mettre a jour.
        changes: Dict ``{champ: {"nouvelle": valeur, ...}}`` decrivant les
            modifications a appliquer, plus une cle optionnelle
            ``consommables`` au format ``{"ajoutes": [...], "retires": [...]}``.
        files: ``request.FILES`` — utilise pour la cle ``lienImageEquipement``.

    Returns:
        L'``Equipement`` mis a jour (deja sauvegarde si des changements ont
        ete appliques).
    """
    simple_fields = [
        "numSerie",
        "reference",
        "designation",
        "dateMiseEnService",
        "prixAchat",
        "modeleEquipement",
        "fournisseur",
        "fabricant",
        "famille",
        "lieu",
        "statut",
        "type",
    ]

    has_updates = False

    for field in simple_fields:
        if field not in changes:
            continue

        nouveau = changes[field].get("nouvelle")

        if field == "lieu" and isinstance(nouveau, dict):
            nouveau = nouveau.get("id")

        if field == "lieu" and nouveau:
            lieu = Lieu.objects.filter(id=nouveau).first()
            if lieu:
                equipement.lieu = lieu
                has_updates = True

        elif field == "statut" and nouveau:
            dernier_statut = equipement.statuts.order_by("-dateChangement").first()
            ancien_statut = dernier_statut.statut if dernier_statut else None
            if ancien_statut != nouveau:
                StatutEquipement.objects.create(
                    equipement=equipement,
                    statut=nouveau,
                    dateChangement=timezone.now(),
                )

        elif field == "modeleEquipement" and nouveau:
            modele = ModeleEquipement.objects.filter(id=nouveau).first()
            if modele:
                equipement.modele = modele
                has_updates = True

        elif field == "fabricant" and nouveau:
            fabricant = Fabricant.objects.filter(id=nouveau).first()
            if fabricant:
                equipement.fabricant = fabricant
                has_updates = True

        elif field == "fournisseur" and nouveau:
            fournisseur = Fournisseur.objects.filter(id=nouveau).first()
            if fournisseur:
                equipement.fournisseur = fournisseur
                has_updates = True

        elif field == "famille" and nouveau:
            famille = FamilleEquipement.objects.filter(id=nouveau).first()
            if famille:
                equipement.famille = famille
                has_updates = True

        elif field in (
            "numSerie",
            "reference",
            "designation",
            "dateMiseEnService",
            "prixAchat",
            "type",
        ):
            ancien_val = getattr(equipement, field, None)
            if str(ancien_val) != str(nouveau):
                setattr(equipement, field, nouveau)
                has_updates = True

    if "consommables" in changes:
        modification = changes["consommables"]
        ajoutes = modification.get("ajoutes", [])
        retires = modification.get("retires", [])

        if retires:
            equipement.constituer_set.filter(consommable_id__in=retires).delete()
        for consommable_id in ajoutes:
            Constituer.objects.create(equipement=equipement, consommable_id=consommable_id)

    if files and "lienImageEquipement" in files:
        uploaded_file = files["lienImageEquipement"]
        if equipement.lienImage:
            try:
                equipement.lienImage.delete(save=False)
            except OSError:
                logger.warning(
                    "Suppression de l'ancienne image impossible pour equipement %s", equipement.pk
                )
        equipement.lienImage = uploaded_file
        has_updates = True

    if has_updates:
        equipement.save()

    return equipement


@transaction.atomic
def archive_equipement_cascade(equipement: Equipement) -> None:
    """Archive toutes les DI et cloture tous les BT rattaches a un equipement.

    Appele lorsque ``Equipement.archive`` passe a ``True`` (cf.
    ``ArchivableViewSetMixin.set_archive``) : les demandes d'intervention
    associees sont archivees, et les bons de travail lies (via ces DI)
    passent au statut ``TERMINE`` (sauf s'ils sont deja ``CLOTURE``) et sont
    egalement archives.

    Args:
        equipement: Equipement dont l'archivage vient d'etre confirme.
    """
    dis_a_archiver = DemandeIntervention.objects.filter(equipement=equipement)
    for di in dis_a_archiver:
        di.archive = True
        di.save(update_fields=["archive"])

    bons_a_terminer = BonTravail.objects.filter(demande_intervention__equipement=equipement)
    for bt in bons_a_terminer:
        bt.statut = "TERMINE" if bt.statut != "CLOTURE" else bt.statut
        bt.date_fin = timezone.now()
        bt.archive = True
        bt.save(update_fields=["statut", "date_fin", "archive"])


def get_historique_statuts(equipement: Equipement) -> list[dict]:
    """Retourne l'historique chronologique des statuts d'un equipement.

    Args:
        equipement: Equipement dont on veut l'historique.

    Returns:
        Liste de dict ``{"statut": str, "dateChangement": datetime}``,
        triee par date de changement croissante. Le frontend en deduit les
        plages (du statut N au statut N+1).
    """
    return list(
        StatutEquipement.objects.filter(equipement=equipement)
        .order_by("dateChangement")
        .values("statut", "dateChangement")
    )


def compute_equipement_kpi(equipement: Equipement) -> dict:
    """Calcule les indicateurs de maintenance corrective d'un equipement.

    Args:
        equipement: Equipement dont on calcule les KPI.

    Returns:
        Dict avec les cles :

        - ``nombre_pannes``: nombre de DI confirmees (ACCEPTEE ou
          TRANSFORMEE), non archivees.
        - ``mtbf_heures``: temps moyen entre deux pannes, en heures
          (``None`` si aucune panne).
        - ``mttr_heures``: temps moyen de reparation, en heures, calcule sur
          les BT correctifs termines/clotures avec ``date_debut`` et
          ``date_fin`` renseignees (``None`` si aucun BT eligible).
    """
    today = timezone.now()

    pannes = DemandeIntervention.objects.filter(
        equipement=equipement,
        statut__in=["ACCEPTEE", "TRANSFORMEE"],
        archive=False,
    ).order_by("date_creation")

    nombre_pannes = pannes.count()

    mtbf_heures = None
    if nombre_pannes > 0:
        date_debut_observation = equipement.dateMiseEnService or pannes.first().date_creation
        duree_totale_heures = (today - date_debut_observation).total_seconds() / 3600
        if duree_totale_heures > 0:
            mtbf_heures = round(duree_totale_heures / nombre_pannes, 1)

    mttr_heures = None
    bts_termines = BonTravail.objects.filter(
        demande_intervention__equipement=equipement,
        type="CORRECTIF",
        statut__in=["TERMINE", "CLOTURE"],
        date_debut__isnull=False,
        date_fin__isnull=False,
        archive=False,
    )

    if bts_termines.exists():
        durees = [
            (bt.date_fin - bt.date_debut).total_seconds() / 3600
            for bt in bts_termines
            if bt.date_fin >= bt.date_debut
        ]
        if durees:
            mttr_heures = round(sum(durees) / len(durees), 1)

    return {
        "nombre_pannes": nombre_pannes,
        "mtbf_heures": mtbf_heures,
        "mttr_heures": mttr_heures,
    }


@transaction.atomic
def add_document_to_equipement(
    equipement: Equipement, uploaded_file, nom: str, type_document_id
) -> Document:
    """Cree un ``Document`` et le rattache a un equipement.

    Args:
        equipement: Equipement auquel rattacher le document.
        uploaded_file: Fichier uploade (``request.FILES.get('file')``).
        nom: Nom souhaite pour le document ; si vide, le nom du fichier
            uploade est utilise.
        type_document_id: Identifiant du ``TypeDocument``.

    Returns:
        Le ``Document`` cree.

    Raises:
        DocumentRequisManquant: Si ``uploaded_file`` ou ``type_document_id``
            est manquant.
    """
    if not uploaded_file:
        raise DocumentRequisManquant("Fichier requis")
    if not type_document_id:
        raise DocumentRequisManquant("Type de document requis")

    document = Document.objects.create(
        nomDocument=(nom or "").strip() or uploaded_file.name,
        typeDocument_id=type_document_id,
        cheminAcces=uploaded_file,
    )
    DocumentEquipement.objects.create(equipement=equipement, document=document)
    return document


@transaction.atomic
def create_vehicule(data: dict, files, request_user) -> Equipement:
    """Cree un vehicule : un Equipement (type VEHICULE) et son VehiculeProfile.

    Reutilise integralement ``create_equipement`` pour la partie generique
    (lieu, fabricant, fournisseur, famille, compteurs, plans de maintenance),
    puis cree le ``VehiculeProfile`` associe dans la meme transaction
    (cf. ADR-001, TUS-005).

    Args:
        data: Donnees de la requete, melangeant les champs Equipement
            generiques et les champs specifiques VehiculeProfile (``vin``,
            ``immatriculation``, ``genre``, ``energie``, ``co2``,
            ``puissanceFiscale``, ``ptac``).
        files: ``request.FILES``, transmis tel quel a ``create_equipement``.
        request_user: ``request.user`` Django, transmis tel quel a
            ``create_equipement``.

    Returns:
        L'``Equipement`` cree, avec son ``VehiculeProfile`` deja persiste
        (accessible via ``equipement.vehicule_profile``).

    Raises:
        UtilisateurCreateurIntrouvable: Cf. ``create_equipement``.
        DocumentRequisManquant: Cf. ``create_equipement``.
        django.core.exceptions.ValidationError: Si les champs du profil
            véhicule (VIN, immatriculation...) ne respectent pas les
            validateurs du modèle ``VehiculeProfile``.
    """
    vehicule_data = {k: v for k, v in data.items() if k in VEHICULE_PROFILE_FIELDS}
    equipement_data = {k: v for k, v in data.items() if k not in VEHICULE_PROFILE_FIELDS}
    equipement_data["type"] = "VEHICULE"

    equipement = create_equipement(equipement_data, files, request_user)

    profile = VehiculeProfile(equipement=equipement, **vehicule_data)
    profile.full_clean(exclude=["equipement"])
    profile.save()

    return equipement


@transaction.atomic
def update_vehicule(equipement: Equipement, changes: dict, files) -> Equipement:
    """Applique un diff de modifications a un vehicule (Equipement + VehiculeProfile).

    Repartit le diff ``changes`` entre les champs generiques (delegues a
    ``update_equipement``) et les champs du profil vehicule, mis a jour
    directement ici selon le meme format ``{"nouvelle": valeur}``.

    Args:
        equipement: Equipement de type VEHICULE a mettre a jour, avec son
            ``vehicule_profile`` deja existant.
        changes: Dict ``{champ: {"nouvelle": valeur}}``, champs Equipement et
            VehiculeProfile melanges.
        files: ``request.FILES``, transmis a ``update_equipement``.

    Returns:
        L'``Equipement`` mis a jour.
    """
    vehicule_changes = {k: v for k, v in changes.items() if k in VEHICULE_PROFILE_FIELDS}
    equipement_changes = {k: v for k, v in changes.items() if k not in VEHICULE_PROFILE_FIELDS}

    equipement = update_equipement(equipement, equipement_changes, files)

    if vehicule_changes:
        profile = equipement.vehicule_profile
        has_updates = False
        for field, modification in vehicule_changes.items():
            nouveau = modification.get("nouvelle")
            if nouveau is not None and str(getattr(profile, field)) != str(nouveau):
                setattr(profile, field, nouveau)
                has_updates = True

        if has_updates:
            profile.full_clean(exclude=["equipement"])
            profile.save()

    return equipement
