"""Tests du modèle ``ControleTechnique`` (TUS-011)."""

import datetime

import pytest

from equipement.models import ControleTechnique
from tests.factories import VehiculeProfileFactory

pytestmark = pytest.mark.django_db


def make_controle_technique(vehicule_profile=None, **overrides):
    fields = {
        "vehicule_profile": vehicule_profile or VehiculeProfileFactory(),
        "date_passage": datetime.date(2024, 3, 1),
        "date_echeance": datetime.date(2026, 3, 1),
        "resultat": "FAVORABLE",
    }
    fields.update(overrides)
    return ControleTechnique.objects.create(**fields)


class TestControleTechniqueCreation:
    def test_should_create_controle_linked_to_vehicule_profile(self):
        vehicule_profile = VehiculeProfileFactory()

        controle = make_controle_technique(vehicule_profile=vehicule_profile)

        assert controle in vehicule_profile.controles_techniques.all()

    def test_should_store_defavorable_result_with_contre_visite_echeance(self):
        controle = make_controle_technique(
            resultat="DEFAVORABLE",
            date_passage=datetime.date(2024, 3, 1),
            date_echeance=datetime.date(2024, 5, 1),
        )

        assert controle.resultat == "DEFAVORABLE"
        assert controle.date_echeance == datetime.date(2024, 5, 1)


class TestControleTechniqueHistorique:
    def test_should_keep_history_of_multiple_passages(self):
        vehicule_profile = VehiculeProfileFactory()
        make_controle_technique(
            vehicule_profile=vehicule_profile, date_passage=datetime.date(2022, 1, 1)
        )
        make_controle_technique(
            vehicule_profile=vehicule_profile, date_passage=datetime.date(2024, 1, 1)
        )

        assert vehicule_profile.controles_techniques.count() == 2

    def test_most_recent_controle_should_be_first_by_default_ordering(self):
        vehicule_profile = VehiculeProfileFactory()
        make_controle_technique(
            vehicule_profile=vehicule_profile, date_passage=datetime.date(2022, 1, 1)
        )
        recent = make_controle_technique(
            vehicule_profile=vehicule_profile, date_passage=datetime.date(2024, 1, 1)
        )

        assert vehicule_profile.controles_techniques.first().pk == recent.pk
