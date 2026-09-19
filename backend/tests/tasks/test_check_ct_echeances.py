"""Tests du job d'alerte d'échéance de contrôle technique (US-012)."""

import datetime

import pytest

from equipement import services
from notifications.models import NotificationEnvoyee
from tasks.checkCtEcheances import check_ct_echeances
from tests.factories import UtilisateurFactory, VehiculeProfileFactory

pytestmark = pytest.mark.django_db


def make_declencher_a_echeance(vehicule_profile, jours_avant_echeance=30):
    """Crée un contrôle technique favorable dont l'échéance est déjà dans la fenêtre d'anticipation."""
    from equipement.models import ControleTechnique

    aujourdhui = datetime.date.today()
    date_echeance = aujourdhui + datetime.timedelta(days=jours_avant_echeance)
    controle = ControleTechnique.objects.create(
        vehicule_profile=vehicule_profile,
        date_passage=aujourdhui - datetime.timedelta(days=365),
        date_echeance=date_echeance,
        resultat="FAVORABLE",
    )
    declencher = services.brancher_controle_technique_sur_declencheur(controle)

    # Simule le cron update_calendar_counters : la valeur courante du compteur
    # calendaire est positionnee sur la date du jour.
    declencher.compteur.valeurCourante = services.date_to_ordinal_days(aujourdhui.isoformat())
    declencher.compteur.save(update_fields=["valeurCourante"])

    return declencher


class TestCheckCtEcheances:
    def test_should_send_notification_when_within_anticipation_window(self, mailoutbox):
        UtilisateurFactory(role__nomRole="Responsable GMAO", email="responsable@gimao.local")
        vehicule_profile = VehiculeProfileFactory()
        make_declencher_a_echeance(vehicule_profile, jours_avant_echeance=30)

        sent = check_ct_echeances()

        assert sent == 1
        assert len(mailoutbox) == 1
        assert vehicule_profile.equipement.designation in mailoutbox[0].subject

    def test_should_not_send_when_echeance_is_far_away(self, mailoutbox):
        UtilisateurFactory(role__nomRole="Responsable GMAO", email="responsable@gimao.local")
        vehicule_profile = VehiculeProfileFactory()
        make_declencher_a_echeance(vehicule_profile, jours_avant_echeance=300)

        sent = check_ct_echeances()

        assert sent == 0
        assert len(mailoutbox) == 0

    def test_should_not_send_duplicate_on_second_run(self, mailoutbox):
        UtilisateurFactory(role__nomRole="Responsable GMAO", email="responsable@gimao.local")
        vehicule_profile = VehiculeProfileFactory()
        make_declencher_a_echeance(vehicule_profile, jours_avant_echeance=30)

        first_run = check_ct_echeances()
        second_run = check_ct_echeances()

        assert first_run == 1
        assert second_run == 0
        assert len(mailoutbox) == 1
        assert NotificationEnvoyee.objects.count() == 1

    def test_should_not_send_when_no_responsable_gmao_has_email(self, mailoutbox):
        # La migration de donnees tasks/0001_initial_data seme un utilisateur
        # "responsable" (role Responsable GMAO) sans email : ce cas est deja
        # couvert par ce seed, aucun utilisateur supplementaire a creer ici.
        vehicule_profile = VehiculeProfileFactory()
        make_declencher_a_echeance(vehicule_profile, jours_avant_echeance=30)

        sent = check_ct_echeances()

        assert sent == 0
        assert len(mailoutbox) == 0
