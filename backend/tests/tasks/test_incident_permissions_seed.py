"""Tests du seed RBAC des domaines incident/sinistre/obd (TUS-023).

Même remarque que pour ``test_vehicule_permissions_seed.py`` (BILAN_EXISTANT.md
§4.10) : ce catalogue reste une donnée consommée par le frontend, aucun
ViewSet du projet ne fait respecter Module/Permission côté serveur
aujourd'hui.
"""

import pytest

from tasks import perms_data
from tasks.create_initial_data import create_initial_data
from utilisateur.models import Module, Permission, Role, RolePermission

pytestmark = pytest.mark.django_db


class TestIncidentSinistreObdPermsData:
    def test_incident_and_sinistre_and_obd_permissions_declared_with_view_list_as_root(self):
        for prefix in ("incident", "sinistre", "obd"):
            assert perms_data.perms[f"{prefix}:viewList"][2] is None
            assert perms_data.perms[f"{prefix}:viewDetail"][2] == f"{prefix}:viewList"
            assert perms_data.perms[f"{prefix}:create"][2] == f"{prefix}:viewList"

    def test_responsable_gmao_gets_all_incident_sinistre_obd_permissions_by_default(self):
        domain_perms = [
            p for p in perms_data.perms if p.startswith(("incident:", "sinistre:", "obd:"))
        ]
        assert set(domain_perms).issubset(set(perms_data.perms_map["Responsable GMAO"]))

    def test_operateur_prod_can_declare_incident_and_sinistre_but_not_view_sinistre_list(self):
        operateur_perms = perms_data.perms_map["Opérateur prod"]

        assert "incident:create" in operateur_perms
        assert "sinistre:create" in operateur_perms
        assert "sinistre:viewList" not in operateur_perms


class TestCreateInitialDataSeedsIncidentModules:
    def test_should_create_incident_sinistre_obd_modules(self):
        create_initial_data()

        for code, nom in (
            ("incident", "Incidents véhicule"),
            ("sinistre", "Sinistres"),
            ("obd", "Diagnostic OBD"),
        ):
            module = Module.objects.get(code=code)
            assert module.nom == nom

    def test_should_link_incident_permissions_to_incident_module(self):
        create_initial_data()

        perm = Permission.objects.get(nomPermission="incident:viewDetail")
        assert perm.module.code == "incident"
        assert perm.parent.nomPermission == "incident:viewList"

    def test_should_attach_obd_create_to_technicien_prod_role(self):
        create_initial_data()

        role = Role.objects.get(nomRole="Technicien prod")
        perm = Permission.objects.get(nomPermission="obd:create")

        assert RolePermission.objects.filter(role=role, permission=perm).exists()

    def test_should_be_idempotent_when_run_twice(self):
        create_initial_data()
        create_initial_data()

        assert Module.objects.filter(code="sinistre").count() == 1
        assert Permission.objects.filter(nomPermission="obd:viewList").count() == 1
