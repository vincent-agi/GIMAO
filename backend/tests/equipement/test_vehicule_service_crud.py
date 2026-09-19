"""Tests unitaires de ``equipement.services.create_vehicule``/``update_vehicule`` (TUS-005)."""

from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError

from equipement import services
from equipement.models import Equipement, VehiculeProfile
from tests.factories import (
    FamilleEquipementFactory,
    FournisseurFactory,
    LieuFactory,
    ModeleEquipementFactory,
    UtilisateurFactory,
)

pytestmark = pytest.mark.django_db


def authenticated_request_user(utilisateur):
    return SimpleNamespace(is_authenticated=True, username=utilisateur.nomUtilisateur)


def base_vehicule_data(**overrides):
    lieu = LieuFactory()
    famille = FamilleEquipementFactory()
    fournisseur = FournisseurFactory()
    modele = ModeleEquipementFactory()
    data = {
        "reference": "REF-VEH-001",
        "designation": "Camionnette de service",
        "lieu": lieu.id,
        "modeleEquipement": modele.id,
        "famille": famille.id,
        "fournisseur": fournisseur.id,
        "fabricant": modele.fabricant.id,
        "vin": "VF1BB000000000010",
        "immatriculation": "AB-123-CD",
        "genre": "VL",
        "energie": "DIESEL",
    }
    data.update(overrides)
    return data


class TestCreateVehicule:
    def test_should_create_equipement_of_type_vehicule_and_its_profile(self):
        utilisateur = UtilisateurFactory()
        data = base_vehicule_data()

        equipement = services.create_vehicule(data, {}, authenticated_request_user(utilisateur))

        assert equipement.type == "VEHICULE"
        profile = VehiculeProfile.objects.get(pk=equipement.pk)
        assert profile.vin == "VF1BB000000000010"
        assert profile.immatriculation == "AB-123-CD"
        assert profile.genre == "VL"

    def test_should_not_create_equipement_when_vehicule_profile_data_invalid(self):
        utilisateur = UtilisateurFactory()
        data = base_vehicule_data(vin="TROP_COURT")

        with pytest.raises(ValidationError):
            services.create_vehicule(data, {}, authenticated_request_user(utilisateur))

        assert not Equipement.objects.filter(reference="REF-VEH-001").exists()

    def test_should_propagate_createur_introuvable(self):
        data = base_vehicule_data()

        with pytest.raises(services.UtilisateurCreateurIntrouvable):
            services.create_vehicule(data, {}, SimpleNamespace(is_authenticated=False))


class TestUpdateVehicule:
    def _create_vehicule(self, utilisateur):
        return services.create_vehicule(
            base_vehicule_data(), {}, authenticated_request_user(utilisateur)
        )

    def test_should_update_equipement_field(self):
        utilisateur = UtilisateurFactory()
        equipement = self._create_vehicule(utilisateur)

        updated = services.update_vehicule(
            equipement, {"designation": {"nouvelle": "Camionnette renommée"}}, {}
        )

        assert updated.designation == "Camionnette renommée"

    def test_should_update_vehicule_profile_field(self):
        utilisateur = UtilisateurFactory()
        equipement = self._create_vehicule(utilisateur)

        services.update_vehicule(equipement, {"immatriculation": {"nouvelle": "ZZ-999-ZZ"}}, {})

        profile = VehiculeProfile.objects.get(pk=equipement.pk)
        assert profile.immatriculation == "ZZ-999-ZZ"

    def test_should_update_mixed_equipement_and_profile_fields_together(self):
        utilisateur = UtilisateurFactory()
        equipement = self._create_vehicule(utilisateur)

        services.update_vehicule(
            equipement,
            {
                "designation": {"nouvelle": "Nouveau nom"},
                "genre": {"nouvelle": "UTILITAIRE"},
            },
            {},
        )

        equipement.refresh_from_db()
        profile = VehiculeProfile.objects.get(pk=equipement.pk)
        assert equipement.designation == "Nouveau nom"
        assert profile.genre == "UTILITAIRE"

    def test_should_reject_invalid_profile_value_via_full_clean(self):
        utilisateur = UtilisateurFactory()
        equipement = self._create_vehicule(utilisateur)

        with pytest.raises(ValidationError):
            services.update_vehicule(equipement, {"immatriculation": {"nouvelle": "invalide"}}, {})
