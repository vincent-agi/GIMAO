"""
Settings de test : surcharge la base de données MySQL par SQLite en mémoire
pour permettre l'exécution des tests sans Docker ni serveur MySQL.
"""

from .settings import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Désactiver les logs CRON pendant les tests
CRONTAB_COMMAND_SUFFIX = ""

# Les tests API existants utilisent majoritairement APIClient sans token explicite.
# On désactive le middleware token pour garder un environnement de test stable.
MIDDLEWARE = [
    middleware for middleware in MIDDLEWARE if middleware != "gimao.middleware.ApiTokenMiddleware"
]
