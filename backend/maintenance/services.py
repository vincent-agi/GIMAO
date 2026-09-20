"""Couche service du domaine Maintenance — signalement d'avaries véhicule.

Concentre la logique de création transactionnelle d'une
``DemandeIntervention`` accompagnée de son profil ``IncidentVehicule``
(et, pour un accident de la route, de son ``Sinistre``), afin que
``DemandeInterventionViewSet`` ne fasse que router, valider le payload et
traduire les erreurs métier en réponses HTTP (même principe que
``equipement.services``, cf. ADR-001, TUS-003).

Le workflow générique de la DI (statut initial ``EN_ATTENTE``, horodatage)
n'est pas modifié : ce module ajoute uniquement l'étape d'enrichissement
véhicule par-dessus.
"""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from .models import DemandeIntervention, IncidentVehicule, Sinistre


class MaintenanceServiceError(Exception):
    """Erreur métier de base du domaine Maintenance.

    Attributes:
        message: Description humaine de l'erreur, destinée à être relayée
            telle quelle dans le corps de la réponse HTTP par le ViewSet
            appelant.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@transaction.atomic
def creer_demande_intervention_incident(
    di_data: dict, incident_data: dict, sinistre_data: dict | None = None
) -> DemandeIntervention:
    """Crée une DemandeIntervention et son profil IncidentVehicule (et Sinistre le cas échéant).

    Reproduit le comportement de création générique d'une
    ``DemandeIntervention`` (statut initial ``EN_ATTENTE``, horodatage,
    cf. ``DemandeInterventionSerializer.create``), puis crée le profil
    ``IncidentVehicule`` associé et, si ``sinistre_data`` est fourni, le
    ``Sinistre`` associé à cet incident (US-020, US-021).

    Args:
        di_data: Données validées de la DI (``nom``, ``commentaire``,
            ``statut_suppose``, ``utilisateur``, ``equipement`` — objets
            résolus, pas des identifiants bruts).
        incident_data: Données validées du profil véhicule (``type_avarie``,
            ``gravite`` optionnel, ``immobilisation`` optionnel).
        sinistre_data: Données validées du sinistre si l'incident est un
            accident de la route (``date_accident``, ``lieu_accident``,
            et champs optionnels). ``None`` si non applicable.

    Returns:
        La ``DemandeIntervention`` créée, avec son ``incident_vehicule``
        (et son ``sinistre`` le cas échéant) déjà persistés.

    Raises:
        django.core.exceptions.ValidationError: Si les données de
            l'incident ou du sinistre ne respectent pas les règles de
            validation des modèles (ex. sinistre fourni pour un incident
            qui n'est pas de type accident de la route).
    """
    demande = DemandeIntervention.objects.create(
        nom=di_data["nom"],
        commentaire=di_data.get("commentaire"),
        statut="EN_ATTENTE",
        statut_suppose=di_data.get("statut_suppose", "EN_FONCTIONNEMENT"),
        date_creation=timezone.now(),
        date_changementStatut=timezone.now(),
        utilisateur=di_data["utilisateur"],
        equipement=di_data["equipement"],
    )

    incident = IncidentVehicule(
        demande_intervention=demande,
        type_avarie=incident_data["type_avarie"],
        gravite=incident_data.get("gravite", "MINEURE"),
        immobilisation=incident_data.get("immobilisation", False),
    )
    incident.full_clean()
    incident.save()

    if sinistre_data:
        sinistre = Sinistre(incident_vehicule=incident, **sinistre_data)
        sinistre.full_clean()
        sinistre.save()

    return demande
