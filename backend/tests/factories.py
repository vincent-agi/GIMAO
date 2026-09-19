import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from donnees.models import Fabricant, Fournisseur, Lieu
from equipement.models import (
    Compteur,
    Declencher,
    Equipement,
    FamilleEquipement,
    ModeleEquipement,
    VehiculeProfile,
)
from maintenance.models import (
    BonTravail,
    DemandeIntervention,
    PlanMaintenance,
    PlanMaintenanceConsommable,
    TypePlanMaintenance,
)
from stock.models import Consommable
from utilisateur.models import Permission, Role, Utilisateur

# ==========================================
# UTILISATEUR & ROLES
# ==========================================


class RoleFactory(DjangoModelFactory):
    class Meta:
        model = Role

    nomRole = factory.Sequence(lambda n: f"Role_{n}")


class UtilisateurFactory(DjangoModelFactory):
    class Meta:
        model = Utilisateur

    nomUtilisateur = factory.Sequence(lambda n: f"technicien_{n}")
    prenom = "Jean"
    nomFamille = "Dupont"
    email = factory.Sequence(lambda n: f"jean.dupont{n}@gimao.local")
    actif = True
    role = factory.SubFactory(RoleFactory)


class PermissionFactory(DjangoModelFactory):
    class Meta:
        model = Permission

    nomPermission = factory.Sequence(lambda n: f"perm_{n}")


# ==========================================
# REFERENTIEL DONNEES
# ==========================================


class LieuFactory(DjangoModelFactory):
    class Meta:
        model = Lieu

    nomLieu = factory.Sequence(lambda n: f"Atelier_{n}")


class FabricantFactory(DjangoModelFactory):
    class Meta:
        model = Fabricant

    nom = factory.Sequence(lambda n: f"Fabricant_{n}")


class FournisseurFactory(DjangoModelFactory):
    class Meta:
        model = Fournisseur

    nom = factory.Sequence(lambda n: f"Fournisseur_{n}")


class ModeleEquipementFactory(DjangoModelFactory):
    class Meta:
        model = ModeleEquipement

    nom = factory.Sequence(lambda n: f"Modele_{n}")
    fabricant = factory.SubFactory(FabricantFactory)


class FamilleEquipementFactory(DjangoModelFactory):
    class Meta:
        model = FamilleEquipement

    nom = factory.Sequence(lambda n: f"Famille_{n}")


# ==========================================
# EQUIPEMENTS & COMPTEURS
# ==========================================


class EquipementFactory(DjangoModelFactory):
    class Meta:
        model = Equipement

    designation = factory.Sequence(lambda n: f"Equipement_Test_{n}")
    lieu = factory.SubFactory(LieuFactory)
    modele = factory.SubFactory(ModeleEquipementFactory)
    famille = factory.SubFactory(FamilleEquipementFactory)
    fournisseur = factory.SubFactory(FournisseurFactory)
    fabricant = factory.SelfAttribute("modele.fabricant")
    createurEquipement = factory.SubFactory(UtilisateurFactory)


class VehiculeProfileFactory(DjangoModelFactory):
    class Meta:
        model = VehiculeProfile

    equipement = factory.SubFactory(EquipementFactory, type="VEHICULE")
    vin = factory.Sequence(lambda n: f"VF1BB{n:012d}")
    immatriculation = factory.Sequence(lambda n: f"AA-{n % 1000:03d}-AA")
    genre = "VL"
    energie = "DIESEL"


class CompteurFactory(DjangoModelFactory):
    class Meta:
        model = Compteur

    nomCompteur = factory.Sequence(lambda n: f"Compteur_{n}")
    valeurCourante = 0.0
    unite = "Heures"
    equipement = factory.SubFactory(EquipementFactory)


# ==========================================
# MAINTENANCE
# ==========================================


class TypePlanMaintenanceFactory(DjangoModelFactory):
    class Meta:
        model = TypePlanMaintenance

    libelle = factory.Sequence(lambda n: f"Type_Plan_{n}")


class PlanMaintenanceFactory(DjangoModelFactory):
    class Meta:
        model = PlanMaintenance

    nom = factory.Sequence(lambda n: f"Plan_Maintenance_{n}")
    equipement = factory.SubFactory(EquipementFactory)
    type_plan_maintenance = factory.SubFactory(TypePlanMaintenanceFactory)


class DeclencherFactory(DjangoModelFactory):
    class Meta:
        model = Declencher

    compteur = factory.SubFactory(CompteurFactory)
    planMaintenance = factory.SubFactory(PlanMaintenanceFactory)
    derniereIntervention = 0
    prochaineMaintenance = 100
    ecartInterventions = 100
    estGlissant = False


# ==========================================
# DEMANDES D'INTERVENTION & BONS DE TRAVAIL
# ==========================================


class DemandeInterventionFactory(DjangoModelFactory):
    class Meta:
        model = DemandeIntervention

    nom = factory.Sequence(lambda n: f"Demande_Intervention_{n}")
    statut = "EN_ATTENTE"
    date_creation = factory.LazyFunction(timezone.now)
    date_changementStatut = factory.LazyFunction(timezone.now)
    utilisateur = factory.SubFactory(UtilisateurFactory)
    equipement = factory.SubFactory(EquipementFactory)


class BonTravailFactory(DjangoModelFactory):
    class Meta:
        model = BonTravail

    nom = factory.Sequence(lambda n: f"Bon_Travail_{n}")
    type = "PREVENTIF"
    statut = "EN_ATTENTE"
    demande_intervention = factory.SubFactory(DemandeInterventionFactory)
    responsable = factory.SubFactory(UtilisateurFactory)


class ConsommableFactory(DjangoModelFactory):
    class Meta:
        model = Consommable

    designation = factory.Sequence(lambda n: f"Consommable_{n}")


class PlanMaintenanceConsommableFactory(DjangoModelFactory):
    class Meta:
        model = PlanMaintenanceConsommable

    plan_maintenance = factory.SubFactory(PlanMaintenanceFactory)
    consommable = factory.SubFactory(ConsommableFactory)
    quantite_necessaire = 2
