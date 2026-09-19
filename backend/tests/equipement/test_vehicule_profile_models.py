"""Tests du modèle ``VehiculeProfile`` (cf. TUS-004, ADR-001)."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from equipement.models import Equipement, VehiculeProfile
from tests.factories import EquipementFactory

pytestmark = pytest.mark.django_db


def make_vehicule_profile(equipement=None, **overrides):
    """Construit un ``VehiculeProfile`` valide, avec surcharges optionnelles."""
    fields = {
        "equipement": equipement or EquipementFactory(type="VEHICULE"),
        "vin": "VF1BB000000000001",
        "immatriculation": "AB-123-CD",
        "genre": "VL",
        "energie": "DIESEL",
    }
    fields.update(overrides)
    return VehiculeProfile(**fields)


class TestVehiculeProfileCreation:
    def test_should_create_profile_linked_to_equipement(self):
        equipement = EquipementFactory(type="VEHICULE")

        profile = make_vehicule_profile(equipement=equipement)
        profile.full_clean()
        profile.save()

        assert VehiculeProfile.objects.get(pk=equipement.pk) == profile
        assert equipement.vehicule_profile == profile

    def test_should_reject_vin_with_wrong_length(self):
        profile = make_vehicule_profile(vin="TROP_COURT")

        with pytest.raises(ValidationError):
            profile.full_clean()

    def test_should_reject_vin_containing_forbidden_letters(self):
        # I, O, Q sont exclus de la norme ISO 3779.
        profile = make_vehicule_profile(vin="VF1BBOOO000000001")

        with pytest.raises(ValidationError):
            profile.full_clean()

    def test_should_reject_immatriculation_not_matching_siv_format(self):
        profile = make_vehicule_profile(immatriculation="1234 AB 56")

        with pytest.raises(ValidationError):
            profile.full_clean()

    def test_should_accept_valid_siv_immatriculation(self):
        profile = make_vehicule_profile(immatriculation="AB-123-CD")

        profile.full_clean()  # ne doit pas lever

    def test_should_reject_duplicate_vin(self):
        make_vehicule_profile(vin="VF1BB000000000002", immatriculation="AA-111-AA").save()

        with pytest.raises(IntegrityError):
            make_vehicule_profile(vin="VF1BB000000000002", immatriculation="BB-222-BB").save()

    def test_should_reject_duplicate_immatriculation(self):
        make_vehicule_profile(vin="VF1BB000000000003", immatriculation="CC-333-CC").save()

        with pytest.raises(IntegrityError):
            make_vehicule_profile(vin="VF1BB000000000004", immatriculation="CC-333-CC").save()


class TestVehiculeProfileCascade:
    def test_should_delete_profile_when_equipement_is_deleted(self):
        equipement = EquipementFactory(type="VEHICULE")
        profile = make_vehicule_profile(equipement=equipement)
        profile.save()

        equipement.delete()

        assert not VehiculeProfile.objects.filter(pk=profile.pk).exists()

    def test_equipement_without_profile_should_not_expose_one(self):
        equipement = EquipementFactory(type="MECANIQUE")

        with pytest.raises(Equipement.vehicule_profile.RelatedObjectDoesNotExist):
            _ = equipement.vehicule_profile
