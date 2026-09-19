import datetime
import logging

from django.utils import timezone

from equipement.models import Compteur
from maintenance.models import (
    BonTravail,
    BonTravailConsommable,
    DemandeIntervention,
)
from utilisateur.models import Utilisateur

logger = logging.getLogger("tasks")


def update_counter():
    try:
        counters = Compteur.objects.filter(equipement__archive=False)
        counters_on_alert = 0
        BT_created = 0

        # Attempt to get a default system user or admin for auto-generated requests
        # In a real scenario, you might have a dedicated 'system' user.
        system_user = Utilisateur.objects.filter(
            role__nomRole__icontains="Responsable GMAO"
        ).first()
        if not system_user:
            system_user = Utilisateur.objects.first()

        for counter in counters:
            if counter.valeurCourante is None:
                logger.warning(f"Counter {counter.id} ignoré (valeurCourante nulle)")
                continue

            # Détection calendaire (même logique que dans DeclenchementViewSet)
            is_calendaire = counter.type == "Calendaire" or counter.unite == "date"

            # Récupérer les déclenchements associés (table declencher)
            declenchements = counter.declenchements.all()

            for declencher in declenchements:
                # Récupérer le plan de maintenance associé
                plan_maintenance = declencher.planMaintenance

                if declencher.prochaineMaintenance is None:
                    continue

                # Seuil effectif : la prochaine maintenance, anticipee si demande.
                # NB: on compare directement a prochaineMaintenance (et non a un
                # pourcentage de ecartInterventions) car ecartInterventions est
                # stocke dans une unite differente pour les compteurs calendaires
                # (millisecondes) que valeurCourante/prochaineMaintenance (jours
                # ordinaux) : comparer les deux provoquait un decalage d'unites
                # qui empechait tout declenchement.
                seuil_effectif = declencher.prochaineMaintenance
                if is_calendaire and declencher.anticipationJours:
                    seuil_effectif = declencher.prochaineMaintenance - declencher.anticipationJours

                if counter.valeurCourante >= seuil_effectif:
                    if plan_maintenance:
                        # Check if a BT already exists and is active for this PlanMaintenance
                        existing_bt = BonTravail.objects.filter(
                            demande_intervention__equipement=counter.equipement,
                            nom__icontains=plan_maintenance.nom,
                            archive=False,
                            statut__in=["EN_ATTENTE", "EN_COURS", "EN_RETARD"],
                        ).exists()

                        if existing_bt:
                            continue

                        if not system_user:
                            logger.error(
                                "Aucun utilisateur trouvé pour créer la demande d'intervention."
                            )
                            continue

                        # Create DemandeIntervention
                        demande = DemandeIntervention.objects.create(
                            nom=f"Maintenance Préventive : {plan_maintenance.nom}",
                            statut="TRANSFORMEE",  # Immediately transformed to BT
                            date_creation=timezone.now(),
                            date_changementStatut=timezone.now(),
                            utilisateur=system_user,
                            equipement=counter.equipement,
                            commentaire=f"Généré automatiquement par le compteur {counter.nomCompteur} (Valeur: {counter.valeurCourante})",
                        )

                        # Create BonTravail
                        bt = BonTravail.objects.create(
                            nom=f"Intervention : {plan_maintenance.nom}",
                            type="PREVENTIF",
                            statut="EN_ATTENTE",
                            demande_intervention=demande,
                            responsable=system_user,
                            commentaire=plan_maintenance.commentaire,
                        )

                        # Copy consumables with quantities
                        for pm_conso in plan_maintenance.planmaintenanceconsommable_set.all():
                            BonTravailConsommable.objects.create(
                                bon_travail=bt,
                                consommable=pm_conso.consommable,
                                quantite_utilisee=pm_conso.quantite_necessaire,
                            )

                        BT_created += 1
                    counters_on_alert += 1

        logger.info(
            f"[{datetime.datetime.now().strftime('%Y-%m-%d')}] Compteurs en alerte: {counters_on_alert}; BonTravail crees: {BT_created}"
        )

        return BT_created

    except Exception:
        logger.exception("Erreur dans le cron update_counter")
        raise
