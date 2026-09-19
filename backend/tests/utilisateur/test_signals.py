import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from tests.factories import RoleFactory, UtilisateurFactory
from utilisateur.middleware import set_thread_user
from utilisateur.models import Log
from utilisateur.signals import (
    capture_old_state,
    get_safe_app_user,
    log_delete,
    log_save,
    make_serializable,
)


@pytest.mark.django_db
def test_make_serializable_handles_common_types():
    role = RoleFactory()
    payload = {
        "decimal": Decimal("12.34"),
        "date": datetime.date(2026, 3, 17),
        "datetime": datetime.datetime(2026, 3, 17, 10, 30, 0),
        "list": [Decimal("1.5"), role],
    }

    serialized = make_serializable(payload)

    assert serialized["decimal"] == "12.34"
    assert serialized["date"] == "2026-03-17"
    assert serialized["datetime"].startswith("2026-03-17T10:30:00")
    assert serialized["list"][0] == "1.5"
    assert serialized["list"][1] == role.pk


@pytest.mark.django_db
def test_make_serializable_handles_field_file_values():
    user = UtilisateurFactory(
        photoProfil=SimpleUploadedFile("avatar.txt", b"abc", content_type="text/plain")
    )

    serialized = make_serializable(user.photoProfil)

    assert "utilisateur_photos/" in serialized
    assert serialized.endswith(".txt")


@pytest.mark.django_db
def test_get_safe_app_user_returns_none_for_invalid_inputs():
    assert get_safe_app_user(None) is None
    assert get_safe_app_user("not-a-user") is None

    unsaved_user = UtilisateurFactory.build()
    assert get_safe_app_user(unsaved_user) is None


@pytest.mark.django_db
def test_get_safe_app_user_returns_none_for_deleted_user():
    from unittest.mock import patch

    user = UtilisateurFactory()

    with patch("utilisateur.signals.Utilisateur.objects.filter") as mock_filter:
        mock_filter.return_value.exists.return_value = False
        assert get_safe_app_user(user) is None


@pytest.mark.django_db
def test_log_save_create_creates_log_entry():
    Log.objects.all().delete()

    role = RoleFactory(nomRole="Technicien")

    entry = Log.objects.get(type="création", nomTable="gimao_role")
    assert entry.idCible["id"] == role.pk
    assert entry.champsModifies["nomRole"]["nouveau"] == "Technicien"


@pytest.mark.django_db
def test_log_save_update_tracks_changed_fields():
    Log.objects.all().delete()
    role = RoleFactory(nomRole="Avant")

    role.nomRole = "Apres"
    role.save()

    update_entry = Log.objects.filter(type="modification", nomTable="gimao_role").latest("date")
    assert update_entry.champsModifies["nomRole"]["ancien"] == "Avant"
    assert update_entry.champsModifies["nomRole"]["nouveau"] == "Apres"


@pytest.mark.django_db
def test_log_save_update_without_changes_creates_no_modification_log():
    Log.objects.all().delete()
    role = RoleFactory(nomRole="Stable")

    before_count = Log.objects.filter(type="modification", nomTable="gimao_role").count()
    role.save()
    after_count = Log.objects.filter(type="modification", nomTable="gimao_role").count()

    assert before_count == after_count


@pytest.mark.django_db
def test_log_save_uses_thread_user_when_available():
    Log.objects.all().delete()
    actor = UtilisateurFactory()

    set_thread_user(actor)
    try:
        role = RoleFactory(nomRole="RoleWithActor")
    finally:
        set_thread_user(None)

    entry = Log.objects.filter(type="création", nomTable="gimao_role").latest("date")
    assert entry.idCible["id"] == role.pk
    assert entry.utilisateur_id == actor.pk


@pytest.mark.django_db
def test_log_delete_creates_suppression_entry():
    Log.objects.all().delete()
    role = RoleFactory(nomRole="A supprimer")

    role.delete()

    delete_entry = Log.objects.filter(type="suppression", nomTable="gimao_role").latest("date")
    assert delete_entry.champsModifies == {"deleted": True}
    assert delete_entry.idCible["id"] is not None


@pytest.mark.django_db
def test_log_model_is_ignored_by_signals_to_avoid_recursion():
    Log.objects.all().delete()

    Log.objects.create(
        type="manuel",
        nomTable="manual_table",
        idCible={"id": 1},
        champsModifies={"x": "y"},
        utilisateur=None,
    )

    assert Log.objects.count() == 1


@pytest.mark.django_db
def test_log_save_fallbacks_to_request_user_utilisateur_when_no_thread_user():
    Log.objects.all().delete()
    app_user = UtilisateurFactory()

    request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True, utilisateur=app_user))

    with patch("utilisateur.middleware.get_current_request", return_value=request):
        role = RoleFactory(nomRole="RoleFallbackUtilisateur")

    entry = Log.objects.filter(type="création", nomTable="gimao_role").latest("date")
    assert entry.idCible["id"] == role.pk
    assert entry.utilisateur_id == app_user.pk


@pytest.mark.django_db
def test_log_save_fallbacks_to_request_user_username_mapping_when_no_utilisateur_attr():
    Log.objects.all().delete()
    app_user = UtilisateurFactory(nomUtilisateur="mapped_signals_user")

    request = SimpleNamespace(
        user=SimpleNamespace(is_authenticated=True, username="mapped_signals_user")
    )

    with patch("utilisateur.middleware.get_current_request", return_value=request):
        role = RoleFactory(nomRole="RoleFallbackUsername")

    entry = Log.objects.filter(type="création", nomTable="gimao_role").latest("date")
    assert entry.idCible["id"] == role.pk
    assert entry.utilisateur_id == app_user.pk


@pytest.mark.django_db
def test_log_delete_uses_username_mapping_when_authenticated_user_has_no_utilisateur_attr():
    Log.objects.all().delete()
    app_user = UtilisateurFactory(nomUtilisateur="mapped_delete_user")
    role_to_delete = RoleFactory(nomRole="RoleDeleteFallback")

    django_user = SimpleNamespace(is_authenticated=True, username="mapped_delete_user")

    with patch("utilisateur.signals.get_current_user", return_value=django_user):
        role_to_delete.delete()

    entry = Log.objects.filter(type="suppression", nomTable="gimao_role").latest("date")
    assert entry.utilisateur_id == app_user.pk


@pytest.mark.django_db
def test_capture_old_state_ignores_missing_instance_without_crashing():
    role = RoleFactory.build()
    role.pk = 999999

    capture_old_state(RoleFactory._meta.model, role)

    assert not hasattr(role, "_old_state")


@pytest.mark.django_db
def test_log_save_fallback_request_errors_are_ignored():
    role = RoleFactory.build(nomRole="NoCrash")
    role.pk = 1234
    role._meta = RoleFactory._meta.model._meta

    with patch("utilisateur.middleware.get_current_request", side_effect=RuntimeError("boom")):
        with patch("utilisateur.signals.Log.objects.create") as mock_create:
            log_save(RoleFactory._meta.model, role, created=True)

    assert mock_create.called


@pytest.mark.django_db
def test_log_save_does_not_crash_when_log_creation_fails():
    role = RoleFactory()

    with patch("utilisateur.signals.Log.objects.create", side_effect=RuntimeError("db fail")):
        log_save(RoleFactory._meta.model, role, created=False)


@pytest.mark.django_db
def test_log_delete_does_not_crash_when_log_creation_fails():
    role = RoleFactory()

    with patch("utilisateur.signals.Log.objects.create", side_effect=RuntimeError("db fail")):
        log_delete(RoleFactory._meta.model, role)
