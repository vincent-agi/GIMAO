"""Tests du seed RBAC du domaine véhicule (TUS-006).

Vérifie que ``create_initial_data`` crée bien le module ``veh``, les
permissions ``veh:*`` avec la bonne hiérarchie parent/enfant, et les
rattache aux rôles pertinents. Note (cf. BILAN_EXISTANT.md §4.10) :
``REST_FRAMEWORK`` n'a aucune classe de permission par défaut et aucun
ViewSet du projet ne fait actuellement respecter ``Module``/``Permission``
côté serveur — ce catalogue reste, pour l'instant, une donnée exploitée par
le frontend (menus, boutons), comme pour toutes les autres entités
existantes (eq, bt, di...). Ce test couvre donc l'intégrité du seed de
données, pas une éventuelle application (absente) au niveau de l'API.
"""

import pytest

from tasks import perms_data
from tasks.create_initial_data import create_initial_data
from utilisateur.models import Module, Permission, Role, RolePermission

pytestmark = pytest.mark.django_db


class TestVehiculePermsData:
    def test_veh_permissions_declared_with_view_list_as_root_parent(self):
        assert perms_data.perms['veh:viewList'][2] is None
        for code in ['veh:viewDetail', 'veh:create', 'veh:edit', 'veh:delete', 'veh:export', 'veh:archive']:
            assert code in perms_data.perms

    def test_veh_create_depends_on_view_list_and_edit_depends_on_view_detail(self):
        assert perms_data.perms['veh:create'][2] == 'veh:viewList'
        assert perms_data.perms['veh:edit'][2] == 'veh:viewDetail'
        assert perms_data.perms['veh:delete'][2] == 'veh:viewDetail'

    def test_responsable_gmao_gets_all_veh_permissions_by_default(self):
        veh_perms = [p for p in perms_data.perms if p.startswith('veh:')]
        assert set(veh_perms).issubset(set(perms_data.perms_map['Responsable GMAO']))

    def test_technicien_prod_gets_read_only_veh_access(self):
        techn_perms = perms_data.perms_map['Technicien prod']
        assert 'veh:viewList' in techn_perms
        assert 'veh:viewDetail' in techn_perms
        assert 'veh:create' not in techn_perms
        assert 'veh:delete' not in techn_perms


class TestCreateInitialDataSeedsVehiculeModule:
    def test_should_create_veh_module(self):
        create_initial_data()

        module = Module.objects.get(code='veh')
        assert module.nom == 'Véhicules'

    def test_should_create_veh_permissions_linked_to_veh_module(self):
        create_initial_data()

        perm = Permission.objects.get(nomPermission='veh:viewDetail')
        assert perm.module.code == 'veh'
        assert perm.parent.nomPermission == 'veh:viewList'

    def test_should_attach_veh_permissions_to_responsable_gmao_role(self):
        create_initial_data()

        role = Role.objects.get(nomRole='Responsable GMAO')
        perm = Permission.objects.get(nomPermission='veh:create')

        assert RolePermission.objects.filter(role=role, permission=perm).exists()

    def test_should_be_idempotent_when_run_twice(self):
        create_initial_data()
        create_initial_data()

        assert Module.objects.filter(code='veh').count() == 1
        assert Permission.objects.filter(nomPermission='veh:viewList').count() == 1
