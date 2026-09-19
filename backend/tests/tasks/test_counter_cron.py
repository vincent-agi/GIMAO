import pytest
from django.utils import timezone

from maintenance.models import BonTravail, BonTravailConsommable, DemandeIntervention
from tasks.counterCron import update_counter
from tests.factories import (
    BonTravailFactory,
    CompteurFactory,
    ConsommableFactory,
    DeclencherFactory,
    DemandeInterventionFactory,
    EquipementFactory,
    PlanMaintenanceConsommableFactory,
    PlanMaintenanceFactory,
    RoleFactory,
    UtilisateurFactory,
)


@pytest.mark.django_db
def test_should_create_bt_when_counter_reaches_85_percent():
    """
    Test la règle métier critique :
    Si un compteur dépasse 85% de son seuil (ecartInterventions),
    le système doit générer automatiquement une Demande d'Intervention et un Bon de Travail.
    """

    # ==========================================
    # GIVEN (Arrangement des données)
    # ==========================================
    # 1. Utilisateur système (requis par le script)
    role_resp = RoleFactory(nomRole="Responsable GMAO")
    admin = UtilisateurFactory(role=role_resp)

    # 2. Equipement et plan de maintenance
    equipement = EquipementFactory(designation="Moteur Principal")
    plan = PlanMaintenanceFactory(nom="Graissage Roulements", equipement=equipement)

    # 3. Compteur simulé à 86% du seuil (86 unités sur un seuil de 100)
    compteur = CompteurFactory(equipement=equipement, valeurCourante=86.0)

    # 4. Paramétrage du déclenchement
    DeclencherFactory(
        compteur=compteur,
        planMaintenance=plan,
        derniereIntervention=0,
        ecartInterventions=100.0,  # Le seuil à atteindre est 100
        prochaineMaintenance=100.0,
    )

    # ==========================================
    # WHEN (Action exercée)
    # ==========================================
    # On déclenche manuellement la tâche CRON
    update_counter()

    # ==========================================
    # THEN (Vérification des conséquences)
    # ==========================================

    # 1. Vérification de la Demande d'Intervention (DI)
    di = DemandeIntervention.objects.filter(equipement=equipement).first()
    assert di is not None, "Une demande d'intervention aurait dû être créée (86% > 85%)."
    assert "Graissage Roulements" in di.nom
    assert di.statut == "TRANSFORMEE"
    assert di.utilisateur.id == admin.id

    # 2. Vérification du Bon de Travail (BT) automatiquement rattaché
    bt = BonTravail.objects.filter(demande_intervention=di).first()
    assert bt is not None, "Un bon de travail aurait dû être créé en même temps que la DI."
    assert "Graissage Roulements" in bt.nom
    assert bt.type == "PREVENTIF"
    assert bt.statut == "EN_ATTENTE"
    assert bt.responsable.id == admin.id


@pytest.mark.django_db
def test_should_not_create_duplicate_bt_when_active_bt_exists():
    """
    Si un BT actif (EN_ATTENTE, EN_COURS ou EN_RETARD) existe déjà pour ce
    plan de maintenance, un deuxième appel à update_counter() ne doit pas
    créer de nouvelles DI/BT.
    """
    # GIVEN
    role_resp = RoleFactory(nomRole="Responsable GMAO")
    UtilisateurFactory(role=role_resp)

    equipement = EquipementFactory()
    plan = PlanMaintenanceFactory(nom="Vidange Huile", equipement=equipement)
    compteur = CompteurFactory(equipement=equipement, valeurCourante=90.0)
    DeclencherFactory(
        compteur=compteur,
        planMaintenance=plan,
        derniereIntervention=0,
        ecartInterventions=100.0,
        prochaineMaintenance=100.0,
    )

    # Un premier appel crée le BT
    update_counter()
    assert BonTravail.objects.filter(demande_intervention__equipement=equipement).count() == 1

    # WHEN — deuxième appel
    update_counter()

    # THEN — toujours 1 seul BT, pas de doublon
    assert BonTravail.objects.filter(demande_intervention__equipement=equipement).count() == 1


@pytest.mark.django_db
def test_should_not_create_bt_when_counter_is_below_threshold():
    """
    Si le compteur est sous 85% du seuil, aucune DI ni BT ne doit être créé.
    """
    # GIVEN
    role_resp = RoleFactory(nomRole="Responsable GMAO")
    UtilisateurFactory(role=role_resp)

    equipement = EquipementFactory()
    plan = PlanMaintenanceFactory(nom="Contrôle Filtre", equipement=equipement)
    # 50 unités sur un seuil de 100 = 50% < 85%
    compteur = CompteurFactory(equipement=equipement, valeurCourante=50.0)
    DeclencherFactory(
        compteur=compteur,
        planMaintenance=plan,
        derniereIntervention=0,
        ecartInterventions=100.0,
        prochaineMaintenance=100.0,
    )

    # WHEN
    update_counter()

    # THEN — aucune DI ni BT créé
    assert DemandeIntervention.objects.filter(equipement=equipement).count() == 0
    assert BonTravail.objects.count() == 0


@pytest.mark.django_db
def test_should_skip_counter_when_valeur_courante_is_none():
    """
    Un compteur avec valeurCourante=None doit être ignoré silencieusement.
    Aucune DI ni BT ne doit être créé.
    """
    from types import SimpleNamespace
    from unittest.mock import patch

    # GIVEN
    RoleFactory(nomRole="Responsable GMAO")
    UtilisateurFactory()

    fake_counter = SimpleNamespace(
        id=999,
        valeurCourante=None,
        declenchements=SimpleNamespace(all=lambda: []),
    )

    # WHEN
    with patch("tasks.counterCron.Compteur.objects.filter", return_value=[fake_counter]):
        update_counter()

    # THEN — aucune action
    assert DemandeIntervention.objects.count() == 0


@pytest.mark.django_db
def test_should_skip_declencher_when_parametres_are_none():
    """
    Si derniereIntervention, ecartInterventions ou prochaineMaintenance est None
    dans le Declencher, le compteur doit être ignoré.
    """
    from types import SimpleNamespace
    from unittest.mock import patch

    # GIVEN
    RoleFactory(nomRole="Responsable GMAO")
    UtilisateurFactory()

    fake_declencher = SimpleNamespace(
        planMaintenance=SimpleNamespace(nom="Plan test", commentaire=""),
        derniereIntervention=None,
        ecartInterventions=100.0,
        prochaineMaintenance=100.0,
    )
    fake_counter = SimpleNamespace(
        id=1000,
        valeurCourante=90.0,
        declenchements=SimpleNamespace(all=lambda: [fake_declencher]),
    )

    # WHEN
    with patch("tasks.counterCron.Compteur.objects.filter", return_value=[fake_counter]):
        update_counter()

    # THEN
    assert DemandeIntervention.objects.count() == 0


@pytest.mark.django_db
def test_should_not_create_bt_when_no_system_user_exists():
    """
    Si aucun utilisateur n'est trouvé par le cron (ni Responsable GMAO, ni fallback),
    aucun BT ne doit être créé et une erreur doit être loggée.
    On mock Utilisateur dans le module pour éviter les contraintes FK PROTECT.
    """
    from unittest.mock import MagicMock, patch

    # GIVEN — compteur en alerte, équipement valide (un vrai user est en base pour les FK)
    equipement = EquipementFactory()
    plan = PlanMaintenanceFactory(equipement=equipement)
    compteur = CompteurFactory(equipement=equipement, valeurCourante=90.0)
    DeclencherFactory(
        compteur=compteur,
        planMaintenance=plan,
        derniereIntervention=0,
        ecartInterventions=100.0,
        prochaineMaintenance=100.0,
    )

    # On simule que le cron ne trouve aucun utilisateur système
    mock_empty_qs = MagicMock()
    mock_empty_qs.first.return_value = None

    # WHEN
    with patch("tasks.counterCron.Utilisateur") as mock_utilisateur:
        mock_utilisateur.objects.filter.return_value = mock_empty_qs
        mock_utilisateur.objects.first.return_value = None
        update_counter()

    # THEN — pas de DI ni BT créé
    assert DemandeIntervention.objects.filter(equipement=equipement).count() == 0
    assert BonTravail.objects.count() == 0


@pytest.mark.django_db
def test_should_copy_plan_consommables_to_bt():
    """
    Quand un BT est créé automatiquement, les consommables du PlanMaintenance
    doivent être copiés dans le BonTravailConsommable avec la bonne quantité.
    """
    # GIVEN
    role_resp = RoleFactory(nomRole="Responsable GMAO")
    UtilisateurFactory(role=role_resp)

    equipement = EquipementFactory()
    plan = PlanMaintenanceFactory(nom="Remplacement Filtre", equipement=equipement)

    # 2 consommables associés au plan
    conso1 = ConsommableFactory(designation="Filtre à huile")
    conso2 = ConsommableFactory(designation="Joint")
    PlanMaintenanceConsommableFactory(
        plan_maintenance=plan, consommable=conso1, quantite_necessaire=1
    )
    PlanMaintenanceConsommableFactory(
        plan_maintenance=plan, consommable=conso2, quantite_necessaire=3
    )

    compteur = CompteurFactory(equipement=equipement, valeurCourante=90.0)
    DeclencherFactory(
        compteur=compteur,
        planMaintenance=plan,
        derniereIntervention=0,
        ecartInterventions=100.0,
        prochaineMaintenance=100.0,
    )

    # WHEN
    update_counter()

    # THEN — le BT existe et contient les 2 consommables avec les bonnes quantités
    bt = BonTravail.objects.filter(demande_intervention__equipement=equipement).first()
    assert bt is not None

    bt_conso = BonTravailConsommable.objects.filter(bon_travail=bt)
    assert bt_conso.count() == 2

    qtés = {bc.consommable.designation: bc.quantite_utilisee for bc in bt_conso}
    assert qtés["Filtre à huile"] == 1
    assert qtés["Joint"] == 3
