import hashlib
import secrets
from datetime import timedelta

from django.db import models
from django.utils import timezone

from utilisateur.models import Utilisateur


class ApiToken(models.Model):
    """
    Token d'authentification pour l'API REST.

    Le token brut (généré par ``create_token``) n'est jamais stocké : seul son hash SHA-256
    est conservé. La durée de validité est de 24 heures à partir de la création.
    Un token peut être révoqué explicitement via ``is_revoked`` sans attendre son expiration.
    Le middleware ``ApiTokenMiddleware`` vérifie ce modèle à chaque requête entrante.
    """

    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    user = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="api_tokens")

    created_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField()

    is_revoked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.id} - {self.user.nomUtilisateur} - {self.token_hash[:10]}"

    def is_valid(self):
        return not self.is_revoked and self.valid_until > timezone.now()


def create_token(user):
    """
    Génère un token d'authentification pour un utilisateur et le persiste en base.

    Retourne le token brut (à transmettre au client). Seul le hash SHA-256 est stocké.
    Le token expire 24 heures après sa création.
    """
    token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(token.encode()).hexdigest()

    ApiToken.objects.create(
        token_hash=token_hash, user=user, valid_until=timezone.now() + timedelta(days=1)
    )

    return token
