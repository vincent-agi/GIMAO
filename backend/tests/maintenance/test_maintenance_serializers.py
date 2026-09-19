import pytest

from maintenance.api.serializers import (
    BonTravailSerializer,
    DemandeInterventionSerializer,
    PlanMaintenanceDetailSerializer,
    PlanMaintenanceSerializer,
)
from maintenance.models import BonTravailConsommable
from tests.factories import (
    BonTravailFactory,
    ConsommableFactory,
    DemandeInterventionFactory,
    EquipementFactory,
    PlanMaintenanceConsommableFactory,
    PlanMaintenanceFactory,
    UtilisateurFactory,
)


@pytest.mark.django_db
def test_should_require_statut_suppose_for_demande_serializer():
    user = UtilisateurFactory()
    equipement = EquipementFactory()

    serializer = DemandeInterventionSerializer(
        data={
            "nom": "DI sans statut suppose",
            "commentaire": "test",
            "utilisateur_id": user.pk,
            "equipement_id": equipement.pk,
        }
    )

    assert serializer.is_valid() is False
    assert "statut_suppose" in serializer.errors


@pytest.mark.django_db
def test_should_create_demande_with_default_status_and_links():
    user = UtilisateurFactory()
    equipement = EquipementFactory()

    serializer = DemandeInterventionSerializer(
        data={
            "nom": "DI test serializer",
            "commentaire": "commentaire",
            "statut_suppose": "EN_FONCTIONNEMENT",
            "utilisateur_id": user.pk,
            "equipement_id": equipement.pk,
        }
    )

    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    assert instance.statut == "EN_ATTENTE"
    assert instance.utilisateur_id == user.pk
    assert instance.equipement_id == equipement.pk
    assert instance.date_creation is not None
    assert instance.date_changementStatut is not None


@pytest.mark.django_db
def test_should_create_bon_travail_with_consommables_and_quantities():
    demande = DemandeInterventionFactory()
    responsable = UtilisateurFactory()
    conso_1 = ConsommableFactory()
    conso_2 = ConsommableFactory()

    serializer = BonTravailSerializer(
        data={
            "nom": "BT serializer create",
            "type": "CORRECTIF",
            "demande_intervention": demande.pk,
            "responsable_id": responsable.pk,
            "consommables": [
                {"consommable_id": conso_1.pk, "quantite_utilisee": 2},
                {"consommable_id": conso_2.pk, "quantite_utilisee": 5},
            ],
        }
    )

    assert serializer.is_valid(), serializer.errors
    bt = serializer.save()

    assocs = BonTravailConsommable.objects.filter(bon_travail=bt).order_by("consommable_id")
    assert assocs.count() == 2
    assert assocs[0].quantite_utilisee in [2, 5]
    assert assocs[1].quantite_utilisee in [2, 5]


@pytest.mark.django_db
def test_should_create_bon_travail_with_consommables_ids_zero_quantity():
    demande = DemandeInterventionFactory()
    conso = ConsommableFactory()

    serializer = BonTravailSerializer(
        data={
            "nom": "BT serializer ids-only",
            "type": "PREVENTIF",
            "demande_intervention": demande.pk,
            "consommables_ids": [conso.pk],
        }
    )

    assert serializer.is_valid(), serializer.errors
    bt = serializer.save()

    assoc = BonTravailConsommable.objects.get(bon_travail=bt, consommable=conso)
    assert assoc.quantite_utilisee == 0


@pytest.mark.django_db
def test_should_sync_bon_travail_consommables_on_update_and_add():
    bt = BonTravailFactory(type="CORRECTIF")
    conso_keep = ConsommableFactory()
    conso_remove = ConsommableFactory()
    conso_add = ConsommableFactory()

    BonTravailConsommable.objects.create(
        bon_travail=bt, consommable=conso_keep, quantite_utilisee=1
    )
    BonTravailConsommable.objects.create(
        bon_travail=bt, consommable=conso_remove, quantite_utilisee=4
    )

    serializer = BonTravailSerializer(
        instance=bt,
        data={
            "consommables": [
                {"consommable_id": conso_keep.pk, "quantite_utilisee": 7},
                {"consommable_id": conso_remove.pk, "quantite_utilisee": 4},
                {"consommable_id": conso_add.pk, "quantite_utilisee": 3},
            ]
        },
        partial=True,
    )

    assert serializer.is_valid(), serializer.errors
    serializer.save()

    assert (
        BonTravailConsommable.objects.get(bon_travail=bt, consommable=conso_keep).quantite_utilisee
        == 7
    )
    assert (
        BonTravailConsommable.objects.get(
            bon_travail=bt, consommable=conso_remove
        ).quantite_utilisee
        == 4
    )
    assert (
        BonTravailConsommable.objects.get(bon_travail=bt, consommable=conso_add).quantite_utilisee
        == 3
    )


@pytest.mark.django_db
def test_should_serialize_plan_maintenance_consommables_in_list_and_detail():
    plan = PlanMaintenanceFactory()
    conso = ConsommableFactory()
    PlanMaintenanceConsommableFactory(
        plan_maintenance=plan,
        consommable=conso,
        quantite_necessaire=6,
    )

    list_data = PlanMaintenanceSerializer(plan).data
    detail_data = PlanMaintenanceDetailSerializer(plan).data

    assert list_data["consommables"] == [{"consommable": conso.pk, "quantite": 6}]
    assert detail_data["consommables"] == [{"consommable": conso.pk, "quantite": 6}]
