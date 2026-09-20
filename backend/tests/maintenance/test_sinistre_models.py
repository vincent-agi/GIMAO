"""Tests du modèle ``Sinistre`` (TUS-021)."""

import datetime

import pytest
from django.core.exceptions import ValidationError

from maintenance.models import IncidentVehicule, Sinistre
from tests.factories import DemandeInterventionFactory

pytestmark = pytest.mark.django_db


def make_incident(type_avarie="ACCIDENT_ROUTE", **overrides):
    demande = DemandeInterventionFactory()
    return IncidentVehicule.objects.create(
        demande_intervention=demande, type_avarie=type_avarie, **overrides
    )


def make_sinistre(incident_vehicule, **overrides):
    fields = {
        "incident_vehicule": incident_vehicule,
        "date_accident": datetime.date(2024, 6, 1),
        "lieu_accident": "Rond-point de la Liberté, Marseille",
    }
    fields.update(overrides)
    return Sinistre(**fields)


class TestSinistreCreation:
    def test_should_create_sinistre_for_accident_route_incident(self):
        incident = make_incident(type_avarie="ACCIDENT_ROUTE", immobilisation=True)

        sinistre = make_sinistre(incident)
        sinistre.full_clean()
        sinistre.save()

        assert incident.sinistre == sinistre

    def test_should_reject_sinistre_for_non_accident_incident(self):
        incident = make_incident(type_avarie="VOYANT")

        sinistre = make_sinistre(incident)

        with pytest.raises(ValidationError):
            sinistre.full_clean()

    def test_should_allow_blank_optional_fields(self):
        incident = make_incident(type_avarie="ACCIDENT_ROUTE")

        sinistre = make_sinistre(incident, tiers_impliques="", degats_constates="", expertise="")
        sinistre.full_clean()  # ne doit pas lever

        sinistre.save()
        assert Sinistre.objects.filter(pk=incident.pk).exists()


class TestSinistreCascade:
    def test_should_delete_sinistre_when_incident_is_deleted(self):
        incident = make_incident(type_avarie="ACCIDENT_ROUTE")
        sinistre = make_sinistre(incident)
        sinistre.full_clean()
        sinistre.save()

        incident.delete()

        assert not Sinistre.objects.filter(pk=sinistre.pk).exists()
