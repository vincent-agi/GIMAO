"""Tests unitaires du module ``equipement.services`` (cf. TUS-003).

Ces tests exercent directement les fonctions de service, sans passer par la
couche HTTP/DRF, pour garantir que la logique métier extraite d'
``EquipementViewSet`` reste correcte indépendamment de son point d'entrée.
"""

from types import SimpleNamespace

import pytest
from django.utils import timezone

from equipement import services
from equipement.models import Compteur, Constituer, Declencher, StatutEquipement
from maintenance.models import PlanMaintenance
from tests.factories import (
    BonTravailFactory,
    CompteurFactory,
    ConsommableFactory,
    DemandeInterventionFactory,
    EquipementFactory,
    FamilleEquipementFactory,
    FournisseurFactory,
    LieuFactory,
    ModeleEquipementFactory,
    TypePlanMaintenanceFactory,
    UtilisateurFactory,
)

pytestmark = pytest.mark.django_db


def anonymous_request_user():
    """Simule un ``request.user`` Django non authentifié."""
    return SimpleNamespace(is_authenticated=False)


def authenticated_request_user(utilisateur):
    """Simule un ``request.user`` Django authentifié rattaché à un ``Utilisateur`` métier."""
    return SimpleNamespace(is_authenticated=True, username=utilisateur.nomUtilisateur)


# ==========================================
# date_to_ordinal_days
# ==========================================


class TestDateToOrdinalDays:
    def test_should_convert_valid_iso_date_to_positive_day_count(self):
        assert services.date_to_ordinal_days("2024-01-02") > 0

    def test_should_return_zero_for_none(self):
        assert services.date_to_ordinal_days(None) == 0

    def test_should_return_zero_for_malformed_date(self):
        assert services.date_to_ordinal_days("pas-une-date") == 0


# ==========================================
# create_declencher_for_plan
# ==========================================


class TestCreateDeclencherForPlan:
    def test_should_create_declencher_with_sum_for_numeric_compteur(self):
        from tests.factories import PlanMaintenanceFactory

        compteur = CompteurFactory(type="Numérique")
        plan = PlanMaintenanceFactory(equipement=compteur.equipement)

        declencher = services.create_declencher_for_plan(
            compteur, plan, {"derniereIntervention": 100, "ecartInterventions": 50}
        )

        assert declencher.derniereIntervention == 100
        assert declencher.prochaineMaintenance == 150

    def test_should_convert_dates_to_ordinal_days_for_calendaire_compteur(self):
        from tests.factories import PlanMaintenanceFactory

        compteur = CompteurFactory(type="Calendaire")
        plan = PlanMaintenanceFactory(equipement=compteur.equipement)

        declencher = services.create_declencher_for_plan(
            compteur,
            plan,
            {"derniereIntervention": "2024-01-01", "prochaineMaintenance": "2024-06-01"},
        )

        assert declencher.derniereIntervention == services.date_to_ordinal_days("2024-01-01")
        assert declencher.prochaineMaintenance == services.date_to_ordinal_days("2024-06-01")


# ==========================================
# create_equipement
# ==========================================


class TestCreateEquipement:
    def _base_data(self, lieu, modele, famille, fournisseur, fabricant):
        return {
            "reference": "REF-001",
            "designation": "Chariot élévateur",
            "lieu": lieu.id,
            "modeleEquipement": modele.id,
            "famille": famille.id,
            "fournisseur": fournisseur.id,
            "fabricant": fabricant.id,
        }

    def test_should_create_equipement_with_resolved_authenticated_user(self):
        utilisateur = UtilisateurFactory()
        lieu = LieuFactory()
        famille = FamilleEquipementFactory()
        fournisseur = FournisseurFactory()
        modele = ModeleEquipementFactory()
        data = self._base_data(lieu, modele, famille, fournisseur, modele.fabricant)

        equipement = services.create_equipement(data, {}, authenticated_request_user(utilisateur))

        assert equipement.pk is not None
        assert equipement.createurEquipement_id == utilisateur.pk
        assert equipement.reference == "REF-001"

    def test_should_fallback_to_createur_equipement_field_when_request_user_not_authenticated(self):
        utilisateur = UtilisateurFactory()
        lieu = LieuFactory()
        famille = FamilleEquipementFactory()
        fournisseur = FournisseurFactory()
        modele = ModeleEquipementFactory()
        data = self._base_data(lieu, modele, famille, fournisseur, modele.fabricant)
        data["createurEquipement"] = utilisateur.id

        equipement = services.create_equipement(data, {}, anonymous_request_user())

        assert equipement.createurEquipement_id == utilisateur.pk

    def test_should_raise_when_no_createur_can_be_resolved(self):
        lieu = LieuFactory()
        famille = FamilleEquipementFactory()
        fournisseur = FournisseurFactory()
        modele = ModeleEquipementFactory()
        data = self._base_data(lieu, modele, famille, fournisseur, modele.fabricant)

        with pytest.raises(services.UtilisateurCreateurIntrouvable):
            services.create_equipement(data, {}, anonymous_request_user())

    def test_should_create_initial_statut_when_provided(self):
        utilisateur = UtilisateurFactory()
        lieu = LieuFactory()
        famille = FamilleEquipementFactory()
        fournisseur = FournisseurFactory()
        modele = ModeleEquipementFactory()
        data = self._base_data(lieu, modele, famille, fournisseur, modele.fabricant)
        data["statut"] = "EN_FONCTIONNEMENT"

        equipement = services.create_equipement(data, {}, authenticated_request_user(utilisateur))

        assert StatutEquipement.objects.filter(
            equipement=equipement, statut="EN_FONCTIONNEMENT"
        ).exists()

    def test_should_link_consommables_via_constituer(self):
        utilisateur = UtilisateurFactory()
        lieu = LieuFactory()
        famille = FamilleEquipementFactory()
        fournisseur = FournisseurFactory()
        modele = ModeleEquipementFactory()
        consommable = ConsommableFactory()
        data = self._base_data(lieu, modele, famille, fournisseur, modele.fabricant)
        data["consommables"] = [consommable.id]

        equipement = services.create_equipement(data, {}, authenticated_request_user(utilisateur))

        assert Constituer.objects.filter(equipement=equipement, consommable=consommable).exists()

    def test_should_create_compteurs_and_linked_plan_with_declencher(self):
        utilisateur = UtilisateurFactory()
        lieu = LieuFactory()
        famille = FamilleEquipementFactory()
        fournisseur = FournisseurFactory()
        modele = ModeleEquipementFactory()
        data = self._base_data(lieu, modele, famille, fournisseur, modele.fabricant)
        type_plan = TypePlanMaintenanceFactory()
        data["compteurs"] = [
            {
                "nom": "Compteur horaire",
                "valeurCourante": 10,
                "unite": "heures",
                "type": "Numérique",
            }
        ]
        data["plansMaintenance"] = [
            {
                "compteurIndex": 0,
                "nom": "Vidange 500h",
                "type_id": type_plan.id,
                "seuil": {"derniereIntervention": 10, "ecartInterventions": 500},
            }
        ]

        equipement = services.create_equipement(data, {}, authenticated_request_user(utilisateur))

        compteur = Compteur.objects.get(equipement=equipement)
        plan = PlanMaintenance.objects.get(equipement=equipement)
        declencher = Declencher.objects.get(compteur=compteur, planMaintenance=plan)

        assert declencher.prochaineMaintenance == 510

    def test_should_raise_document_requis_manquant_when_file_missing(self):
        utilisateur = UtilisateurFactory()
        lieu = LieuFactory()
        famille = FamilleEquipementFactory()
        fournisseur = FournisseurFactory()
        modele = ModeleEquipementFactory()
        data = self._base_data(lieu, modele, famille, fournisseur, modele.fabricant)
        type_plan = TypePlanMaintenanceFactory()
        data["compteurs"] = [
            {"nom": "Compteur", "valeurCourante": 0, "unite": "heures", "type": "Numérique"}
        ]
        data["plansMaintenance"] = [
            {
                "compteurIndex": 0,
                "nom": "Plan",
                "type_id": type_plan.id,
                "seuil": {},
                "documents": [{"titre": "Notice", "type": 1}],
            }
        ]

        with pytest.raises(services.DocumentRequisManquant):
            services.create_equipement(data, {}, authenticated_request_user(utilisateur))


# ==========================================
# update_equipement
# ==========================================


class TestUpdateEquipement:
    def test_should_update_simple_field_when_value_differs(self):
        equipement = EquipementFactory(designation="Ancien nom")

        updated = services.update_equipement(
            equipement, {"designation": {"nouvelle": "Nouveau nom"}}, {}
        )

        assert updated.designation == "Nouveau nom"

    def test_should_not_persist_when_value_is_identical(self):
        equipement = EquipementFactory(designation="Identique")

        updated = services.update_equipement(
            equipement, {"designation": {"nouvelle": "Identique"}}, {}
        )

        assert updated.designation == "Identique"

    def test_should_create_statut_history_entry_when_statut_changes(self):
        equipement = EquipementFactory()
        StatutEquipement.objects.create(equipement=equipement, statut="EN_FONCTIONNEMENT")

        services.update_equipement(equipement, {"statut": {"nouvelle": "DEGRADE"}}, {})

        assert StatutEquipement.objects.filter(equipement=equipement, statut="DEGRADE").exists()

    def test_should_not_duplicate_statut_history_entry_when_statut_unchanged(self):
        equipement = EquipementFactory()
        StatutEquipement.objects.create(equipement=equipement, statut="EN_FONCTIONNEMENT")
        count_before = StatutEquipement.objects.filter(equipement=equipement).count()

        services.update_equipement(equipement, {"statut": {"nouvelle": "EN_FONCTIONNEMENT"}}, {})

        assert StatutEquipement.objects.filter(equipement=equipement).count() == count_before

    def test_should_add_and_remove_consommables(self):
        equipement = EquipementFactory()
        conso_a = ConsommableFactory()
        conso_b = ConsommableFactory()
        Constituer.objects.create(equipement=equipement, consommable=conso_a)

        services.update_equipement(
            equipement,
            {"consommables": {"ajoutes": [conso_b.id], "retires": [conso_a.id]}},
            {},
        )

        assert not Constituer.objects.filter(equipement=equipement, consommable=conso_a).exists()
        assert Constituer.objects.filter(equipement=equipement, consommable=conso_b).exists()


# ==========================================
# archive_equipement_cascade
# ==========================================


class TestArchiveEquipementCascade:
    def test_should_archive_linked_demande_intervention(self):
        equipement = EquipementFactory()
        di = DemandeInterventionFactory(equipement=equipement, archive=False)

        services.archive_equipement_cascade(equipement)

        di.refresh_from_db()
        assert di.archive is True

    def test_should_terminate_and_archive_linked_bon_travail(self):
        equipement = EquipementFactory()
        di = DemandeInterventionFactory(equipement=equipement)
        bt = BonTravailFactory(demande_intervention=di, statut="EN_COURS", archive=False)

        services.archive_equipement_cascade(equipement)

        bt.refresh_from_db()
        assert bt.statut == "TERMINE"
        assert bt.archive is True
        assert bt.date_fin is not None

    def test_should_not_downgrade_bon_travail_already_cloture(self):
        equipement = EquipementFactory()
        di = DemandeInterventionFactory(equipement=equipement)
        bt = BonTravailFactory(demande_intervention=di, statut="CLOTURE", archive=False)

        services.archive_equipement_cascade(equipement)

        bt.refresh_from_db()
        assert bt.statut == "CLOTURE"
        assert bt.archive is True


# ==========================================
# get_historique_statuts / compute_equipement_kpi
# ==========================================


class TestHistoriqueEtKpi:
    def test_historique_statuts_should_be_ordered_chronologically(self):
        equipement = EquipementFactory()
        StatutEquipement.objects.create(equipement=equipement, statut="EN_FONCTIONNEMENT")
        StatutEquipement.objects.create(equipement=equipement, statut="DEGRADE")

        historique = services.get_historique_statuts(equipement)

        assert [h["statut"] for h in historique] == ["EN_FONCTIONNEMENT", "DEGRADE"]

    def test_kpi_should_return_none_values_when_no_panne(self):
        equipement = EquipementFactory()

        kpi = services.compute_equipement_kpi(equipement)

        assert kpi == {"nombre_pannes": 0, "mtbf_heures": None, "mttr_heures": None}

    def test_kpi_should_count_confirmed_pannes_only(self):
        equipement = EquipementFactory(dateMiseEnService=timezone.now())
        DemandeInterventionFactory(equipement=equipement, statut="ACCEPTEE")
        DemandeInterventionFactory(equipement=equipement, statut="EN_ATTENTE")

        kpi = services.compute_equipement_kpi(equipement)

        assert kpi["nombre_pannes"] == 1

    def test_kpi_should_compute_mttr_from_completed_correctif_bt(self):
        equipement = EquipementFactory()
        di = DemandeInterventionFactory(equipement=equipement, statut="ACCEPTEE")
        now = timezone.now()
        BonTravailFactory(
            demande_intervention=di,
            type="CORRECTIF",
            statut="CLOTURE",
            date_debut=now,
            date_fin=now + timezone.timedelta(hours=2),
        )

        kpi = services.compute_equipement_kpi(equipement)

        assert kpi["mttr_heures"] == 2.0


# ==========================================
# add_document_to_equipement
# ==========================================


class TestAddDocumentToEquipement:
    def test_should_raise_when_file_missing(self):
        equipement = EquipementFactory()

        with pytest.raises(services.DocumentRequisManquant):
            services.add_document_to_equipement(equipement, None, "Notice", 1)

    def test_should_raise_when_type_missing(self):
        equipement = EquipementFactory()
        fake_file = SimpleNamespace(name="notice.pdf")

        with pytest.raises(services.DocumentRequisManquant):
            services.add_document_to_equipement(equipement, fake_file, "Notice", None)
