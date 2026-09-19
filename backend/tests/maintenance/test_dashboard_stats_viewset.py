import pytest
from rest_framework.test import APIRequestFactory

from maintenance.api.viewsets import DashboardStatsViewset
from tests.factories import (
    BonTravailFactory,
    DemandeInterventionFactory,
    PermissionFactory,
    UtilisateurFactory,
)
from utilisateur.models import RolePermission, UtilisateurPermission


@pytest.fixture
def api_factory():
    return APIRequestFactory()


@pytest.mark.django_db
def test_should_return_404_when_user_is_not_found(api_factory):
    view = DashboardStatsViewset.as_view({"get": "list"})
    request = api_factory.get("/api/maintenance/stats/", {"userId": 999999})

    response = view(request)

    assert response.status_code == 404
    assert response.data["detail"] == "Utilisateur not found"


@pytest.mark.django_db
def test_should_return_400_when_user_has_no_dash_permissions(api_factory):
    user = UtilisateurFactory()

    view = DashboardStatsViewset.as_view({"get": "list"})
    request = api_factory.get("/api/maintenance/stats/", {"userId": user.pk})

    response = view(request)

    assert response.status_code == 400
    assert response.data["detail"] == "Invalid role"


@pytest.mark.django_db
def test_should_return_full_stats_when_user_has_dash_stats_full_permission(api_factory):
    user = UtilisateurFactory()
    permission = PermissionFactory(nomPermission="dash:stats.full")
    RolePermission.objects.create(role=user.role, permission=permission)

    DemandeInterventionFactory(statut="EN_ATTENTE", archive=False)
    DemandeInterventionFactory(statut="ACCEPTEE", archive=False)
    DemandeInterventionFactory(statut="TRANSFORMEE", archive=False)

    BonTravailFactory(statut="EN_COURS", archive=False)
    BonTravailFactory(statut="EN_RETARD", archive=False)
    BonTravailFactory(statut="CLOTURE", archive=False)

    view = DashboardStatsViewset.as_view({"get": "list"})
    request = api_factory.get("/api/maintenance/stats/", {"userId": user.pk})

    response = view(request)

    assert response.status_code == 200
    stats = response.data["stats"]
    labels = {entry["label"] for entry in stats}
    assert "Nombre de DI" in labels
    assert "Nombre de BT" in labels


@pytest.mark.django_db
def test_should_return_bt_stats_when_user_has_dash_stats_bt_permission(api_factory):
    user = UtilisateurFactory()
    permission = PermissionFactory(nomPermission="dash:stats.bt")
    RolePermission.objects.create(role=user.role, permission=permission)

    bt_open = BonTravailFactory(statut="EN_COURS", archive=False)
    bt_open.utilisateur_assigne.add(user)
    bt_done = BonTravailFactory(statut="TERMINE", archive=False)
    bt_done.utilisateur_assigne.add(user)

    view = DashboardStatsViewset.as_view({"get": "list"})
    request = api_factory.get("/api/maintenance/stats/", {"userId": user.pk})

    response = view(request)

    assert response.status_code == 200
    stats = {entry["label"]: entry["value"] for entry in response.data["stats"]}
    assert stats["Vos BT"] == 2
    assert stats["Vos BT en cours"] == 1
    assert stats["Vos BT terminés"] == 1


@pytest.mark.django_db
def test_should_use_custom_dash_permission_before_role_permission(api_factory):
    user = UtilisateurFactory()
    role_perm = PermissionFactory(nomPermission="dash:stats.full")
    custom_perm = PermissionFactory(nomPermission="dash:stats.di")

    RolePermission.objects.create(role=user.role, permission=role_perm)
    UtilisateurPermission.objects.create(utilisateur=user, permission=custom_perm)

    DemandeInterventionFactory(utilisateur=user, statut="EN_ATTENTE", archive=False)
    DemandeInterventionFactory(utilisateur=user, statut="ACCEPTEE", archive=False)
    BonTravailFactory(statut="EN_COURS", archive=False)

    view = DashboardStatsViewset.as_view({"get": "list"})
    request = api_factory.get("/api/maintenance/stats/", {"userId": user.pk})

    response = view(request)

    assert response.status_code == 200
    labels = [entry["label"] for entry in response.data["stats"]]
    assert "Vos DI" in labels
    assert "Nombre de BT" not in labels
