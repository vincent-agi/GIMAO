"""Tests API du ``CodeDefautOBDViewSet`` (US-022)."""

import pytest
from rest_framework.test import APIClient

from tests.factories import DemandeInterventionFactory, VehiculeProfileFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_create_code_defaut_obd_returns_201(api_client):
    vehicule_profile = VehiculeProfileFactory()

    response = api_client.post(
        "/api/codes-defaut-obd/",
        {
            "vehicule_profile": vehicule_profile.pk,
            "code": "P0301",
            "description": "Raté d'allumage cylindre 1",
            "date_lecture": "2024-03-01T10:00:00Z",
            "source": "MANUEL",
        },
        format="json",
    )

    assert response.status_code == 201, response.data


@pytest.mark.django_db
def test_create_code_defaut_obd_without_incident_is_allowed(api_client):
    vehicule_profile = VehiculeProfileFactory()

    response = api_client.post(
        "/api/codes-defaut-obd/",
        {
            "vehicule_profile": vehicule_profile.pk,
            "code": "P0171",
            "date_lecture": "2024-03-01T10:00:00Z",
            "source": "AUTOMATIQUE",
        },
        format="json",
    )

    assert response.status_code == 201, response.data
    assert response.json()["incident_vehicule"] is None


@pytest.mark.django_db
def test_list_codes_defaut_obd_filters_by_vehicule_profile(api_client):
    vehicule_a = VehiculeProfileFactory()
    vehicule_b = VehiculeProfileFactory()

    for vehicule, code in [(vehicule_a, "P0100"), (vehicule_b, "P0200")]:
        api_client.post(
            "/api/codes-defaut-obd/",
            {
                "vehicule_profile": vehicule.pk,
                "code": code,
                "date_lecture": "2024-03-01T10:00:00Z",
                "source": "MANUEL",
            },
            format="json",
        )

    response = api_client.get("/api/codes-defaut-obd/", {"vehicule_profile": vehicule_a.pk})

    assert response.status_code == 200
    payload = response.json()
    results = payload["results"] if isinstance(payload, dict) and "results" in payload else payload
    assert len(results) == 1
    assert results[0]["code"] == "P0100"


@pytest.mark.django_db
def test_create_code_defaut_obd_linked_to_incident(api_client):
    from maintenance.models import IncidentVehicule

    vehicule_profile = VehiculeProfileFactory()
    incident = IncidentVehicule.objects.create(
        demande_intervention=DemandeInterventionFactory(equipement=vehicule_profile.equipement),
        type_avarie="CODE_DEFAUT",
    )

    response = api_client.post(
        "/api/codes-defaut-obd/",
        {
            "vehicule_profile": vehicule_profile.pk,
            "incident_vehicule": incident.pk,
            "code": "P0420",
            "date_lecture": "2024-03-01T10:00:00Z",
            "source": "MANUEL",
        },
        format="json",
    )

    assert response.status_code == 201, response.data
    assert response.json()["incident_vehicule"] == incident.pk


@pytest.mark.django_db
def test_create_code_defaut_obd_rejects_invalid_source():
    api_client = APIClient()
    vehicule_profile = VehiculeProfileFactory()

    response = api_client.post(
        "/api/codes-defaut-obd/",
        {
            "vehicule_profile": vehicule_profile.pk,
            "code": "P0100",
            "date_lecture": "2024-03-01T10:00:00Z",
            "source": "PAS_UNE_SOURCE_VALIDE",
        },
        format="json",
    )

    assert response.status_code == 400
