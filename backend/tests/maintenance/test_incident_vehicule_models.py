"""Tests du modèle ``IncidentVehicule`` (TUS-020)."""

import pytest
from django.db import IntegrityError

from maintenance.models import DemandeIntervention, IncidentVehicule
from tests.factories import DemandeInterventionFactory, EquipementFactory

pytestmark = pytest.mark.django_db


class TestIncidentVehiculeCreation:
    def test_should_create_incident_linked_to_demande_intervention(self):
        demande = DemandeInterventionFactory(equipement=EquipementFactory(type="VEHICULE"))

        incident = IncidentVehicule.objects.create(
            demande_intervention=demande,
            type_avarie="VOYANT",
            gravite="MINEURE",
            immobilisation=False,
        )

        assert demande.incident_vehicule == incident

    def test_should_default_gravite_to_mineure(self):
        demande = DemandeInterventionFactory()

        incident = IncidentVehicule.objects.create(
            demande_intervention=demande, type_avarie="BRUIT_ANORMAL"
        )

        assert incident.gravite == "MINEURE"

    def test_should_reject_second_incident_for_same_demande_intervention(self):
        demande = DemandeInterventionFactory()
        IncidentVehicule.objects.create(demande_intervention=demande, type_avarie="VOYANT")

        with pytest.raises(IntegrityError):
            IncidentVehicule.objects.create(demande_intervention=demande, type_avarie="CODE_DEFAUT")


class TestIncidentVehiculeCascade:
    def test_should_delete_incident_when_demande_intervention_is_deleted(self):
        demande = DemandeInterventionFactory()
        incident = IncidentVehicule.objects.create(
            demande_intervention=demande, type_avarie="ACCIDENT_ROUTE", immobilisation=True
        )

        demande.delete()

        assert not IncidentVehicule.objects.filter(pk=incident.pk).exists()

    def test_demande_intervention_without_incident_should_not_expose_one(self):
        demande = DemandeInterventionFactory()

        with pytest.raises(DemandeIntervention.incident_vehicule.RelatedObjectDoesNotExist):
            _ = demande.incident_vehicule
