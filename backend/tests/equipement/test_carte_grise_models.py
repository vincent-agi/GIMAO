"""Tests du modèle ``CarteGrise`` (TUS-010)."""

import datetime

import pytest
from django.core.exceptions import ValidationError

from equipement.models import CarteGrise
from tests.factories import VehiculeProfileFactory

pytestmark = pytest.mark.django_db


def make_carte_grise(vehicule_profile=None, **overrides):
    fields = {
        "vehicule_profile": vehicule_profile or VehiculeProfileFactory(),
        "immatriculation": "AB-123-CD",
        "titulaire": "Société GIMAO Transports",
        "date_premiere_mise_circulation": datetime.date(2020, 1, 15),
        "date_emission": datetime.date(2024, 3, 1),
    }
    fields.update(overrides)
    return CarteGrise(**fields)


class TestCarteGriseCreation:
    def test_should_create_carte_grise_linked_to_vehicule_profile(self):
        vehicule_profile = VehiculeProfileFactory()

        carte = make_carte_grise(vehicule_profile=vehicule_profile)
        carte.full_clean()
        carte.save()

        assert carte in vehicule_profile.cartes_grises.all()

    def test_should_reject_immatriculation_not_matching_siv_format(self):
        carte = make_carte_grise(immatriculation="1234ABC")

        with pytest.raises(ValidationError):
            carte.full_clean()


class TestCarteGriseHistorique:
    def test_should_keep_history_when_titulaire_changes(self):
        vehicule_profile = VehiculeProfileFactory()
        make_carte_grise(
            vehicule_profile=vehicule_profile,
            titulaire="Ancien titulaire",
            date_emission=datetime.date(2020, 1, 1),
        ).save()
        make_carte_grise(
            vehicule_profile=vehicule_profile,
            titulaire="Nouveau titulaire",
            date_emission=datetime.date(2024, 1, 1),
        ).save()

        assert vehicule_profile.cartes_grises.count() == 2

    def test_most_recent_carte_grise_should_be_first_by_default_ordering(self):
        vehicule_profile = VehiculeProfileFactory()
        ancienne = make_carte_grise(
            vehicule_profile=vehicule_profile, date_emission=datetime.date(2020, 1, 1)
        )
        ancienne.save()
        recente = make_carte_grise(
            vehicule_profile=vehicule_profile, date_emission=datetime.date(2024, 1, 1)
        )
        recente.save()

        derniere_carte = vehicule_profile.cartes_grises.first()

        assert derniere_carte.pk == recente.pk
