"""Tests de l'enrichissement véhicule de DemandeInterventionViewSet.create (US-020/021).

Vérifie que fournir ``incident_vehicule`` (et optionnellement ``sinistre``)
dans le payload de création d'une DI crée l'IncidentVehicule (et le
Sinistre) associés, et que le chemin générique existant (sans
``incident_vehicule``) reste inchangé.
"""

import json

import pytest
from rest_framework.test import APIRequestFactory

from maintenance.api.viewsets import DemandeInterventionViewSet
from maintenance.models import DemandeIntervention, IncidentVehicule, Sinistre
from tests.factories import EquipementFactory, UtilisateurFactory


@pytest.fixture
def api_factory():
    return APIRequestFactory()


@pytest.mark.django_db
def test_should_create_di_and_incident_for_voyant_signal(api_factory):
    utilisateur = UtilisateurFactory()
    equipement = EquipementFactory(type="VEHICULE")

    view = DemandeInterventionViewSet.as_view({"post": "create"})
    request = api_factory.post(
        "/api/maintenance/demandes-intervention/",
        {
            "nom": "Voyant moteur allumé",
            "statut_suppose": "DEGRADE",
            "equipement_id": str(equipement.pk),
            "utilisateur_id": str(utilisateur.pk),
            "incident_vehicule": json.dumps({"type_avarie": "VOYANT", "gravite": "MODEREE"}),
        },
        format="json",
    )

    response = view(request)

    assert response.status_code == 201, response.data
    demande = DemandeIntervention.objects.get(pk=response.data["id"])
    assert demande.statut == "EN_ATTENTE"
    incident = IncidentVehicule.objects.get(demande_intervention=demande)
    assert incident.type_avarie == "VOYANT"
    assert incident.gravite == "MODEREE"
    assert incident.immobilisation is False


@pytest.mark.django_db
def test_should_create_di_incident_and_sinistre_for_accident(api_factory):
    utilisateur = UtilisateurFactory()
    equipement = EquipementFactory(type="VEHICULE")

    view = DemandeInterventionViewSet.as_view({"post": "create"})
    request = api_factory.post(
        "/api/maintenance/demandes-intervention/",
        {
            "nom": "Accident sur parking",
            "statut_suppose": "A_LARRET",
            "equipement_id": str(equipement.pk),
            "utilisateur_id": str(utilisateur.pk),
            "incident_vehicule": json.dumps(
                {"type_avarie": "ACCIDENT_ROUTE", "gravite": "CRITIQUE", "immobilisation": True}
            ),
            "sinistre": json.dumps(
                {
                    "date_accident": "2024-06-01",
                    "lieu_accident": "Parking dépôt central",
                    "tiers_impliques": "Aucun tiers",
                }
            ),
        },
        format="json",
    )

    response = view(request)

    assert response.status_code == 201, response.data
    demande = DemandeIntervention.objects.get(pk=response.data["id"])
    incident = IncidentVehicule.objects.get(demande_intervention=demande)
    assert incident.immobilisation is True
    sinistre = Sinistre.objects.get(incident_vehicule=incident)
    assert sinistre.lieu_accident == "Parking dépôt central"


@pytest.mark.django_db
def test_should_reject_sinistre_for_non_accident_type_avarie(api_factory):
    utilisateur = UtilisateurFactory()
    equipement = EquipementFactory(type="VEHICULE")

    view = DemandeInterventionViewSet.as_view({"post": "create"})
    request = api_factory.post(
        "/api/maintenance/demandes-intervention/",
        {
            "nom": "Bruit anormal avec sinistre incohérent",
            "statut_suppose": "DEGRADE",
            "equipement_id": str(equipement.pk),
            "utilisateur_id": str(utilisateur.pk),
            "incident_vehicule": json.dumps({"type_avarie": "BRUIT_ANORMAL"}),
            "sinistre": json.dumps(
                {"date_accident": "2024-06-01", "lieu_accident": "Parking dépôt central"}
            ),
        },
        format="json",
    )

    response = view(request)

    assert response.status_code == 400
    # La DI ne doit pas avoir été créée (transaction atomique).
    assert not DemandeIntervention.objects.filter(
        nom="Bruit anormal avec sinistre incohérent"
    ).exists()


@pytest.mark.django_db
def test_should_reject_invalid_type_avarie_choice(api_factory):
    utilisateur = UtilisateurFactory()
    equipement = EquipementFactory(type="VEHICULE")

    view = DemandeInterventionViewSet.as_view({"post": "create"})
    request = api_factory.post(
        "/api/maintenance/demandes-intervention/",
        {
            "nom": "Type invalide",
            "statut_suppose": "DEGRADE",
            "equipement_id": str(equipement.pk),
            "utilisateur_id": str(utilisateur.pk),
            "incident_vehicule": json.dumps({"type_avarie": "PAS_UN_TYPE_VALIDE"}),
        },
        format="json",
    )

    response = view(request)

    assert response.status_code == 400


@pytest.mark.django_db
def test_should_still_create_plain_di_without_incident_vehicule(api_factory):
    """Non-régression : le chemin générique (sans incident_vehicule) est inchangé."""
    utilisateur = UtilisateurFactory()
    equipement = EquipementFactory()

    view = DemandeInterventionViewSet.as_view({"post": "create"})
    request = api_factory.post(
        "/api/maintenance/demandes-intervention/",
        {
            "nom": "DI générique classique",
            "statut_suppose": "EN_FONCTIONNEMENT",
            "equipement_id": str(equipement.pk),
            "utilisateur_id": str(utilisateur.pk),
        },
        format="json",
    )

    response = view(request)

    assert response.status_code == 201, response.data
    demande = DemandeIntervention.objects.get(pk=response.data["id"])
    assert not IncidentVehicule.objects.filter(demande_intervention=demande).exists()


@pytest.mark.django_db
def test_retrieve_should_expose_incident_vehicule_and_sinistre(api_factory):
    utilisateur = UtilisateurFactory()
    equipement = EquipementFactory(type="VEHICULE")

    create_view = DemandeInterventionViewSet.as_view({"post": "create"})
    create_request = api_factory.post(
        "/api/maintenance/demandes-intervention/",
        {
            "nom": "Accident avec sinistre",
            "statut_suppose": "A_LARRET",
            "equipement_id": str(equipement.pk),
            "utilisateur_id": str(utilisateur.pk),
            "incident_vehicule": json.dumps({"type_avarie": "ACCIDENT_ROUTE"}),
            "sinistre": json.dumps(
                {"date_accident": "2024-06-01", "lieu_accident": "Rond-point Nord"}
            ),
        },
        format="json",
    )
    demande_id = create_view(create_request).data["id"]

    retrieve_view = DemandeInterventionViewSet.as_view({"get": "retrieve"})
    retrieve_request = api_factory.get(f"/api/maintenance/demandes-intervention/{demande_id}/")
    response = retrieve_view(retrieve_request, pk=demande_id)

    assert response.status_code == 200
    assert response.data["incident_vehicule"]["type_avarie"] == "ACCIDENT_ROUTE"
    assert response.data["incident_vehicule"]["sinistre"]["lieu_accident"] == "Rond-point Nord"


@pytest.mark.django_db
def test_retrieve_should_expose_null_incident_vehicule_for_generic_di(api_factory):
    utilisateur = UtilisateurFactory()
    equipement = EquipementFactory()

    create_view = DemandeInterventionViewSet.as_view({"post": "create"})
    create_request = api_factory.post(
        "/api/maintenance/demandes-intervention/",
        {
            "nom": "DI générique",
            "statut_suppose": "EN_FONCTIONNEMENT",
            "equipement_id": str(equipement.pk),
            "utilisateur_id": str(utilisateur.pk),
        },
        format="json",
    )
    demande_id = create_view(create_request).data["id"]

    retrieve_view = DemandeInterventionViewSet.as_view({"get": "retrieve"})
    retrieve_request = api_factory.get(f"/api/maintenance/demandes-intervention/{demande_id}/")
    response = retrieve_view(retrieve_request, pk=demande_id)

    assert response.status_code == 200
    assert response.data["incident_vehicule"] is None
