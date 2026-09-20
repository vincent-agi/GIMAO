"""Service de notification email generique (cf. TUS-013).

Socle reutilisable pour toutes les alertes d'echeance du projet (controle
technique, permis de conduire, contrat LLD...). Un seul template email
generique est utilise ; ``event`` sert uniquement d'etiquette de tracabilite
dans les logs et n'est pas encore utilise pour choisir un template distinct
(cf. TODO.md, ce comportement pourra evoluer si des besoins de mise en
forme specifiques par evenement apparaissent).
"""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

ECHEANCE_EMAIL_TEMPLATE = "notifications/echeance_email.html"


def send_notification(event: str, recipients: list[str], context: dict) -> bool:
    """Envoie une notification email pour un evenement metier donne.

    Args:
        event: Identifiant court de l'evenement (ex. "echeance_controle_technique"),
            utilise uniquement pour la tracabilite dans les logs.
        recipients: Adresses email destinataires. Aucun envoi n'est tente si
            la liste est vide.
        context: Contexte de rendu du template email. Doit au minimum
            contenir ``subject`` (objet du mail) et ``titre``/``message``
            (corps). Voir ``notifications/templates/notifications/echeance_email.html``.

    Returns:
        ``True`` si l'email a ete transmis au backend d'envoi Django,
        ``False`` si aucun destinataire n'a ete fourni (envoi ignore).
    """
    if not recipients:
        logger.warning("Notification '%s' ignoree : aucun destinataire fourni", event)
        return False

    subject = context.get("subject") or event
    html_body = render_to_string(ECHEANCE_EMAIL_TEMPLATE, context)

    email = EmailMultiAlternatives(
        subject=subject,
        body=context.get("message", ""),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=False)

    logger.info("Notification '%s' envoyee a %s", event, recipients)
    return True
