"""Tests API du ``CarteGriseViewSet`` (complète TUS-010 : endpoint nécessaire à US-010)."""

import pytest
from rest_framework.test import APIClient

from tests.factories import VehiculeProfileFactory

pytestmark = pytest.mark.django_db


def test_create_carte_grise_returns_201():
    client = APIClient()
    vehicule_profile = VehiculeProfileFactory()

    response = client.post(
        "/api/cartes-grises/",
        {
            "vehicule_profile": vehicule_profile.pk,
            "immatriculation": vehicule_profile.immatriculation,
            "titulaire": "Société GIMAO Transports",
            "date_premiere_mise_circulation": "2020-01-15",
            "date_emission": "2024-03-01",
        },
        format="json",
    )

    assert response.status_code == 201, response.data


def test_list_cartes_grises_filters_by_vehicule_profile():
    client = APIClient()
    vehicule_a = VehiculeProfileFactory()
    vehicule_b = VehiculeProfileFactory()

    for vehicule, titulaire in [(vehicule_a, "Titulaire A"), (vehicule_b, "Titulaire B")]:
        client.post(
            "/api/cartes-grises/",
            {
                "vehicule_profile": vehicule.pk,
                "immatriculation": vehicule.immatriculation,
                "titulaire": titulaire,
                "date_premiere_mise_circulation": "2020-01-15",
                "date_emission": "2024-03-01",
            },
            format="json",
        )

    response = client.get("/api/cartes-grises/", {"vehicule_profile": vehicule_a.pk})

    assert response.status_code == 200
    payload = response.json()
    results = payload["results"] if isinstance(payload, dict) and "results" in payload else payload
    assert len(results) == 1
    assert results[0]["titulaire"] == "Titulaire A"


def test_create_carte_grise_rejects_invalid_immatriculation_format():
    client = APIClient()
    vehicule_profile = VehiculeProfileFactory()

    response = client.post(
        "/api/cartes-grises/",
        {
            "vehicule_profile": vehicule_profile.pk,
            "immatriculation": "invalide",
            "titulaire": "Société GIMAO Transports",
            "date_premiere_mise_circulation": "2020-01-15",
            "date_emission": "2024-03-01",
        },
        format="json",
    )

    assert response.status_code == 400
