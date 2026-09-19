import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

SECRET_KEY = (
    os.getenv("SECRET_KEY") or "django-insecure-tp-gimao-2026-xK8mP3qL9nR7vW2jH5tY1uA4sD6fG0cE"
)

DEBUG = os.getenv("DEBUG", "False").strip().lower() in ("true", "1", "yes")
ENABLE_SQL_LOGGING = os.getenv("ENABLE_SQL_LOGGING", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

_allowed_hosts_env = os.getenv("ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts_env.split(",") if h.strip()] or [
    "localhost",
    "127.0.0.1",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_crontab",
    "rest_framework",
    "django_filters",
    "corsheaders",
    "drf_yasg",
    "utilisateur",
    "security",
    "donnees",
    "stock",
    "equipement",
    "maintenance",
    "tasks",
    "exportData",
    "importData",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # Doit être en premier
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # 'django.middleware.csrf.CsrfViewMiddleware',  # Désactivé
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "utilisateur.middleware.CurrentUserMiddleware",
    "gimao.middleware.ApiTokenMiddleware",  # Ajout du middleware personnalisé
]

# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': [
#         'rest_framework.authentication.SessionAuthentication',
#     ],
#     'DEFAULT_RENDERER_CLASSES': [
#         'rest_framework.renderers.JSONRenderer',
#     ],
# }
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

ROOT_URLCONF = "gimao.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "gimao.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME") or os.getenv("MYSQL_DATABASE", "gimao"),
        "USER": os.getenv("DB_USER") or os.getenv("MYSQL_USER", "root"),
        "PASSWORD": os.getenv("DB_PASSWORD") or os.getenv("MYSQL_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": ("SET sql_mode='STRICT_TRANS_TABLES';"),
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = "/app/staticfiles"

# ============================================
# CORS Configuration - CORRIGÉ
# ============================================
CORS_ALLOW_ALL_ORIGINS = True  # En développement uniquement
CORS_ALLOW_CREDENTIALS = True

# Ou en production, utilisez plutôt :
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost",
#     "http://localhost:8080",
#     "http://127.0.0.1",
#     "http://127.0.0.1:8080",
# ]

# Headers autorisés
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

# ============================================
# Logging
# ============================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "cron_file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(MEDIA_ROOT, "cron_logs/cron.log"),
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "tasks": {
            "handlers": ["cron_file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

if ENABLE_SQL_LOGGING:
    LOGGING["loggers"]["django.db.backends"] = {
        "handlers": ["console"],
        "level": "DEBUG",
        "propagate": False,
    }

# ============================================
# Cron Jobs
# ============================================
CRONJOBS = [
    ("0 12 * * *", "tasks.updateBtStatus.update_bt_status"),
    ("0 0 * * *", "tasks.updateBtStatus.update_bt_status"),
    ("0 3 * * *", "tasks.counterCron.update_counter"),
    ("0 0 * * *", "tasks.updateCalendarDates.update_calendar_counters"),
    ("0 0 * * *", "tasks.deletedExpiredTokens.delete_useless_tokens"),
]
