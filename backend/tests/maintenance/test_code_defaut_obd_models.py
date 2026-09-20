"""Tests du modèle ``CodeDefautOBD`` (TUS-022)."""

import datetime

import pytest
from django.utils.timezone import make_aware

from maintenance.models import CodeDefautOBD, IncidentVehicule
from tests.factories import DemandeInterventionFactory, VehiculeProfileFactory

pytestmark = pytest.mark.django_db


class TestCodeDefautOBDCreation:
    def test_should_create_manual_code_linked_to_vehicule(self):
        vehicule_profile = VehiculeProfileFactory()

        code = CodeDefautOBD.objects.create(
            vehicule_profile=vehicule_profile,
            code="P0301",
            description="Raté d'allumage cylindre 1",
            date_lecture=make_aware(datetime.datetime(2024, 3, 1, 10, 0)),
            source="MANUEL",
        )

        assert code in vehicule_profile.codes_defaut_obd.all()

    def test_should_allow_optional_link_to_incident(self):
        vehicule_profile = VehiculeProfileFactory()
        incident = IncidentVehicule.objects.create(
            demande_intervention=DemandeInterventionFactory(equipement=vehicule_profile.equipement),
            type_avarie="CODE_DEFAUT",
        )

        code = CodeDefautOBD.objects.create(
            vehicule_profile=vehicule_profile,
            incident_vehicule=incident,
            code="P0420",
            date_lecture=make_aware(datetime.datetime(2024, 3, 1, 10, 0)),
            source="MANUEL",
        )

        assert code in incident.codes_defaut_obd.all()

    def test_should_create_code_without_incident(self):
        vehicule_profile = VehiculeProfileFactory()

        code = CodeDefautOBD.objects.create(
            vehicule_profile=vehicule_profile,
            code="P0171",
            date_lecture=make_aware(datetime.datetime(2024, 3, 1, 10, 0)),
            source="AUTOMATIQUE",
        )

        assert code.incident_vehicule is None

    def test_should_keep_code_when_incident_is_deleted(self):
        vehicule_profile = VehiculeProfileFactory()
        incident = IncidentVehicule.objects.create(
            demande_intervention=DemandeInterventionFactory(equipement=vehicule_profile.equipement),
            type_avarie="CODE_DEFAUT",
        )
        code = CodeDefautOBD.objects.create(
            vehicule_profile=vehicule_profile,
            incident_vehicule=incident,
            code="P0300",
            date_lecture=make_aware(datetime.datetime(2024, 3, 1, 10, 0)),
            source="MANUEL",
        )

        incident.demande_intervention.delete()

        code.refresh_from_db()
        assert code.incident_vehicule_id is None


class TestCodeDefautOBDHistorique:
    def test_most_recent_code_should_be_first_by_default_ordering(self):
        vehicule_profile = VehiculeProfileFactory()
        CodeDefautOBD.objects.create(
            vehicule_profile=vehicule_profile,
            code="P0100",
            date_lecture=make_aware(datetime.datetime(2022, 1, 1)),
            source="MANUEL",
        )
        recent = CodeDefautOBD.objects.create(
            vehicule_profile=vehicule_profile,
            code="P0200",
            date_lecture=make_aware(datetime.datetime(2024, 1, 1)),
            source="MANUEL",
        )

        assert vehicule_profile.codes_defaut_obd.first().pk == recent.pk
