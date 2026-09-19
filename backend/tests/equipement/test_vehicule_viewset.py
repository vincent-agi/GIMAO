"""Tests API du ``VehiculeViewSet`` (TUS-005)."""

import pytest
from rest_framework.test import APIClient

from tests.factories import (
    EquipementFactory,
    FamilleEquipementFactory,
    FournisseurFactory,
    LieuFactory,
    ModeleEquipementFactory,
    UtilisateurFactory,
)

pytestmark = pytest.mark.django_db


def build_create_payload(utilisateur, **overrides):
    lieu = LieuFactory()
    famille = FamilleEquipementFactory()
    fournisseur = FournisseurFactory()
    modele = ModeleEquipementFactory()
    payload = {
        "reference": "REF-API-001",
        "designation": "Fourgon atelier",
        "lieu": lieu.id,
        "modeleEquipement": modele.id,
        "famille": famille.id,
        "fournisseur": fournisseur.id,
        "fabricant": modele.fabricant.id,
        "createurEquipement": utilisateur.id,
        "vin": "VF1BB000000000099",
        "immatriculation": "CD-456-EF",
        "genre": "VL",
        "energie": "ESSENCE",
    }
    payload.update(overrides)
    return payload


def test_create_vehicule_returns_201_with_nested_profile():
    client = APIClient()
    utilisateur = UtilisateurFactory()

    response = client.post("/api/vehicules/", build_create_payload(utilisateur), format="json")

    assert response.status_code == 201, response.data
    payload = response.json()
    assert payload["type"] == "VEHICULE"
    assert payload["vehicule_profile"]["immatriculation"] == "CD-456-EF"


def test_create_vehicule_returns_400_on_invalid_vin():
    client = APIClient()
    utilisateur = UtilisateurFactory()

    response = client.post(
        "/api/vehicules/", build_create_payload(utilisateur, vin="TROP_COURT"), format="json"
    )

    assert response.status_code == 400


def test_list_vehicules_excludes_non_vehicule_equipements():
    client = APIClient()
    utilisateur = UtilisateurFactory()
    EquipementFactory(type="MECANIQUE")
    response = client.post("/api/vehicules/", build_create_payload(utilisateur), format="json")
    assert response.status_code == 201

    list_response = client.get("/api/vehicules/")

    assert list_response.status_code == 200
    payload = list_response.json()
    results = payload["results"] if "results" in payload else payload
    assert all(item["type"] == "VEHICULE" for item in results)


def test_retrieve_non_vehicule_equipement_returns_404():
    client = APIClient()
    equipement = EquipementFactory(type="MECANIQUE")

    response = client.get(f"/api/vehicules/{equipement.pk}/")

    assert response.status_code == 404


def test_update_vehicule_persists_profile_field_change():
    client = APIClient()
    utilisateur = UtilisateurFactory()
    create_response = client.post(
        "/api/vehicules/", build_create_payload(utilisateur), format="json"
    )
    vehicule_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/vehicules/{vehicule_id}/",
        {"changes": '{"genre": {"nouvelle": "UTILITAIRE"}}'},
        format="json",
    )

    assert update_response.status_code == 200, update_response.data
    assert update_response.json()["vehicule_profile"]["genre"] == "UTILITAIRE"
