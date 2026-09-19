"""Alerte email avant échéance de contrôle technique (US-012).

Réutilise le ``Declencher`` calendaire créé par
``equipement.services.brancher_controle_technique_sur_declencheur``
(TUS-012) : dès que sa valeur courante atteint le seuil anticipé (même
condition que le cron ``update_counter``, cf. ``tasks.counterCron``), un
email est envoyé aux responsables GMAO. La table ``NotificationEnvoyee``
empêche l'envoi d'un doublon à chaque exécution tant que la situation n'a
pas changé.
"""

import logging

from equipement.models import Declencher
from equipement.services import CT_COMPTEUR_NOM, CT_PLAN_MAINTENANCE_NOM, ordinal_days_to_date
from notifications.models import NotificationEnvoyee
from notifications.services import send_notification
from utilisateur.models import Utilisateur

logger = logging.getLogger("tasks")

EVENT_ECHEANCE_CONTROLE_TECHNIQUE = "echeance_controle_technique"


def _destinataires_responsables_gmao() -> list[str]:
    """Retourne les emails des utilisateurs actifs ayant le rôle Responsable GMAO."""
    return list(
        Utilisateur.objects.filter(role__nomRole__icontains="Responsable GMAO", actif=True)
        .exclude(email="")
        .values_list("email", flat=True)
    )


def check_ct_echeances() -> int:
    """Envoie une alerte pour chaque contrôle technique dont l'échéance approche.

    Un ``Declencher`` calendaire de contrôle technique est considéré à
    échéance selon la même règle que le cron préventif générique : sa
    valeur courante a atteint ``prochaineMaintenance - anticipationJours``.

    Returns:
        Le nombre de notifications effectivement envoyées lors de cette
        exécution (les cibles déjà notifiées ne sont pas recomptées).
    """
    declencheurs = Declencher.objects.filter(
        compteur__nomCompteur=CT_COMPTEUR_NOM,
        planMaintenance__nom=CT_PLAN_MAINTENANCE_NOM,
    ).select_related("compteur", "compteur__equipement")

    destinataires = _destinataires_responsables_gmao()
    notifications_envoyees = 0

    for declencher in declencheurs:
        anticipation = declencher.anticipationJours or 0
        seuil_effectif = declencher.prochaineMaintenance - anticipation

        if declencher.compteur.valeurCourante < seuil_effectif:
            continue

        cle_cible = str(declencher.id)
        deja_envoyee = NotificationEnvoyee.objects.filter(
            event=EVENT_ECHEANCE_CONTROLE_TECHNIQUE, cle_cible=cle_cible
        ).exists()
        if deja_envoyee:
            continue

        equipement = declencher.compteur.equipement
        echeance = ordinal_days_to_date(declencher.prochaineMaintenance)

        sent = send_notification(
            event=EVENT_ECHEANCE_CONTROLE_TECHNIQUE,
            recipients=destinataires,
            context={
                "subject": f"Contrôle technique à échéance — {equipement.designation}",
                "titre": "Contrôle technique à échéance",
                "message": (
                    f"Le véhicule « {equipement.designation} » arrive à échéance de "
                    "contrôle technique."
                ),
                "echeance": echeance.isoformat(),
            },
        )

        if sent:
            NotificationEnvoyee.objects.create(
                event=EVENT_ECHEANCE_CONTROLE_TECHNIQUE, cle_cible=cle_cible
            )
            notifications_envoyees += 1

    logger.info("[check_ct_echeances] %s notification(s) envoyee(s)", notifications_envoyees)
    return notifications_envoyees
