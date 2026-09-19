import pytest

from maintenance.models import BonTravail, DemandeIntervention, PlanMaintenance, TypePlanMaintenance
from tests.factories import (
    BonTravailFactory,
    DemandeInterventionFactory,
    PlanMaintenanceFactory,
    TypePlanMaintenanceFactory,
)


@pytest.mark.django_db
class TestMaintenanceModels:
    def test_type_plan_creation(self):
        TypePlanMaintenanceFactory(libelle="Preventif")
        assert TypePlanMaintenance.objects.filter(libelle="Preventif").exists()

    def test_plan_maintenance_creation(self):
        pm = PlanMaintenanceFactory(nom="Plan Annuel")
        assert PlanMaintenance.objects.filter(nom="Plan Annuel").exists()
        assert "Plan Annuel" in str(pm)

    def test_demande_intervention_str(self):
        di = DemandeInterventionFactory(nom="Panne moteur")
        assert "Panne moteur" in str(di)

    def test_bon_travail_status_update(self):
        bt = BonTravailFactory(statut="EN_ATTENTE")
        bt.statut = "TERMINE"
        bt.save()
        assert BonTravail.objects.get(id=bt.id).statut == "TERMINE"

    def test_type_plan_delete(self):
        tpm = TypePlanMaintenanceFactory()
        tpm_id = tpm.id
        tpm.delete()
        assert not TypePlanMaintenance.objects.filter(id=tpm_id).exists()

    def test_demande_intervention_update(self):
        di = DemandeInterventionFactory(statut="EN_ATTENTE")
        di.statut = "EN_COURS"
        di.save()
        assert DemandeIntervention.objects.get(id=di.id).statut == "EN_COURS"

    def test_bon_travail_creation(self):
        BonTravailFactory(nom="Nettoyage")
        assert BonTravail.objects.filter(nom="Nettoyage").exists()

    def test_plan_maintenance_multiple(self):
        PlanMaintenanceFactory.create_batch(4)
        assert PlanMaintenance.objects.count() >= 4

    def test_demande_intervention_relation(self):
        di = DemandeInterventionFactory()
        assert di.equipement is not None
        assert di.utilisateur is not None

    def test_bon_travail_relations(self):
        bt = BonTravailFactory()
        assert bt.demande_intervention is not None
        assert bt.responsable is not None
