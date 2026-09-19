import json
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory

from donnees.models import Document, TypeDocument
from equipement.models import Declencher
from maintenance.api.viewsets import PlanMaintenanceViewSet
from maintenance.models import PlanMaintenance, PlanMaintenanceConsommable, PlanMaintenanceDocument
from tests.factories import (
    CompteurFactory,
    ConsommableFactory,
    PlanMaintenanceFactory,
    TypePlanMaintenanceFactory,
)


@pytest.fixture
def api_factory():
    return APIRequestFactory()


@pytest.mark.django_db
def test_should_return_400_when_par_equipement_without_param(api_factory):
    view = PlanMaintenanceViewSet.as_view({"get": "par_equipement"})
    request = api_factory.get("/api/maintenance/plans-maintenance/par_equipement/")

    response = view(request)

    assert response.status_code == 400
    assert "equipement_id" in response.data["error"]


@pytest.mark.django_db
def test_should_filter_plans_by_equipement(api_factory):
    plan_target = PlanMaintenanceFactory()
    PlanMaintenanceFactory()

    view = PlanMaintenanceViewSet.as_view({"get": "par_equipement"})
    request = api_factory.get(
        "/api/maintenance/plans-maintenance/par_equipement/",
        {"equipement_id": plan_target.equipement_id},
    )

    response = view(request)

    assert response.status_code == 200
    ids = [item["id"] for item in response.data]
    assert ids == [plan_target.id]


@pytest.mark.django_db
def test_should_return_400_when_create_receives_invalid_seuil_json(api_factory):
    view = PlanMaintenanceViewSet.as_view({"post": "create"})
    request = api_factory.post(
        "/api/maintenance/plans-maintenance/",
        {"seuil": "{invalid-json"},
        format="multipart",
    )

    response = view(request)

    assert response.status_code == 400
    assert "Format JSON invalide" in response.data["error"]


@pytest.mark.django_db
def test_should_return_400_when_create_without_type_id(api_factory):
    compteur = CompteurFactory()

    payload = {
        "seuil": json.dumps(
            {
                "equipmentId": compteur.equipement_id,
                "compteurId": compteur.id,
                "prochaineMaintenance": 100,
                "ecartInterventions": 10,
                "planMaintenance": {
                    "nom": "Plan sans type",
                },
            }
        )
    }

    view = PlanMaintenanceViewSet.as_view({"post": "create"})
    request = api_factory.post("/api/maintenance/plans-maintenance/", payload, format="multipart")

    response = view(request)

    assert response.status_code == 400
    assert "type de plan de maintenance" in response.data["error"]


@pytest.mark.django_db
def test_should_return_400_when_create_without_equipment_id(api_factory):
    type_plan = TypePlanMaintenanceFactory()
    compteur = CompteurFactory()

    payload = {
        "seuil": json.dumps(
            {
                "compteurId": compteur.id,
                "prochaineMaintenance": 100,
                "ecartInterventions": 10,
                "planMaintenance": {
                    "nom": "Plan sans equipement",
                    "type_id": type_plan.id,
                },
            }
        )
    }

    view = PlanMaintenanceViewSet.as_view({"post": "create"})
    request = api_factory.post("/api/maintenance/plans-maintenance/", payload, format="multipart")

    response = view(request)

    assert response.status_code == 400
    assert "équipement" in response.data["error"]


@pytest.mark.django_db
def test_should_create_plan_and_declencher_when_payload_is_valid(api_factory):
    type_plan = TypePlanMaintenanceFactory()
    compteur = CompteurFactory()

    payload = {
        "seuil": json.dumps(
            {
                "equipmentId": compteur.equipement_id,
                "compteurId": compteur.id,
                "derniereIntervention": 10,
                "prochaineMaintenance": 100,
                "ecartInterventions": 30,
                "estGlissant": True,
                "planMaintenance": {
                    "nom": "Plan valide",
                    "commentaire": "Commentaire plan",
                    "type_id": type_plan.id,
                    "necessiteHabilitationElectrique": True,
                    "necessitePermisFeu": False,
                    "consommables": [],
                    "documents": [],
                },
            }
        )
    }

    view = PlanMaintenanceViewSet.as_view({"post": "create"})
    request = api_factory.post("/api/maintenance/plans-maintenance/", payload, format="multipart")

    response = view(request)

    assert response.status_code == 201
    assert PlanMaintenance.objects.count() == 1

    plan = PlanMaintenance.objects.get()
    declenchement = Declencher.objects.get(planMaintenance=plan)

    assert plan.nom == "Plan valide"
    assert plan.type_plan_maintenance_id == type_plan.id
    assert plan.equipement_id == compteur.equipement_id
    assert declenchement.compteur_id == compteur.id
    assert declenchement.prochaineMaintenance == 100


@pytest.mark.django_db
def test_should_return_400_when_create_without_compteur_id(api_factory):
    type_plan = TypePlanMaintenanceFactory()
    compteur = CompteurFactory()

    payload = {
        "seuil": json.dumps(
            {
                "equipmentId": compteur.equipement_id,
                "prochaineMaintenance": 100,
                "ecartInterventions": 10,
                "planMaintenance": {
                    "nom": "Plan sans compteur",
                    "type_id": type_plan.id,
                },
            }
        )
    }

    view = PlanMaintenanceViewSet.as_view({"post": "create"})
    request = api_factory.post("/api/maintenance/plans-maintenance/", payload, format="multipart")

    response = view(request)

    assert response.status_code == 400
    assert "compteur" in response.data["error"].lower()


@pytest.mark.django_db
def test_should_create_plan_with_consommables_when_payload_contains_lines(api_factory):
    type_plan = TypePlanMaintenanceFactory()
    compteur = CompteurFactory()
    consommable = ConsommableFactory()

    payload = {
        "seuil": json.dumps(
            {
                "equipmentId": compteur.equipement_id,
                "compteurId": compteur.id,
                "prochaineMaintenance": 100,
                "ecartInterventions": 10,
                "planMaintenance": {
                    "nom": "Plan avec consommable",
                    "type_id": type_plan.id,
                    "consommables": [{"consommable_id": consommable.id, "quantite": 3}],
                },
            }
        )
    }

    view = PlanMaintenanceViewSet.as_view({"post": "create"})
    request = api_factory.post("/api/maintenance/plans-maintenance/", payload, format="multipart")

    response = view(request)

    assert response.status_code == 201
    plan = PlanMaintenance.objects.get(pk=response.data["id"])
    assoc = PlanMaintenanceConsommable.objects.get(plan_maintenance=plan, consommable=consommable)
    assert assoc.quantite_necessaire == 3


@pytest.mark.django_db
def test_should_return_400_when_create_with_invalid_consommable_line(api_factory):
    type_plan = TypePlanMaintenanceFactory()
    compteur = CompteurFactory()

    payload = {
        "seuil": json.dumps(
            {
                "equipmentId": compteur.equipement_id,
                "compteurId": compteur.id,
                "prochaineMaintenance": 100,
                "ecartInterventions": 10,
                "planMaintenance": {
                    "nom": "Plan consommable invalide",
                    "type_id": type_plan.id,
                    "consommables": [{"consommable_id": 999999, "quantite": 3}],
                },
            }
        )
    }

    view = PlanMaintenanceViewSet.as_view({"post": "create"})
    request = api_factory.post("/api/maintenance/plans-maintenance/", payload, format="multipart")

    with patch(
        "maintenance.api.viewsets.PlanMaintenanceConsommable.objects.create",
        side_effect=Exception("boom"),
    ):
        response = view(request)

    assert response.status_code == 400
    assert "création du plan de maintenance" in response.data["error"]


@pytest.mark.django_db
def test_should_create_plan_document_with_default_name_when_metadata_is_missing(api_factory):
    TypeDocument.objects.create(id=1, nomTypeDocument="Defaut")
    type_plan = TypePlanMaintenanceFactory()
    compteur = CompteurFactory()

    payload = {
        "seuil": json.dumps(
            {
                "equipmentId": compteur.equipement_id,
                "compteurId": compteur.id,
                "prochaineMaintenance": 100,
                "ecartInterventions": 10,
                "planMaintenance": {
                    "nom": "Plan avec doc",
                    "type_id": type_plan.id,
                    "documents": [],
                },
            }
        ),
        "documents": [SimpleUploadedFile("fallback_name.txt", b"abc", content_type="text/plain")],
    }

    view = PlanMaintenanceViewSet.as_view({"post": "create"})
    request = api_factory.post("/api/maintenance/plans-maintenance/", payload, format="multipart")

    response = view(request)

    assert response.status_code == 201
    plan = PlanMaintenance.objects.get(pk=response.data["id"])
    assoc = PlanMaintenanceDocument.objects.get(plan_maintenance=plan)
    assert assoc.document.nomDocument == "fallback_name"
    assert assoc.document.typeDocument_id == 1


@pytest.mark.django_db
def test_should_return_400_when_create_document_has_invalid_type(api_factory):
    type_plan = TypePlanMaintenanceFactory()
    compteur = CompteurFactory()

    payload = {
        "seuil": json.dumps(
            {
                "equipmentId": compteur.equipement_id,
                "compteurId": compteur.id,
                "prochaineMaintenance": 100,
                "ecartInterventions": 10,
                "planMaintenance": {
                    "nom": "Plan doc type invalide",
                    "type_id": type_plan.id,
                    "documents": [{"nomDocument": "Doc", "typeDocument_id": 999999}],
                },
            }
        ),
        "documents": [SimpleUploadedFile("doc_bad.txt", b"abc", content_type="text/plain")],
    }

    view = PlanMaintenanceViewSet.as_view({"post": "create"})
    request = api_factory.post("/api/maintenance/plans-maintenance/", payload, format="multipart")

    with patch(
        "maintenance.api.viewsets.Document.objects.create", side_effect=Exception("bad doc")
    ):
        response = view(request)

    assert response.status_code == 400
    assert "création des documents" in response.data["error"]


@pytest.mark.django_db
def test_should_update_simple_plan_fields(api_factory):
    plan = PlanMaintenanceFactory(
        nom="Plan initial",
        commentaire="Avant",
        necessiteHabilitationElectrique=False,
    )

    view = PlanMaintenanceViewSet.as_view({"put": "update"})
    request = api_factory.put(
        f"/api/maintenance/plans-maintenance/{plan.pk}/",
        {
            "nom": "Plan modifie",
            "commentaire": "Apres",
            "necessiteHabilitationElectrique": True,
        },
        format="multipart",
    )

    response = view(request, pk=plan.pk)
    plan.refresh_from_db()

    assert response.status_code == 200
    assert plan.nom == "Plan modifie"
    assert plan.commentaire == "Apres"
    assert plan.necessiteHabilitationElectrique is True


@pytest.mark.django_db
def test_should_apply_changes_json_to_plan_and_consommables(api_factory):
    plan = PlanMaintenanceFactory(nom="Plan initial", necessitePermisFeu=False)
    old_consommable = ConsommableFactory()
    PlanMaintenanceConsommable.objects.create(
        plan_maintenance=plan,
        consommable=old_consommable,
        quantite_necessaire=1,
    )
    new_consommable = ConsommableFactory()

    changes_payload = {
        "planMaintenance.nom": {"ancienne": "Plan initial", "nouvelle": "Plan via changes"},
        "planMaintenance.necessitePermisFeu": {"ancienne": False, "nouvelle": True},
        "planMaintenance.consommables": {
            "ancienne": [{"consommable_id": old_consommable.id, "quantite": 1}],
            "nouvelle": [{"consommable_id": new_consommable.id, "quantite": 4}],
        },
    }

    view = PlanMaintenanceViewSet.as_view({"put": "update"})
    request = api_factory.put(
        f"/api/maintenance/plans-maintenance/{plan.pk}/",
        {"changes": json.dumps(changes_payload)},
        format="multipart",
    )

    response = view(request, pk=plan.pk)
    plan.refresh_from_db()

    assert response.status_code == 200
    assert plan.nom == "Plan via changes"
    assert plan.necessitePermisFeu is True

    assocs = list(
        PlanMaintenanceConsommable.objects.filter(plan_maintenance=plan).values(
            "consommable_id", "quantite_necessaire"
        )
    )
    assert assocs == [{"consommable_id": new_consommable.id, "quantite_necessaire": 4}]


@pytest.mark.django_db
def test_should_update_declenchement_with_seuil_payload(api_factory):
    compteur_old = CompteurFactory()
    compteur_new = CompteurFactory(equipement=compteur_old.equipement)
    plan = PlanMaintenanceFactory(equipement=compteur_old.equipement)
    declenchement = Declencher.objects.create(
        planMaintenance=plan,
        compteur=compteur_old,
        derniereIntervention=10,
        prochaineMaintenance=100,
        ecartInterventions=20,
        estGlissant=False,
    )

    seuil_payload = {
        "derniereIntervention": 12,
        "prochaineMaintenance": 180,
        "ecartInterventions": 30,
        "estGlissant": True,
        "compteurId": compteur_new.id,
    }

    view = PlanMaintenanceViewSet.as_view({"put": "update"})
    request = api_factory.put(
        f"/api/maintenance/plans-maintenance/{plan.pk}/",
        {"seuil": json.dumps(seuil_payload)},
        format="multipart",
    )

    response = view(request, pk=plan.pk)
    declenchement.refresh_from_db()

    assert response.status_code == 200
    assert declenchement.derniereIntervention == 12
    assert declenchement.prochaineMaintenance == 180
    assert declenchement.ecartInterventions == 30
    assert declenchement.estGlissant is True
    assert declenchement.compteur_id == compteur_new.id


@pytest.mark.django_db
def test_should_create_document_association_on_update_with_uploaded_file(api_factory):
    plan = PlanMaintenanceFactory()
    type_document = TypeDocument.objects.create(nomTypeDocument="Notice")

    seuil_payload = {
        "planMaintenance": {
            "documents": [
                {
                    "nomDocument": "Document MAJ",
                    "typeDocument_id": type_document.id,
                }
            ]
        }
    }

    view = PlanMaintenanceViewSet.as_view({"put": "update"})
    request = api_factory.put(
        f"/api/maintenance/plans-maintenance/{plan.pk}/",
        {
            "seuil": json.dumps(seuil_payload),
            "documents": [SimpleUploadedFile("plan.txt", b"abc", content_type="text/plain")],
        },
        format="multipart",
    )

    response = view(request, pk=plan.pk)

    assert response.status_code == 200
    assert PlanMaintenanceDocument.objects.filter(plan_maintenance=plan).count() == 1


@pytest.mark.django_db
def test_should_update_even_when_changes_json_is_invalid(api_factory):
    plan = PlanMaintenanceFactory(nom="Initial")

    view = PlanMaintenanceViewSet.as_view({"put": "update"})
    request = api_factory.put(
        f"/api/maintenance/plans-maintenance/{plan.pk}/",
        {"nom": "Apres", "changes": "{invalid"},
        format="multipart",
    )

    response = view(request, pk=plan.pk)
    plan.refresh_from_db()

    assert response.status_code == 200
    assert plan.nom == "Apres"


@pytest.mark.django_db
def test_should_ignore_invalid_seuil_json_in_update(api_factory):
    plan = PlanMaintenanceFactory(commentaire="Avant")

    view = PlanMaintenanceViewSet.as_view({"put": "update"})
    request = api_factory.put(
        f"/api/maintenance/plans-maintenance/{plan.pk}/",
        {"commentaire": "Apres", "seuil": "{invalid"},
        format="multipart",
    )

    response = view(request, pk=plan.pk)
    plan.refresh_from_db()

    assert response.status_code == 200
    assert plan.commentaire == "Apres"
