import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from donnees.api.serializers import (
    DocumentSerializer,
    FabricantSerializer,
    FournisseurSerializer,
    LieuDetailSerializer,
)
from donnees.models import Adresse, Document, Fabricant, Fournisseur, Lieu, TypeDocument


@pytest.mark.django_db
def test_should_serialize_lieu_parent_children_and_hierarchy():
    root = Lieu.objects.create(nomLieu="Site", typeLieu="SITE")
    parent = Lieu.objects.create(nomLieu="Atelier", typeLieu="BATIMENT", lieuParent=root)
    child = Lieu.objects.create(nomLieu="Zone A", typeLieu="ZONE", lieuParent=parent)

    data = LieuDetailSerializer(parent).data

    assert data["lieuParent"] == {
        "id": root.id,
        "nomLieu": "Site",
        "typeLieu": "SITE",
    }
    assert data["sous_lieux"] == [{"id": child.id, "nomLieu": "Zone A", "typeLieu": "ZONE"}]
    assert data["hierarchie_complete"] == [{"id": root.id, "nomLieu": "Site", "typeLieu": "SITE"}]


@pytest.mark.django_db
def test_should_return_none_for_lieu_parent_and_empty_hierarchy_when_no_parent():
    leaf = Lieu.objects.create(nomLieu="Isolé", typeLieu="ZONE")

    data = LieuDetailSerializer(leaf).data

    assert data["lieuParent"] is None
    assert data["hierarchie_complete"] == []


@pytest.mark.django_db
def test_should_require_typedocument_or_typedocument_id_for_document_serializer():
    upload = SimpleUploadedFile("doc.pdf", b"file-content", content_type="application/pdf")

    serializer = DocumentSerializer(data={"cheminAcces": upload})

    assert serializer.is_valid() is False
    assert "typeDocument" in serializer.errors


@pytest.mark.django_db
def test_should_reject_invalid_typedocument_id_alias():
    upload = SimpleUploadedFile("doc.pdf", b"file-content", content_type="application/pdf")

    serializer = DocumentSerializer(data={"cheminAcces": upload, "typeDocument_id": 999999})

    assert serializer.is_valid() is False
    assert "typeDocument_id" in serializer.errors


@pytest.mark.django_db
def test_should_create_document_with_typedocument_id_alias_and_default_name_from_file():
    type_doc = TypeDocument.objects.create(nomTypeDocument="PDF")
    upload = SimpleUploadedFile("manuel.pdf", b"file-content", content_type="application/pdf")

    serializer = DocumentSerializer(
        data={"cheminAcces": upload, "typeDocument_id": type_doc.id, "nomDocument": ""}
    )

    assert serializer.is_valid(), serializer.errors
    document = serializer.save()

    assert document.typeDocument_id == type_doc.id
    assert document.nomDocument == "manuel.pdf"


@pytest.mark.django_db
def test_should_serialize_document_compat_fields():
    type_doc = TypeDocument.objects.create(nomTypeDocument="Notice")
    document = Document.objects.create(
        nomDocument="Notice machine",
        cheminAcces=SimpleUploadedFile("notice.txt", b"abc", content_type="text/plain"),
        typeDocument=type_doc,
    )

    data = DocumentSerializer(document).data

    assert data["titre"] == "Notice machine"
    assert data["type"] == type_doc.id
    assert data["type_nom"] == "Notice"
    assert data["path"].startswith("documents/")
    assert data["path"].endswith(".txt")


@pytest.mark.django_db
def test_should_serialize_fabricant_and_fournisseur_with_nested_adresse():
    adresse = Adresse.objects.create(
        numero="10",
        rue="Rue des Tests",
        ville="Paris",
        code_postal="75000",
        pays="France",
    )
    fabricant = Fabricant.objects.create(nom="Fabricant X", adresse=adresse)
    fournisseur = Fournisseur.objects.create(nom="Fournisseur Y", adresse=adresse)

    fabricant_data = FabricantSerializer(fabricant).data
    fournisseur_data = FournisseurSerializer(fournisseur).data

    assert fabricant_data["adresse"]["id"] == adresse.id
    assert fournisseur_data["adresse"]["id"] == adresse.id
    assert fabricant_data["nom"] == "Fabricant X"
    assert fournisseur_data["nom"] == "Fournisseur Y"
