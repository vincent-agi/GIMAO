"""Tests du branchement ControleTechnique -> Compteur/Declencher (TUS-012).

Vérifie l'intégration bout en bout avec le cron existant
``tasks.counterCron.update_counter`` : un contrôle technique favorable doit
suivre exactement le même chemin qu'un ``Declencher`` classique, sans aucune
modification du cron.
"""

import datetime

import pytest

from equipement import services
from equipement.models import Compteur, ControleTechnique, Declencher
from maintenance.models import BonTravail, DemandeIntervention, PlanMaintenance
from tasks.counterCron import update_counter
from tests.factories import UtilisateurFactory, VehiculeProfileFactory

pytestmark = pytest.mark.django_db


def make_favorable_controle(vehicule_profile, date_passage, date_echeance):
    return ControleTechnique.objects.create(
        vehicule_profile=vehicule_profile,
        date_passage=date_passage,
        date_echeance=date_echeance,
        resultat="FAVORABLE",
    )


class TestBrancherControleTechnique:
    def test_should_create_compteur_and_plan_and_declencher(self):
        vehicule_profile = VehiculeProfileFactory()
        controle = make_favorable_controle(
            vehicule_profile, datetime.date(2024, 3, 1), datetime.date(2026, 3, 1)
        )

        declencher = services.brancher_controle_technique_sur_declencheur(controle)

        assert declencher is not None
        assert Compteur.objects.filter(
            equipement=vehicule_profile.equipement, nomCompteur="Échéance Contrôle Technique"
        ).exists()
        assert PlanMaintenance.objects.filter(
            equipement=vehicule_profile.equipement, nom="Contrôle technique"
        ).exists()
        assert declencher.anticipationJours == 60

    def test_should_do_nothing_when_resultat_is_not_favorable(self):
        vehicule_profile = VehiculeProfileFactory()
        controle = ControleTechnique.objects.create(
            vehicule_profile=vehicule_profile,
            date_passage=datetime.date(2024, 3, 1),
            date_echeance=datetime.date(2024, 5, 1),
            resultat="DEFAVORABLE",
        )

        result = services.brancher_controle_technique_sur_declencheur(controle)

        assert result is None
        assert not Compteur.objects.filter(equipement=vehicule_profile.equipement).exists()

    def test_should_reuse_existing_compteur_and_plan_on_second_controle(self):
        vehicule_profile = VehiculeProfileFactory()
        premier = make_favorable_controle(
            vehicule_profile, datetime.date(2020, 1, 1), datetime.date(2022, 1, 1)
        )
        second = make_favorable_controle(
            vehicule_profile, datetime.date(2022, 1, 15), datetime.date(2024, 1, 15)
        )
        services.brancher_controle_technique_sur_declencheur(premier)
        services.brancher_controle_technique_sur_declencheur(second)

        assert Compteur.objects.filter(equipement=vehicule_profile.equipement).count() == 1
        assert PlanMaintenance.objects.filter(equipement=vehicule_profile.equipement).count() == 1
        assert (
            Declencher.objects.filter(compteur__equipement=vehicule_profile.equipement).count() == 1
        )

    def test_should_update_echeance_on_second_favorable_controle(self):
        vehicule_profile = VehiculeProfileFactory()
        premier_controle = make_favorable_controle(
            vehicule_profile, datetime.date(2020, 1, 1), datetime.date(2022, 1, 1)
        )
        services.brancher_controle_technique_sur_declencheur(premier_controle)

        second_controle = make_favorable_controle(
            vehicule_profile, datetime.date(2022, 1, 15), datetime.date(2024, 1, 15)
        )
        declencher = services.brancher_controle_technique_sur_declencheur(second_controle)

        assert declencher.prochaineMaintenance == services.date_to_ordinal_days("2024-01-15")


class TestControleTechniqueDeclencheurEndToEnd:
    def test_should_create_preventive_bt_when_cron_runs_past_echeance(self):
        """Reproduit le scenario complet CT -> Declencher -> cron -> BT (US-013)."""
        UtilisateurFactory(role__nomRole="Responsable GMAO")
        vehicule_profile = VehiculeProfileFactory()

        # Echeance dans le passe pour que le cron la detecte immediatement.
        controle = make_favorable_controle(
            vehicule_profile,
            datetime.date(2020, 1, 1),
            datetime.date(2020, 6, 1),
        )
        services.brancher_controle_technique_sur_declencheur(controle)

        # Le cron de mise a jour des compteurs calendaires positionne la
        # valeur courante du compteur CT sur la date du jour (comportement
        # existant, non modifie par cette fonctionnalite).
        compteur = Compteur.objects.get(
            equipement=vehicule_profile.equipement, nomCompteur="Échéance Contrôle Technique"
        )
        compteur.valeurCourante = services.date_to_ordinal_days(datetime.date.today().isoformat())
        compteur.save(update_fields=["valeurCourante"])

        bt_created = update_counter()

        assert bt_created >= 1
        assert DemandeIntervention.objects.filter(equipement=vehicule_profile.equipement).exists()
        assert BonTravail.objects.filter(
            demande_intervention__equipement=vehicule_profile.equipement
        ).exists()
