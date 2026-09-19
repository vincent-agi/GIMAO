from datetime import timedelta

import pytest
from django.utils import timezone

from tasks.updateBtStatus import update_bt_status
from tests.factories import BonTravailFactory


@pytest.mark.django_db
def test_should_mark_bt_as_en_retard_when_date_prevue_is_past():
    """
    Un BT EN_ATTENTE dont la date prévue est dépassée et non commencé
    doit passer au statut EN_RETARD.
    """
    # GIVEN
    bt = BonTravailFactory(
        statut="EN_ATTENTE",
        date_prevue=timezone.now() - timedelta(days=1),
        date_debut=None,
    )

    # WHEN
    update_bt_status()

    # THEN
    bt.refresh_from_db()
    assert bt.statut == "EN_RETARD"


@pytest.mark.django_db
def test_should_not_alter_bt_already_in_terminal_status():
    """
    Un BT déjà TERMINE ou CLOTURE ne doit pas être modifié,
    même si sa date prévue est dépassée.
    """
    # GIVEN
    bt_termine = BonTravailFactory(
        statut="TERMINE",
        date_prevue=timezone.now() - timedelta(days=2),
        date_debut=None,
    )
    bt_cloture = BonTravailFactory(
        statut="CLOTURE",
        date_prevue=timezone.now() - timedelta(days=2),
        date_debut=None,
    )

    # WHEN
    update_bt_status()

    # THEN
    bt_termine.refresh_from_db()
    bt_cloture.refresh_from_db()
    assert bt_termine.statut == "TERMINE"
    assert bt_cloture.statut == "CLOTURE"


@pytest.mark.django_db
def test_should_not_alter_bt_without_date_prevue():
    """
    Un BT sans date prévue ne doit jamais passer en EN_RETARD.
    """
    # GIVEN
    bt = BonTravailFactory(
        statut="EN_ATTENTE",
        date_prevue=None,
        date_debut=None,
    )

    # WHEN
    update_bt_status()

    # THEN
    bt.refresh_from_db()
    assert bt.statut == "EN_ATTENTE"
