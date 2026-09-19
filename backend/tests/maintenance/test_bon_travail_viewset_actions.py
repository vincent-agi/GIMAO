import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory

from donnees.models import Document, TypeDocument
from maintenance.api.viewsets import BonTravailViewSet
from maintenance.models import (
    BonTravail,
    BonTravailConsommable,
    BonTravailConsommableReservation,
    DemandeIntervention,
)
from stock.models import Magasin, Stocker
from tests.factories import (
    BonTravailFactory,
    ConsommableFactory,
    EquipementFactory,
    UtilisateurFactory,
)


@pytest.fixture
def api_factory():
    return APIRequestFactory()


def _extract_items(response_data):
    if isinstance(response_data, dict) and "results" in response_data:
        return response_data["results"]
    return response_data


@pytest.mark.django_db
def test_should_return_400_when_distribution_without_consommable_id(api_factory):
    bon = BonTravailFactory()

    view = BonTravailViewSet.as_view({"patch": "update_consommable_distribution"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/update_consommable_distribution/",
        {"distribue": True},
        format="json",
    )

    response = view(request, pk=bon.pk)

    assert response.status_code == 400
    assert "consommable_id" in response.data["error"]


@pytest.mark.django_db
def test_should_return_404_when_consommable_is_not_linked_to_bt(api_factory):
    bon = BonTravailFactory()
    consommable = ConsommableFactory()

    view = BonTravailViewSet.as_view({"patch": "update_consommable_distribution"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/update_consommable_distribution/",
        {"consommable_id": consommable.pk, "distribue": True},
        format="json",
    )

    response = view(request, pk=bon.pk)

    assert response.status_code == 404
    assert "Consommable non trouvé" in response.data["error"]


@pytest.mark.django_db
def test_should_confirm_distribution_and_decrease_stock_for_single_eligible_store(api_factory):
    bon = BonTravailFactory()
    consommable = ConsommableFactory()
    assoc = BonTravailConsommable.objects.create(
        bon_travail=bon,
        consommable=consommable,
        quantite_utilisee=3,
    )
    magasin = Magasin.objects.create(nom="Magasin A")
    stock = Stocker.objects.create(consommable=consommable, magasin=magasin, quantite=7)

    view = BonTravailViewSet.as_view({"patch": "update_consommable_distribution"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/update_consommable_distribution/",
        {"consommable_id": consommable.pk, "distribue": True},
        format="json",
    )

    response = view(request, pk=bon.pk)
    assoc.refresh_from_db()
    stock.refresh_from_db()

    assert response.status_code == 200
    assert assoc.estConfirme is True
    assert assoc.date_confirme is not None
    assert assoc.magasin_reserve_id == magasin.pk
    assert stock.quantite == 4


@pytest.mark.django_db
def test_should_return_409_when_multiple_stores_can_cover_and_no_choice_given(api_factory):
    bon = BonTravailFactory()
    consommable = ConsommableFactory()
    BonTravailConsommable.objects.create(
        bon_travail=bon,
        consommable=consommable,
        quantite_utilisee=2,
    )
    magasin_a = Magasin.objects.create(nom="Magasin A")
    magasin_b = Magasin.objects.create(nom="Magasin B")
    Stocker.objects.create(consommable=consommable, magasin=magasin_a, quantite=5)
    Stocker.objects.create(consommable=consommable, magasin=magasin_b, quantite=6)

    view = BonTravailViewSet.as_view({"patch": "update_consommable_distribution"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/update_consommable_distribution/",
        {"consommable_id": consommable.pk, "distribue": True},
        format="json",
    )

    response = view(request, pk=bon.pk)

    assert response.status_code == 409
    assert response.data["needs_magasin_selection"] is True
    assert len(response.data["magasins"]) == 2


@pytest.mark.django_db
def test_should_restore_stock_when_distribution_is_cancelled(api_factory):
    bon = BonTravailFactory()
    consommable = ConsommableFactory()
    magasin = Magasin.objects.create(nom="Magasin A")
    assoc = BonTravailConsommable.objects.create(
        bon_travail=bon,
        consommable=consommable,
        quantite_utilisee=3,
        estConfirme=True,
        magasin_reserve=magasin,
    )
    stock = Stocker.objects.create(consommable=consommable, magasin=magasin, quantite=1)
    BonTravailConsommableReservation.objects.create(
        bon_travail_consommable=assoc,
        magasin=magasin,
        quantite=3,
    )

    view = BonTravailViewSet.as_view({"patch": "update_consommable_distribution"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/update_consommable_distribution/",
        {"consommable_id": consommable.pk, "distribue": False},
        format="json",
    )

    response = view(request, pk=bon.pk)
    assoc.refresh_from_db()
    stock.refresh_from_db()

    assert response.status_code == 200
    assert assoc.estConfirme is False
    assert assoc.date_confirme is None
    assert assoc.magasin_reserve_id is None
    assert stock.quantite == 4
    assert assoc.reservations.count() == 0


@pytest.mark.django_db
def test_should_cancel_all_reservations_for_a_bt(api_factory):
    bon = BonTravailFactory()

    cons_1 = ConsommableFactory()
    mag_1 = Magasin.objects.create(nom="Magasin A")
    assoc_1 = BonTravailConsommable.objects.create(
        bon_travail=bon,
        consommable=cons_1,
        quantite_utilisee=2,
        estConfirme=True,
        magasin_reserve=mag_1,
    )
    stock_1 = Stocker.objects.create(consommable=cons_1, magasin=mag_1, quantite=3)
    BonTravailConsommableReservation.objects.create(
        bon_travail_consommable=assoc_1,
        magasin=mag_1,
        quantite=2,
    )

    cons_2 = ConsommableFactory()
    mag_2 = Magasin.objects.create(nom="Magasin B")
    assoc_2 = BonTravailConsommable.objects.create(
        bon_travail=bon,
        consommable=cons_2,
        quantite_utilisee=1,
        estConfirme=True,
        magasin_reserve=mag_2,
    )
    stock_2 = Stocker.objects.create(consommable=cons_2, magasin=mag_2, quantite=0)

    view = BonTravailViewSet.as_view({"patch": "cancel_mise_de_cote"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/cancel_mise_de_cote/",
        {},
        format="json",
    )

    response = view(request, pk=bon.pk)

    assoc_1.refresh_from_db()
    assoc_2.refresh_from_db()
    stock_1.refresh_from_db()
    stock_2.refresh_from_db()

    assert response.status_code == 200
    assert response.content == b'{"ok": true}'

    assert assoc_1.estConfirme is False
    assert assoc_1.date_confirme is None
    assert assoc_1.magasin_reserve_id is None
    assert assoc_1.reservations.count() == 0
    assert stock_1.quantite == 5

    assert assoc_2.estConfirme is False
    assert assoc_2.date_confirme is None
    assert assoc_2.magasin_reserve_id is None
    assert stock_2.quantite == 1


@pytest.mark.django_db
def test_should_toggle_pieces_recuperees_and_recuperation_date(api_factory):
    bon = BonTravailFactory(pieces_recuperees=False, date_recuperation=None)

    view = BonTravailViewSet.as_view({"patch": "set_recupere"})

    request_true = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/set_recupere/",
        {"recupere": True},
        format="json",
    )
    response_true = view(request_true, pk=bon.pk)
    bon.refresh_from_db()

    assert response_true.status_code == 200
    assert bon.pieces_recuperees is True
    assert bon.date_recuperation is not None

    request_false = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/set_recupere/",
        {"recupere": False},
        format="json",
    )
    response_false = view(request_false, pk=bon.pk)
    bon.refresh_from_db()

    assert response_false.status_code == 200
    assert bon.pieces_recuperees is False
    assert bon.date_recuperation is None


@pytest.mark.django_db
def test_should_return_400_when_repartition_total_does_not_match_needed_quantity(api_factory):
    bon = BonTravailFactory()
    consommable = ConsommableFactory()
    BonTravailConsommable.objects.create(
        bon_travail=bon,
        consommable=consommable,
        quantite_utilisee=4,
    )
    magasin = Magasin.objects.create(nom="Magasin A")
    Stocker.objects.create(consommable=consommable, magasin=magasin, quantite=10)

    view = BonTravailViewSet.as_view({"patch": "update_consommable_distribution"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/update_consommable_distribution/",
        {
            "consommable_id": consommable.pk,
            "distribue": True,
            "repartition": [{"magasin_id": magasin.pk, "quantite": 3}],
        },
        format="json",
    )

    response = view(request, pk=bon.pk)

    assert response.status_code == 400
    assert "totaliser exactement 4" in response.data["error"]


@pytest.mark.django_db
def test_should_return_400_when_repartition_contains_duplicate_store(api_factory):
    bon = BonTravailFactory()
    consommable = ConsommableFactory()
    BonTravailConsommable.objects.create(
        bon_travail=bon,
        consommable=consommable,
        quantite_utilisee=4,
    )
    magasin = Magasin.objects.create(nom="Magasin A")
    Stocker.objects.create(consommable=consommable, magasin=magasin, quantite=10)

    view = BonTravailViewSet.as_view({"patch": "update_consommable_distribution"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/update_consommable_distribution/",
        {
            "consommable_id": consommable.pk,
            "distribue": True,
            "repartition": [
                {"magasin_id": magasin.pk, "quantite": 2},
                {"magasin_id": magasin.pk, "quantite": 2},
            ],
        },
        format="json",
    )

    response = view(request, pk=bon.pk)

    assert response.status_code == 400
    assert "une seule fois" in response.data["error"]


@pytest.mark.django_db
def test_should_return_400_when_repartition_quantity_is_not_positive(api_factory):
    bon = BonTravailFactory()
    consommable = ConsommableFactory()
    BonTravailConsommable.objects.create(
        bon_travail=bon,
        consommable=consommable,
        quantite_utilisee=2,
    )
    magasin = Magasin.objects.create(nom="Magasin A")
    Stocker.objects.create(consommable=consommable, magasin=magasin, quantite=10)

    view = BonTravailViewSet.as_view({"patch": "update_consommable_distribution"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/update_consommable_distribution/",
        {
            "consommable_id": consommable.pk,
            "distribue": True,
            "repartition": [{"magasin_id": magasin.pk, "quantite": 0}],
        },
        format="json",
    )

    response = view(request, pk=bon.pk)

    assert response.status_code == 400
    assert "strictement positive" in response.data["error"]


@pytest.mark.django_db
def test_should_apply_repartition_split_and_create_reservations(api_factory):
    bon = BonTravailFactory()
    consommable = ConsommableFactory()
    assoc = BonTravailConsommable.objects.create(
        bon_travail=bon,
        consommable=consommable,
        quantite_utilisee=5,
    )
    magasin_a = Magasin.objects.create(nom="Magasin A")
    magasin_b = Magasin.objects.create(nom="Magasin B")
    stock_a = Stocker.objects.create(consommable=consommable, magasin=magasin_a, quantite=4)
    stock_b = Stocker.objects.create(consommable=consommable, magasin=magasin_b, quantite=6)

    view = BonTravailViewSet.as_view({"patch": "update_consommable_distribution"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/update_consommable_distribution/",
        {
            "consommable_id": consommable.pk,
            "distribue": True,
            "repartition": [
                {"magasin_id": magasin_a.pk, "quantite": 2},
                {"magasin_id": magasin_b.pk, "quantite": 3},
            ],
        },
        format="json",
    )

    response = view(request, pk=bon.pk)
    assoc.refresh_from_db()
    stock_a.refresh_from_db()
    stock_b.refresh_from_db()

    assert response.status_code == 200
    assert assoc.estConfirme is True
    assert assoc.date_confirme is not None
    assert assoc.magasin_reserve_id is None
    assert stock_a.quantite == 2
    assert stock_b.quantite == 3
    assert assoc.reservations.count() == 2


@pytest.mark.django_db
def test_should_return_400_when_update_status_payload_has_no_statut(api_factory):
    bon = BonTravailFactory(statut="EN_ATTENTE")

    view = BonTravailViewSet.as_view({"patch": "updateStatus"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/updateStatus/",
        {},
        format="json",
    )

    response = view(request, pk=bon.pk)

    assert response.status_code == 400
    assert "statut" in response.data["error"]


@pytest.mark.django_db
def test_should_move_from_en_attente_to_en_cours_and_set_date_debut(api_factory):
    bon = BonTravailFactory(statut="EN_ATTENTE", date_debut=None)

    view = BonTravailViewSet.as_view({"patch": "updateStatus"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/updateStatus/",
        {"statut": "EN_COURS"},
        format="json",
    )

    response = view(request, pk=bon.pk)
    bon.refresh_from_db()

    assert response.status_code == 200
    assert bon.statut == "EN_COURS"
    assert bon.date_debut is not None


@pytest.mark.django_db
def test_should_return_400_when_refusing_closure_without_comment(api_factory):
    bon = BonTravailFactory(statut="TERMINE")

    view = BonTravailViewSet.as_view({"patch": "updateStatus"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/updateStatus/",
        {"statut": "EN_COURS"},
        format="json",
    )

    response = view(request, pk=bon.pk)

    assert response.status_code == 400
    assert "commentaire de refus" in response.data["error"]


@pytest.mark.django_db
def test_should_reopen_terminated_bt_with_refusal_comment(api_factory):
    bon = BonTravailFactory(
        statut="TERMINE",
        date_fin="2026-01-01T10:00:00Z",
        date_cloture="2026-01-01T11:00:00Z",
        commentaire_refus_cloture=None,
    )

    view = BonTravailViewSet.as_view({"patch": "updateStatus"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/updateStatus/",
        {"statut": "EN_COURS", "commentaire_refus_cloture": "Manque une verification"},
        format="json",
    )

    response = view(request, pk=bon.pk)
    bon.refresh_from_db()

    assert response.status_code == 200
    assert bon.statut == "EN_COURS"
    assert bon.date_fin is None
    assert bon.date_cloture is None
    assert bon.commentaire_refus_cloture == "Manque une verification"


@pytest.mark.django_db
def test_should_move_from_en_cours_to_termine_and_set_date_fin(api_factory):
    bon = BonTravailFactory(statut="EN_COURS", date_fin=None)

    view = BonTravailViewSet.as_view({"patch": "updateStatus"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/updateStatus/",
        {"statut": "TERMINE"},
        format="json",
    )

    response = view(request, pk=bon.pk)
    bon.refresh_from_db()

    assert response.status_code == 200
    assert bon.statut == "TERMINE"
    assert bon.date_fin is not None


@pytest.mark.django_db
def test_should_return_400_when_trying_to_finish_bt_not_in_progress(api_factory):
    bon = BonTravailFactory(statut="EN_ATTENTE")

    view = BonTravailViewSet.as_view({"patch": "updateStatus"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/updateStatus/",
        {"statut": "TERMINE"},
        format="json",
    )

    response = view(request, pk=bon.pk)

    assert response.status_code == 400
    assert "en cours" in response.data["error"]


@pytest.mark.django_db
def test_should_cloture_and_fill_date_fin_if_missing(api_factory):
    bon = BonTravailFactory(statut="TERMINE", date_fin=None, date_cloture=None)

    view = BonTravailViewSet.as_view({"patch": "updateStatus"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/updateStatus/",
        {"statut": "CLOTURE"},
        format="json",
    )

    response = view(request, pk=bon.pk)
    bon.refresh_from_db()

    assert response.status_code == 200
    assert bon.statut == "CLOTURE"
    assert bon.date_cloture is not None
    assert bon.date_fin is not None


@pytest.mark.django_db
def test_should_return_400_when_distribution_quantity_is_not_set(api_factory):
    bon = BonTravailFactory()
    consommable = ConsommableFactory()
    BonTravailConsommable.objects.create(
        bon_travail=bon,
        consommable=consommable,
        quantite_utilisee=0,
    )

    view = BonTravailViewSet.as_view({"patch": "update_consommable_distribution"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/update_consommable_distribution/",
        {"consommable_id": consommable.pk, "distribue": True},
        format="json",
    )

    response = view(request, pk=bon.pk)

    assert response.status_code == 400
    assert "Quantite non renseignee" in response.data["error"]


@pytest.mark.django_db
def test_should_return_404_when_explicit_store_stock_is_missing(api_factory):
    bon = BonTravailFactory()
    consommable = ConsommableFactory()
    BonTravailConsommable.objects.create(
        bon_travail=bon,
        consommable=consommable,
        quantite_utilisee=2,
    )
    magasin = Magasin.objects.create(nom="Magasin A")

    view = BonTravailViewSet.as_view({"patch": "update_consommable_distribution"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/update_consommable_distribution/",
        {
            "consommable_id": consommable.pk,
            "distribue": True,
            "magasin_id": magasin.pk,
        },
        format="json",
    )

    response = view(request, pk=bon.pk)

    assert response.status_code == 404
    assert "Stock introuvable" in response.data["error"]


@pytest.mark.django_db
def test_should_return_400_when_explicit_store_has_insufficient_stock(api_factory):
    bon = BonTravailFactory()
    consommable = ConsommableFactory()
    BonTravailConsommable.objects.create(
        bon_travail=bon,
        consommable=consommable,
        quantite_utilisee=4,
    )
    magasin = Magasin.objects.create(nom="Magasin A")
    Stocker.objects.create(consommable=consommable, magasin=magasin, quantite=1)

    view = BonTravailViewSet.as_view({"patch": "update_consommable_distribution"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/update_consommable_distribution/",
        {
            "consommable_id": consommable.pk,
            "distribue": True,
            "magasin_id": magasin.pk,
        },
        format="json",
    )

    response = view(request, pk=bon.pk)

    assert response.status_code == 400
    assert "Stock insuffisant" in response.data["error"]
    insuffisant = response.data["insuffisants"][0]
    assert insuffisant["magasin_id"] == magasin.pk


@pytest.mark.django_db
def test_should_confirm_distribution_with_explicit_store_selection(api_factory):
    bon = BonTravailFactory()
    consommable = ConsommableFactory()
    assoc = BonTravailConsommable.objects.create(
        bon_travail=bon,
        consommable=consommable,
        quantite_utilisee=3,
    )
    magasin = Magasin.objects.create(nom="Magasin A")
    stock = Stocker.objects.create(consommable=consommable, magasin=magasin, quantite=5)

    view = BonTravailViewSet.as_view({"patch": "update_consommable_distribution"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/update_consommable_distribution/",
        {
            "consommable_id": consommable.pk,
            "distribue": True,
            "magasin_id": magasin.pk,
        },
        format="json",
    )

    response = view(request, pk=bon.pk)
    assoc.refresh_from_db()
    stock.refresh_from_db()

    assert response.status_code == 200
    assert assoc.estConfirme is True
    assert assoc.magasin_reserve_id == magasin.pk
    assert stock.quantite == 2


@pytest.mark.django_db
def test_should_return_400_when_no_single_store_can_cover_and_total_is_insufficient(api_factory):
    bon = BonTravailFactory()
    consommable = ConsommableFactory()
    BonTravailConsommable.objects.create(
        bon_travail=bon,
        consommable=consommable,
        quantite_utilisee=9,
    )
    magasin_a = Magasin.objects.create(nom="Magasin A")
    magasin_b = Magasin.objects.create(nom="Magasin B")
    Stocker.objects.create(consommable=consommable, magasin=magasin_a, quantite=2)
    Stocker.objects.create(consommable=consommable, magasin=magasin_b, quantite=3)

    view = BonTravailViewSet.as_view({"patch": "update_consommable_distribution"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/update_consommable_distribution/",
        {"consommable_id": consommable.pk, "distribue": True},
        format="json",
    )

    response = view(request, pk=bon.pk)

    assert response.status_code == 400
    assert response.data["error"] == "Stock insuffisant"


@pytest.mark.django_db
def test_should_return_400_when_stock_is_split_across_stores_without_single_match(api_factory):
    bon = BonTravailFactory()
    consommable = ConsommableFactory()
    BonTravailConsommable.objects.create(
        bon_travail=bon,
        consommable=consommable,
        quantite_utilisee=6,
    )
    magasin_a = Magasin.objects.create(nom="Magasin A")
    magasin_b = Magasin.objects.create(nom="Magasin B")
    Stocker.objects.create(consommable=consommable, magasin=magasin_a, quantite=3)
    Stocker.objects.create(consommable=consommable, magasin=magasin_b, quantite=4)

    view = BonTravailViewSet.as_view({"patch": "update_consommable_distribution"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/update_consommable_distribution/",
        {"consommable_id": consommable.pk, "distribue": True},
        format="json",
    )

    response = view(request, pk=bon.pk)

    assert response.status_code == 400
    assert "réparti sur plusieurs magasins" in response.data["error"]


@pytest.mark.django_db
def test_should_create_di_bt_and_document_with_create_with_di(api_factory):
    utilisateur = UtilisateurFactory()
    equipement = EquipementFactory()
    type_document = TypeDocument.objects.create(nomTypeDocument="Notice")
    file_0 = SimpleUploadedFile("notice.txt", b"abc", content_type="text/plain")

    view = BonTravailViewSet.as_view({"post": "create_with_di"})
    request = api_factory.post(
        "/api/maintenance/bons-travail/create_with_di/",
        {
            "nom": "Intervention create_with_di",
            "commentaire": "Commentaire test",
            "statut_suppose": "EN_FONCTIONNEMENT",
            "equipement_id": str(equipement.pk),
            "utilisateur_id": str(utilisateur.pk),
            "type": "CORRECTIF",
            "documents": json.dumps(
                [
                    {
                        "nomDocument": "Notice BT",
                        "typeDocument_id": type_document.pk,
                    }
                ]
            ),
            "document_0": file_0,
        },
        format="multipart",
    )

    response = view(request)

    assert response.status_code == 201
    assert DemandeIntervention.objects.count() == 1
    assert BonTravail.objects.count() == 1
    assert Document.objects.count() == 1

    di = DemandeIntervention.objects.get()
    bt = BonTravail.objects.get()
    doc = Document.objects.get()

    assert di.statut == "TRANSFORMEE"
    assert di.utilisateur_id == utilisateur.pk
    assert di.equipement_id == equipement.pk
    assert bt.demande_intervention_id == di.pk
    assert bt.responsable_id == utilisateur.pk
    assert bt.documents.filter(pk=doc.pk).exists()


@pytest.mark.django_db
def test_should_rollback_create_with_di_when_document_type_is_missing(api_factory):
    utilisateur = UtilisateurFactory()
    equipement = EquipementFactory()
    file_0 = SimpleUploadedFile("notice.txt", b"abc", content_type="text/plain")

    view = BonTravailViewSet.as_view({"post": "create_with_di"})
    request = api_factory.post(
        "/api/maintenance/bons-travail/create_with_di/",
        {
            "nom": "Intervention invalide",
            "commentaire": "Rollback attendu",
            "statut_suppose": "EN_FONCTIONNEMENT",
            "equipement_id": str(equipement.pk),
            "utilisateur_id": str(utilisateur.pk),
            "type": "CORRECTIF",
            "documents": json.dumps(
                [
                    {
                        "nomDocument": "Doc sans type",
                    }
                ]
            ),
            "document_0": file_0,
        },
        format="multipart",
    )

    response = view(request)

    assert response.status_code == 400
    assert DemandeIntervention.objects.count() == 0
    assert BonTravail.objects.count() == 0
    assert Document.objects.count() == 0


@pytest.mark.django_db
def test_should_return_400_when_partial_update_modifies_demande_or_equipement(api_factory):
    bon = BonTravailFactory()

    view = BonTravailViewSet.as_view({"patch": "partial_update"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/",
        {"equipement_id": 12345},
        format="json",
    )

    response = view(request, pk=bon.pk)

    assert response.status_code == 400
    assert "interdite" in response.data["error"]


@pytest.mark.django_db
def test_should_set_date_assignation_when_assigne_ids_change_in_partial_update(api_factory):
    bon = BonTravailFactory(date_assignation=None)
    technicien = UtilisateurFactory()

    view = BonTravailViewSet.as_view({"patch": "partial_update"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/",
        {"utilisateur_assigne_ids": [technicien.pk]},
        format="json",
    )

    response = view(request, pk=bon.pk)
    bon.refresh_from_db()

    assert response.status_code == 200
    assert bon.utilisateur_assigne.filter(pk=technicien.pk).exists()
    assert bon.date_assignation is not None


@pytest.mark.django_db
def test_should_return_400_when_assigne_a_without_utilisateur_id(api_factory):
    view = BonTravailViewSet.as_view({"get": "assigne_a"})
    request = api_factory.get("/api/maintenance/bons-travail/assigne_a/")

    response = view(request)

    assert response.status_code == 400
    assert "utilisateur_id" in response.data["error"]


@pytest.mark.django_db
def test_should_filter_assigned_bons_by_utilisateur(api_factory):
    technicien = UtilisateurFactory()
    other = UtilisateurFactory()
    bt_target = BonTravailFactory()
    bt_other = BonTravailFactory()
    bt_target.utilisateur_assigne.add(technicien)
    bt_other.utilisateur_assigne.add(other)

    view = BonTravailViewSet.as_view({"get": "assigne_a"})
    request = api_factory.get(
        "/api/maintenance/bons-travail/assigne_a/",
        {"utilisateur_id": technicien.pk},
    )

    response = view(request)

    assert response.status_code == 200
    ids = [item["id"] for item in response.data["results"]]
    assert ids == [bt_target.id]


@pytest.mark.django_db
def test_should_return_400_when_delink_document_without_document_id(api_factory):
    bon = BonTravailFactory()

    view = BonTravailViewSet.as_view({"patch": "delink_document"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/delink_document/",
        {},
        format="json",
    )

    response = view(request, pk=bon.pk)

    assert response.status_code == 400
    assert "document_id" in response.data["error"]


@pytest.mark.django_db
def test_should_return_404_when_delink_document_not_linked(api_factory):
    bon = BonTravailFactory()

    view = BonTravailViewSet.as_view({"patch": "delink_document"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/delink_document/",
        {"document_id": 999999},
        format="json",
    )

    response = view(request, pk=bon.pk)

    assert response.status_code == 404
    assert "n'est pas lié" in response.data["error"]


@pytest.mark.django_db
def test_should_delink_document_from_bon_travail(api_factory):
    bon = BonTravailFactory()
    type_document = TypeDocument.objects.create(nomTypeDocument="Notice")
    document = Document.objects.create(
        nomDocument="Doc BT",
        cheminAcces=SimpleUploadedFile("doc.txt", b"abc", content_type="text/plain"),
        typeDocument=type_document,
    )
    bon.documents.add(document)

    view = BonTravailViewSet.as_view({"patch": "delink_document"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/delink_document/",
        {"document_id": document.pk},
        format="json",
    )

    response = view(request, pk=bon.pk)
    bon.refresh_from_db()

    assert response.status_code == 200
    assert bon.documents.filter(pk=document.pk).exists() is False


@pytest.mark.django_db
def test_should_return_400_when_ajouter_document_without_document_id(api_factory):
    bon = BonTravailFactory()

    view = BonTravailViewSet.as_view({"post": "ajouter_document"})
    request = api_factory.post(
        f"/api/maintenance/bons-travail/{bon.pk}/ajouter_document/",
        {},
        format="json",
    )

    response = view(request, pk=bon.pk)

    assert response.status_code == 400
    assert "document_id" in response.data["error"]


@pytest.mark.django_db
def test_should_return_400_when_ajouter_document_with_non_integer_id(api_factory):
    bon = BonTravailFactory()

    view = BonTravailViewSet.as_view({"post": "ajouter_document"})
    request = api_factory.post(
        f"/api/maintenance/bons-travail/{bon.pk}/ajouter_document/",
        {"document_id": "abc"},
        format="json",
    )

    response = view(request, pk=bon.pk)

    assert response.status_code == 400
    assert "entier" in response.data["error"]


@pytest.mark.django_db
def test_should_return_400_when_ajouter_document_with_unknown_document(api_factory):
    bon = BonTravailFactory()

    view = BonTravailViewSet.as_view({"post": "ajouter_document"})
    request = api_factory.post(
        f"/api/maintenance/bons-travail/{bon.pk}/ajouter_document/",
        {"document_id": 999999},
        format="json",
    )

    response = view(request, pk=bon.pk)

    assert response.status_code == 400
    assert "introuvable" in response.data["error"]


@pytest.mark.django_db
def test_should_add_document_to_bon_travail(api_factory):
    bon = BonTravailFactory()
    type_document = TypeDocument.objects.create(nomTypeDocument="Notice")
    document = Document.objects.create(
        nomDocument="Doc BT",
        cheminAcces=SimpleUploadedFile("doc2.txt", b"abc", content_type="text/plain"),
        typeDocument=type_document,
    )

    view = BonTravailViewSet.as_view({"post": "ajouter_document"})
    request = api_factory.post(
        f"/api/maintenance/bons-travail/{bon.pk}/ajouter_document/",
        {"document_id": document.pk},
        format="json",
    )

    response = view(request, pk=bon.pk)
    bon.refresh_from_db()

    assert response.status_code == 200
    assert bon.documents.filter(pk=document.pk).exists()


@pytest.mark.django_db
def test_should_be_idempotent_when_adding_already_linked_document(api_factory):
    bon = BonTravailFactory()
    type_document = TypeDocument.objects.create(nomTypeDocument="Notice")
    document = Document.objects.create(
        nomDocument="Doc BT",
        cheminAcces=SimpleUploadedFile("doc3.txt", b"abc", content_type="text/plain"),
        typeDocument=type_document,
    )
    bon.documents.add(document)

    view = BonTravailViewSet.as_view({"post": "ajouter_document"})
    request = api_factory.post(
        f"/api/maintenance/bons-travail/{bon.pk}/ajouter_document/",
        {"document_id": document.pk},
        format="json",
    )

    response = view(request, pk=bon.pk)

    assert response.status_code == 200
    assert bon.documents.filter(pk=document.pk).count() == 1


@pytest.mark.django_db
def test_should_list_stock_without_termine_and_cloture(api_factory):
    bt_en_attente = BonTravailFactory(statut="EN_ATTENTE")
    bt_en_cours = BonTravailFactory(statut="EN_COURS")
    BonTravailFactory(statut="TERMINE")
    BonTravailFactory(statut="CLOTURE")

    view = BonTravailViewSet.as_view({"get": "list_stock"})
    request = api_factory.get("/api/maintenance/bons-travail/list_stock/")

    response = view(request)

    assert response.status_code == 200
    ids = {item["id"] for item in response.data["results"]}
    assert bt_en_attente.id in ids
    assert bt_en_cours.id in ids
    assert len(ids) == 2


@pytest.mark.django_db
def test_should_set_archive_flag_via_set_archive_action(api_factory):
    bon = BonTravailFactory(archive=False)

    view = BonTravailViewSet.as_view({"patch": "set_archive"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/set-archive/",
        {"archive": True},
        format="json",
    )

    response = view(request, pk=bon.pk)
    bon.refresh_from_db()

    assert response.status_code == 200
    assert response.data["archive"] is True
    assert bon.archive is True


@pytest.mark.django_db
def test_should_return_400_when_set_archive_without_archive_value(api_factory):
    bon = BonTravailFactory(archive=False)

    view = BonTravailViewSet.as_view({"patch": "set_archive"})
    request = api_factory.patch(
        f"/api/maintenance/bons-travail/{bon.pk}/set-archive/",
        {},
        format="json",
    )

    response = view(request, pk=bon.pk)

    assert response.status_code == 400
    assert "archive" in response.data["error"]


@pytest.mark.django_db
def test_should_exclude_archived_bons_from_list(api_factory):
    visible = BonTravailFactory(archive=False, statut="EN_ATTENTE")
    BonTravailFactory(archive=True, statut="EN_ATTENTE")

    view = BonTravailViewSet.as_view({"get": "list"})
    request = api_factory.get("/api/maintenance/bons-travail/")

    response = view(request)

    assert response.status_code == 200
    ids = {item["id"] for item in _extract_items(response.data)}
    assert visible.id in ids
    assert len(ids) == 1


@pytest.mark.django_db
def test_should_exclude_cloture_from_list_by_default(api_factory):
    bt_open = BonTravailFactory(statut="EN_COURS")
    BonTravailFactory(statut="CLOTURE")

    view = BonTravailViewSet.as_view({"get": "list"})
    request = api_factory.get("/api/maintenance/bons-travail/")

    response = view(request)

    assert response.status_code == 200
    ids = {item["id"] for item in _extract_items(response.data)}
    assert bt_open.id in ids
    assert len(ids) == 1


@pytest.mark.django_db
def test_should_include_cloture_when_cloture_query_param_is_true(api_factory):
    bt_open = BonTravailFactory(statut="EN_COURS")
    bt_closed = BonTravailFactory(statut="CLOTURE")

    view = BonTravailViewSet.as_view({"get": "list"})
    request = api_factory.get("/api/maintenance/bons-travail/", {"cloture": "true"})

    response = view(request)

    assert response.status_code == 200
    ids = {item["id"] for item in _extract_items(response.data)}
    assert bt_open.id in ids
    assert bt_closed.id in ids
