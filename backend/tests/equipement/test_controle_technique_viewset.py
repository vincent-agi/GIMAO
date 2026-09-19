"""Tests API du ``ControleTechniqueViewSet`` (TUS-011)."""

import pytest
from rest_framework.test import APIClient

from tests.factories import VehiculeProfileFactory

pytestmark = pytest.mark.django_db


def test_create_controle_technique_returns_201():
    client = APIClient()
    vehicule_profile = VehiculeProfileFactory()

    response = client.post(
        "/api/controles-techniques/",
        {
            "vehicule_profile": vehicule_profile.pk,
            "date_passage": "2024-03-01",
            "date_echeance": "2026-03-01",
            "resultat": "FAVORABLE",
        },
        format="json",
    )

    assert response.status_code == 201, response.data


def test_list_controles_techniques_filters_by_vehicule_profile():
    client = APIClient()
    vehicule_a = VehiculeProfileFactory()
    vehicule_b = VehiculeProfileFactory()

    for vehicule in (vehicule_a, vehicule_b):
        client.post(
            "/api/controles-techniques/",
            {
                "vehicule_profile": vehicule.pk,
                "date_passage": "2024-03-01",
                "date_echeance": "2026-03-01",
                "resultat": "FAVORABLE",
            },
            format="json",
        )

    response = client.get("/api/controles-techniques/", {"vehicule_profile": vehicule_a.pk})

    assert response.status_code == 200
    payload = response.json()
    results = payload["results"] if isinstance(payload, dict) and "results" in payload else payload
    assert len(results) == 1
    assert results[0]["vehicule_profile"] == vehicule_a.pk


def test_create_controle_technique_rejects_invalid_resultat_choice():
    client = APIClient()
    vehicule_profile = VehiculeProfileFactory()

    response = client.post(
        "/api/controles-techniques/",
        {
            "vehicule_profile": vehicule_profile.pk,
            "date_passage": "2024-03-01",
            "date_echeance": "2026-03-01",
            "resultat": "PAS_UN_RESULTAT_VALIDE",
        },
        format="json",
    )

    assert response.status_code == 400
