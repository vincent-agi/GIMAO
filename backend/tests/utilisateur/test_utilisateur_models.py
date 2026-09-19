import os

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone

from tests.factories import RoleFactory, UtilisateurFactory
from utilisateur.models import Permission, RolePermission, UtilisateurPermission


@pytest.mark.django_db
def test_should_clear_password_when_set_password_receives_empty_value():
    user = UtilisateurFactory()
    user.set_password("")

    assert user.motDePasse is None
    assert user.has_usable_password() is False


@pytest.mark.django_db
def test_should_report_usable_password_after_hashing_password():
    user = UtilisateurFactory()
    user.set_password("secret")

    assert user.has_usable_password() is True


@pytest.mark.django_db
def test_should_detect_premiere_connexion_from_derniere_connexion_field():
    user = UtilisateurFactory(derniereConnexion=None)
    assert user.premiere_connexion() is True

    user.derniereConnexion = timezone.now()
    assert user.premiere_connexion() is False


@pytest.mark.django_db
def test_should_return_human_label_for_known_permission_code():
    permission = Permission.objects.create(nomPermission="bt:viewList")

    assert "bt:viewList" in str(permission)
    assert "Voir la liste des BT" in str(permission)


@pytest.mark.django_db
def test_should_fallback_to_permission_code_for_unknown_permission():
    permission = Permission.objects.create(nomPermission="custom:unknown")

    assert "custom:unknown" in str(permission)


@pytest.mark.django_db
def test_should_render_role_permission_and_utilisateur_permission_strings():
    role = RoleFactory(nomRole="Magasinier")
    user = UtilisateurFactory(role=role, nomUtilisateur="user_model_test")
    permission = Permission.objects.create(nomPermission="stock:view")

    role_permission = RolePermission.objects.create(role=role, permission=permission)
    utilisateur_permission = UtilisateurPermission.objects.create(
        utilisateur=user, permission=permission
    )

    assert "Magasinier - stock:view" in str(role_permission)
    assert "user_model_test - stock:view" in str(utilisateur_permission)


@pytest.mark.django_db
@override_settings(MEDIA_ROOT="/tmp/gimao_test_media")
def test_should_delete_old_photo_file_when_replaced():
    os.makedirs("/tmp/gimao_test_media", exist_ok=True)

    user = UtilisateurFactory(
        photoProfil=SimpleUploadedFile("old.txt", b"old-content", content_type="text/plain")
    )
    old_path = user.photoProfil.path
    assert os.path.exists(old_path)

    user.photoProfil = SimpleUploadedFile("new.txt", b"new-content", content_type="text/plain")
    user.save()

    assert os.path.exists(old_path) is False
    assert os.path.exists(user.photoProfil.path)


@pytest.mark.django_db
@override_settings(MEDIA_ROOT="/tmp/gimao_test_media")
def test_should_delete_photo_file_when_user_is_deleted():
    os.makedirs("/tmp/gimao_test_media", exist_ok=True)

    user = UtilisateurFactory(
        photoProfil=SimpleUploadedFile("to_delete.txt", b"data", content_type="text/plain")
    )
    file_path = user.photoProfil.path
    assert os.path.exists(file_path)

    user.delete()

    assert os.path.exists(file_path) is False
