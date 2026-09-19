from django.db import models


class NotificationEnvoyee(models.Model):
    """
    Trace qu'une notification a deja ete envoyee pour un evenement et une cible donnes.

    Evite le renvoi d'un meme email a chaque execution d'un job planifie
    (ex. ``check_ct_echeances``, US-012) tant que la situation n'a pas
    change : la paire ``(event, cle_cible)`` est unique, un nouvel envoi
    pour la meme cible et le meme evenement est donc idempotent au niveau
    base de donnees.

    Attributes:
        event: Identifiant de l'evenement notifie (ex. "echeance_controle_technique").
        cle_cible: Identifiant de l'entite notifiee (ex. l'id du Declencher
            concerne), sous forme de chaine pour rester generique entre
            evenements portant sur des modeles differents.
        date_envoi: Date et heure d'envoi de la notification.
    """

    event = models.CharField(max_length=100)
    cle_cible = models.CharField(max_length=100)
    date_envoi = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gimao_notification_envoyee"
        verbose_name = "Notification envoyée"
        verbose_name_plural = "Notifications envoyées"
        constraints = [
            models.UniqueConstraint(
                fields=["event", "cle_cible"], name="unique_notification_event_cible"
            ),
        ]

    def __str__(self):
        return f"{self.id} - {self.event} - {self.cle_cible}"
