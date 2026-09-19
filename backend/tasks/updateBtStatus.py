import logging

from django.utils import timezone

from maintenance.models import BonTravail

logger = logging.getLogger("tasks")


def update_bt_status():
    """
    Vérifie les bons de travails existants planifiés et les passe
    au statut 'En retard' si leur date prévue est dépassée.
    """

    bons_travail = BonTravail.objects.filter(
        date_prevue__lt=timezone.now(),
        date_debut__isnull=True,
        archive=False,
    ).exclude(statut__in=["EN_RETARD", "TERMINE", "CLOTURE"])

    updated_bts = 0
    for bt in bons_travail:
        bt.statut = "EN_RETARD"
        bt.save()
        updated_bts += 1

    if updated_bts > 0:
        logger.info(
            f"{updated_bts} bons de travail ont été mis à jour en statut 'EN_RETARD' le {timezone.now()}"
        )
