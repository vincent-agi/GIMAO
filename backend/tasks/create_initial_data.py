from donnees.models import TypeDocument
from maintenance.models import TypePlanMaintenance
from utilisateur.models import Module, Permission, Role, RolePermission, Utilisateur

from . import perms_data


def create_initial_data():
    # Création des rôles par défaut
    roles = [
        "Responsable GMAO",
        "Technicien prod",
        "Technicien maintenance",
        "Magasinier",
        "Opérateur prod",
    ]
    for role_name in roles:
        role, _ = Role.objects.get_or_create(nomRole=role_name)
        if not role.estDefaut:
            role.estDefaut = True
            role.save()

    # Création des types de plans de maintenance par défaut
    types_plan_maintenance = ["Préventive systématique", "Préventive conditionnelle", "Corrective"]
    for type_name in types_plan_maintenance:
        TypePlanMaintenance.objects.get_or_create(libelle=type_name)

    # Création des types de documents par défaut
    types_document = [
        "Manuel d'utilisation",
        "Manuel de maintenance",
        "Notice technique",
        "Schéma technique",
        "Contrat de maintenance",
        "Garantie",
        "Procédure de maintenance",
        "Consigne de sécurité",
        "Rapport d'intervention",
        "Rapport de contrôle",
        "Certificat de conformité",
        "Devis / Facture",
    ]
    for doc_type in types_document:
        TypeDocument.objects.get_or_create(nomTypeDocument=doc_type)

    # Création des modules
    modules_data = {
        "di": "Demandes d'intervention",
        "bt": "Bons de travail",
        "eq": "Équipements",
        "cp": "Compteurs",
        "mp": "Maintenances préventives",
        "stock": "Stocks",
        "cons": "Consommables",
        "mag": "Magasins",
        "user": "Utilisateurs",
        "role": "Rôles",
        "loc": "Lieux",
        "sup": "Fournisseurs",
        "man": "Fabricants",
        "eqmod": "Modèles d'équipement",
        "veh": "Véhicules",
        "export": "Export",
        "menu": "Menu",
        "dash": "Dashboard",
    }
    modules = {}
    for code, nom in modules_data.items():
        module, _ = Module.objects.get_or_create(code=code, defaults={"nom": nom})
        modules[code] = module

    # Premier passage : créer/mettre à jour sans parent
    for perm_name, (description, perm_type, _parent) in perms_data.perms.items():
        module_code = perm_name.split(":")[0]
        module = modules.get(module_code)

        perm, _created = Permission.objects.get_or_create(nomPermission=perm_name)

        changed = False
        if perm.description != description:
            perm.description = description
            changed = True
        if perm.type != perm_type:
            perm.type = perm_type
            changed = True
        if module and perm.module != module:
            perm.module = module
            changed = True
        if changed:
            perm.save()

    # Deuxième passage : assigner ou effacer les parents
    for perm_name, (_description, _perm_type, parent_name) in perms_data.perms.items():
        perm = Permission.objects.get(nomPermission=perm_name)
        if parent_name:
            parent = Permission.objects.get(nomPermission=parent_name)
            if perm.parent != parent:
                perm.parent = parent
                perm.save()
        elif perm.parent is not None:
            perm.parent = None
            perm.save()

    # Assignation des permissions aux rôles
    for role_name, perm_list in perms_data.perms_map.items():
        role = Role.objects.get(nomRole=role_name)
        for perm_name in perm_list:
            perm = Permission.objects.get(nomPermission=perm_name)
            RolePermission.objects.get_or_create(role=role, permission=perm)

    # Création de l'utilisateur responsable APRÈS les permissions
    Utilisateur.objects.get_or_create(
        nomUtilisateur="responsable",
        defaults={"role": Role.objects.get(nomRole="Responsable GMAO")},
    )
