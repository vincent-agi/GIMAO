import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from donnees.models import Document, TypeDocument
from equipement.models import StatutEquipement
from maintenance.api.viewsets import DemandeInterventionViewSet
from maintenance.models import BonTravail
from tests.factories import DemandeInterventionFactory, EquipementFactory, UtilisateurFactory


@pytest.fixture
def api_factory():
    return APIRequestFactory()


@pytest.mark.django_db
def test_should_return_400_when_par_equipement_without_param(api_factory):
    view = DemandeInterventionViewSet.as_view({"get": "par_equipement"})
    request = api_factory.get("/api/maintenance/demandes-intervention/par_equipement/")

    response = view(request)

    assert response.status_code == 400
    assert "equipement_id" in response.data["error"]


@pytest.mark.django_db
def test_should_filter_demandes_by_equipement(api_factory):
    equipement_target = EquipementFactory()
    equipement_other = EquipementFactory()
    di_target = DemandeInterventionFactory(equipement=equipement_target)
    DemandeInterventionFactory(equipement=equipement_other)

    view = DemandeInterventionViewSet.as_view({"get": "par_equipement"})
    request = api_factory.get(
        "/api/maintenance/demandes-intervention/par_equipement/",
        {"equipement_id": equipement_target.pk},
    )

    response = view(request)

    assert response.status_code == 200
    ids = [item["id"] for item in response.data["results"]]
    assert ids == [di_target.id]


@pytest.mark.django_db
def test_should_return_400_when_par_utilisateur_without_param(api_factory):
    view = DemandeInterventionViewSet.as_view({"get": "par_utilisateur"})
    request = api_factory.get("/api/maintenance/demandes-intervention/par_utilisateur/")

    response = view(request)

    assert response.status_code == 400
    assert "utilisateur_id" in response.data["error"]


@pytest.mark.django_db
def test_should_filter_demandes_by_utilisateur(api_factory):
    user_target = UtilisateurFactory()
    user_other = UtilisateurFactory()
    di_target = DemandeInterventionFactory(utilisateur=user_target)
    DemandeInterventionFactory(utilisateur=user_other)

    view = DemandeInterventionViewSet.as_view({"get": "par_utilisateur"})
    request = api_factory.get(
        "/api/maintenance/demandes-intervention/par_utilisateur/",
        {"utilisateur_id": user_target.pk},
    )

    response = view(request)

    assert response.status_code == 200
    ids = [item["id"] for item in response.data["results"]]
    assert ids == [di_target.id]


@pytest.mark.django_db
def test_should_update_demande_status_via_update_status_action(api_factory):
    demande = DemandeInterventionFactory(statut="EN_ATTENTE")
    before_change = demande.date_changementStatut

    view = DemandeInterventionViewSet.as_view({"patch": "updateStatus"})
    request = api_factory.patch(
        f"/api/maintenance/demandes-intervention/{demande.pk}/updateStatus/",
        {"statut": "ACCEPTEE"},
        format="json",
    )

    response = view(request, pk=demande.pk)
    demande.refresh_from_db()

    assert response.status_code == 200
    assert demande.statut == "ACCEPTEE"
    assert demande.date_changementStatut >= before_change


@pytest.mark.django_db
def test_should_transform_demande_to_bon_travail(api_factory):
    demande = DemandeInterventionFactory(statut="EN_ATTENTE")
    responsable = UtilisateurFactory()

    view = DemandeInterventionViewSet.as_view({"post": "transform_to_bon_travail"})
    request = api_factory.post(
        f"/api/maintenance/demandes-intervention/{demande.pk}/transform_to_bon_travail/",
        {"responsable": responsable.pk},
        format="json",
    )

    response = view(request, pk=demande.pk)
    demande.refresh_from_db()

    assert response.status_code == 200
    assert demande.statut == "TRANSFORMEE"

    bt = BonTravail.objects.get(demande_intervention=demande)
    assert bt.type == "CORRECTIF"
    assert bt.responsable_id == responsable.pk


@pytest.mark.django_db
def test_should_return_400_when_delink_document_without_document_id(api_factory):
    demande = DemandeInterventionFactory()

    view = DemandeInterventionViewSet.as_view({"patch": "delink_document"})
    request = api_factory.patch(
        f"/api/maintenance/demandes-intervention/{demande.pk}/delink_document/",
        {},
        format="json",
    )

    response = view(request, pk=demande.pk)

    assert response.status_code == 400
    assert "document_id" in response.data["error"]


@pytest.mark.django_db
def test_should_return_404_when_delink_document_not_linked(api_factory):
    demande = DemandeInterventionFactory()

    view = DemandeInterventionViewSet.as_view({"patch": "delink_document"})
    request = api_factory.patch(
        f"/api/maintenance/demandes-intervention/{demande.pk}/delink_document/",
        {"document_id": 999999},
        format="json",
    )

    response = view(request, pk=demande.pk)

    assert response.status_code == 404
    assert "n'est pas lié" in response.data["error"]


@pytest.mark.django_db
def test_should_create_demande_with_document(api_factory):
    utilisateur = UtilisateurFactory()
    equipement = EquipementFactory()
    type_document = TypeDocument.objects.create(nomTypeDocument="Notice")

    view = DemandeInterventionViewSet.as_view({"post": "create"})
    request = api_factory.post(
        "/api/maintenance/demandes-intervention/",
        {
            "nom": "DI creation",
            "commentaire": "Commentaire",
            "statut_suppose": "EN_FONCTIONNEMENT",
            "equipement_id": str(equipement.pk),
            "utilisateur_id": str(utilisateur.pk),
            "documents": json.dumps(
                [
                    {
                        "nomDocument": "Doc DI",
                        "typeDocument_id": type_document.pk,
                    }
                ]
            ),
            "document_0": SimpleUploadedFile("doc_di.txt", b"abc", content_type="text/plain"),
        },
        format="multipart",
    )

    response = view(request)

    assert response.status_code == 201
    demande = DemandeInterventionFactory._meta.model.objects.get(pk=response.data["id"])
    assert demande.statut == "EN_ATTENTE"
    assert demande.documents.count() == 1


@pytest.mark.django_db
def test_should_return_400_when_create_without_identified_user(api_factory):
    equipement = EquipementFactory()

    view = DemandeInterventionViewSet.as_view({"post": "create"})
    request = api_factory.post(
        "/api/maintenance/demandes-intervention/",
        {
            "nom": "DI sans user",
            "statut_suppose": "EN_FONCTIONNEMENT",
            "equipement_id": str(equipement.pk),
        },
        format="json",
    )

    response = view(request)

    assert response.status_code == 400
    assert "utilisateur_id" in response.data


@pytest.mark.django_db
def test_should_return_400_when_create_with_invalid_equipement(api_factory):
    utilisateur = UtilisateurFactory()

    view = DemandeInterventionViewSet.as_view({"post": "create"})
    request = api_factory.post(
        "/api/maintenance/demandes-intervention/",
        {
            "nom": "DI equipement invalide",
            "statut_suppose": "EN_FONCTIONNEMENT",
            "utilisateur_id": utilisateur.pk,
            "equipement_id": 999999,
        },
        format="json",
    )

    response = view(request)

    assert response.status_code == 400
    assert "equipement_id" in response.data


@pytest.mark.django_db
def test_should_return_400_when_create_document_missing_file(api_factory):
    utilisateur = UtilisateurFactory()
    equipement = EquipementFactory()
    type_document = TypeDocument.objects.create(nomTypeDocument="Notice")

    view = DemandeInterventionViewSet.as_view({"post": "create"})
    request = api_factory.post(
        "/api/maintenance/demandes-intervention/",
        {
            "nom": "DI doc invalide",
            "commentaire": "Commentaire",
            "statut_suppose": "EN_FONCTIONNEMENT",
            "equipement_id": str(equipement.pk),
            "utilisateur_id": str(utilisateur.pk),
            "documents": json.dumps(
                [
                    {
                        "nomDocument": "Doc sans fichier",
                        "typeDocument_id": type_document.pk,
                    }
                ]
            ),
        },
        format="multipart",
    )

    response = view(request)

    assert response.status_code == 400
    assert "fichier manquant" in str(response.data)


@pytest.mark.django_db
def test_should_add_existing_document_to_demande(api_factory):
    demande = DemandeInterventionFactory()
    type_document = TypeDocument.objects.create(nomTypeDocument="Notice")
    document = Document.objects.create(
        nomDocument="Doc externe",
        cheminAcces=SimpleUploadedFile("ext.txt", b"abc", content_type="text/plain"),
        typeDocument=type_document,
    )

    view = DemandeInterventionViewSet.as_view({"post": "ajouter_document"})
    request = api_factory.post(
        f"/api/maintenance/demandes-intervention/{demande.pk}/ajouter_document/",
        {"document_id": document.pk},
        format="json",
    )

    response = view(request, pk=demande.pk)

    assert response.status_code == 200
    assert demande.documents.filter(pk=document.pk).exists()


@pytest.mark.django_db
def test_should_partial_update_demande_and_create_new_document(api_factory):
    demande = DemandeInterventionFactory(nom="Nom initial")
    type_document = TypeDocument.objects.create(nomTypeDocument="Notice")

    view = DemandeInterventionViewSet.as_view({"patch": "partial_update"})
    request = api_factory.patch(
        f"/api/maintenance/demandes-intervention/{demande.pk}/",
        {
            "nom": "Nom modifie",
            "documents": json.dumps(
                [
                    {
                        "nomDocument": "Doc nouveau",
                        "typeDocument_id": type_document.pk,
                    }
                ]
            ),
            "document_0": SimpleUploadedFile("new_doc.txt", b"abc", content_type="text/plain"),
        },
        format="multipart",
    )

    response = view(request, pk=demande.pk)
    demande.refresh_from_db()

    assert response.status_code == 200
    assert demande.nom == "Nom modifie"
    assert demande.documents.count() == 1


@pytest.mark.django_db
def test_should_partial_update_existing_document_metadata(api_factory):
    demande = DemandeInterventionFactory()
    type_doc_old = TypeDocument.objects.create(nomTypeDocument="Ancien")
    type_doc_new = TypeDocument.objects.create(nomTypeDocument="Nouveau")
    document = Document.objects.create(
        nomDocument="Doc initial",
        cheminAcces=SimpleUploadedFile("doc_init.txt", b"abc", content_type="text/plain"),
        typeDocument=type_doc_old,
    )
    demande.documents.add(document)

    view = DemandeInterventionViewSet.as_view({"patch": "partial_update"})
    request = api_factory.patch(
        f"/api/maintenance/demandes-intervention/{demande.pk}/",
        {
            "documents": json.dumps(
                [
                    {
                        "document_id": document.pk,
                        "nomDocument": "Doc modifie",
                        "typeDocument_id": type_doc_new.pk,
                    }
                ]
            ),
        },
        format="multipart",
    )

    response = view(request, pk=demande.pk)
    document.refresh_from_db()

    assert response.status_code == 200
    assert document.nomDocument == "Doc modifie"
    assert document.typeDocument_id == type_doc_new.pk


@pytest.mark.django_db
def test_should_create_statut_equipement_when_transform_with_status(api_factory):
    demande = DemandeInterventionFactory(statut="EN_ATTENTE")
    responsable = UtilisateurFactory()

    view = DemandeInterventionViewSet.as_view({"post": "transform_to_bon_travail"})
    request = api_factory.post(
        f"/api/maintenance/demandes-intervention/{demande.pk}/transform_to_bon_travail/",
        {"responsable": responsable.pk, "statut_equipement": "DEGRADE"},
        format="json",
    )

    response = view(request, pk=demande.pk)

    assert response.status_code == 200
    assert StatutEquipement.objects.filter(equipement=demande.equipement, statut="DEGRADE").exists()


@pytest.mark.django_db
def test_should_return_400_when_ajouter_document_without_document_id(api_factory):
    demande = DemandeInterventionFactory()

    view = DemandeInterventionViewSet.as_view({"post": "ajouter_document"})
    request = api_factory.post(
        f"/api/maintenance/demandes-intervention/{demande.pk}/ajouter_document/",
        {},
        format="json",
    )

    response = view(request, pk=demande.pk)

    assert response.status_code == 400
    assert "document_id" in response.data["error"]


@pytest.mark.django_db
def test_should_return_400_when_ajouter_document_with_non_integer_id(api_factory):
    demande = DemandeInterventionFactory()

    view = DemandeInterventionViewSet.as_view({"post": "ajouter_document"})
    request = api_factory.post(
        f"/api/maintenance/demandes-intervention/{demande.pk}/ajouter_document/",
        {"document_id": "abc"},
        format="json",
    )

    response = view(request, pk=demande.pk)

    assert response.status_code == 400
    assert "entier" in response.data["error"]


@pytest.mark.django_db
def test_should_return_400_when_ajouter_document_with_unknown_document(api_factory):
    demande = DemandeInterventionFactory()

    view = DemandeInterventionViewSet.as_view({"post": "ajouter_document"})
    request = api_factory.post(
        f"/api/maintenance/demandes-intervention/{demande.pk}/ajouter_document/",
        {"document_id": 999999},
        format="json",
    )

    response = view(request, pk=demande.pk)

    assert response.status_code == 400
    assert "introuvable" in response.data["error"]


@pytest.mark.django_db
def test_should_be_idempotent_when_ajouter_document_already_linked(api_factory):
    demande = DemandeInterventionFactory()
    type_document = TypeDocument.objects.create(nomTypeDocument="Notice")
    document = Document.objects.create(
        nomDocument="Doc lie",
        cheminAcces=SimpleUploadedFile("linked.txt", b"abc", content_type="text/plain"),
        typeDocument=type_document,
    )
    demande.documents.add(document)

    view = DemandeInterventionViewSet.as_view({"post": "ajouter_document"})
    request = api_factory.post(
        f"/api/maintenance/demandes-intervention/{demande.pk}/ajouter_document/",
        {"document_id": document.pk},
        format="json",
    )

    response = view(request, pk=demande.pk)

    assert response.status_code == 200
    assert demande.documents.filter(pk=document.pk).count() == 1


@pytest.mark.django_db
def test_should_return_400_when_partial_update_documents_format_is_invalid(api_factory):
    demande = DemandeInterventionFactory()

    view = DemandeInterventionViewSet.as_view({"patch": "partial_update"})
    request = api_factory.patch(
        f"/api/maintenance/demandes-intervention/{demande.pk}/",
        {"documents": json.dumps({"invalid": True})},
        format="json",
    )

    response = view(request, pk=demande.pk)

    assert response.status_code == 400
    assert "documents" in response.data


@pytest.mark.django_db
def test_should_return_400_when_partial_update_document_id_is_invalid(api_factory):
    demande = DemandeInterventionFactory()

    view = DemandeInterventionViewSet.as_view({"patch": "partial_update"})
    request = api_factory.patch(
        f"/api/maintenance/demandes-intervention/{demande.pk}/",
        {
            "documents": json.dumps([{"document_id": "abc", "nomDocument": "X"}]),
        },
        format="json",
    )

    response = view(request, pk=demande.pk)

    assert response.status_code == 400
    assert "document_id invalide" in str(response.data)


@pytest.mark.django_db
def test_should_return_400_when_partial_update_document_id_not_found(api_factory):
    demande = DemandeInterventionFactory()

    view = DemandeInterventionViewSet.as_view({"patch": "partial_update"})
    request = api_factory.patch(
        f"/api/maintenance/demandes-intervention/{demande.pk}/",
        {
            "documents": json.dumps([{"document_id": 999999, "nomDocument": "X"}]),
        },
        format="json",
    )

    response = view(request, pk=demande.pk)

    assert response.status_code == 400
    assert "document introuvable" in str(response.data)


@pytest.mark.django_db
def test_should_return_400_when_partial_update_new_document_without_type(api_factory):
    demande = DemandeInterventionFactory()

    view = DemandeInterventionViewSet.as_view({"patch": "partial_update"})
    request = api_factory.patch(
        f"/api/maintenance/demandes-intervention/{demande.pk}/",
        {
            "documents": json.dumps([{"nomDocument": "Sans type"}]),
            "document_0": SimpleUploadedFile("x.txt", b"abc", content_type="text/plain"),
        },
        format="multipart",
    )

    response = view(request, pk=demande.pk)

    assert response.status_code == 400
    assert "typeDocument_id requis" in str(response.data)


@pytest.mark.django_db
def test_should_return_400_when_partial_update_new_document_without_file(api_factory):
    demande = DemandeInterventionFactory()
    type_document = TypeDocument.objects.create(nomTypeDocument="Notice")

    view = DemandeInterventionViewSet.as_view({"patch": "partial_update"})
    request = api_factory.patch(
        f"/api/maintenance/demandes-intervention/{demande.pk}/",
        {
            "documents": json.dumps(
                [{"nomDocument": "Sans fichier", "typeDocument_id": type_document.pk}]
            ),
        },
        format="json",
    )

    response = view(request, pk=demande.pk)

    assert response.status_code == 400
    assert "fichier manquant" in str(response.data)
