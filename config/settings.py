"""
Configuration principale du projet FactCheck Mada.

Les valeurs sensibles sont lues depuis le fichier .env (voir .env.example).
Le projet fonctionne avec SQLite pour le MVP et peut basculer vers PostgreSQL
grâce aux variables d'environnement, sans modifier le code.
"""

import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Chemins et environnement
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

# Charge les variables du fichier .env s'il existe.
load_dotenv(BASE_DIR / ".env")


def lire_bool(nom: str, defaut: bool = False) -> bool:
    """Convertit une variable d'environnement en booléen."""
    valeur = os.getenv(nom)
    if valeur is None:
        return defaut
    return valeur.strip().lower() in {"1", "true", "vrai", "oui", "yes", "on"}


def lire_liste(nom: str, defaut: str = "") -> list[str]:
    """Convertit une liste séparée par des virgules en liste Python."""
    valeur = os.getenv(nom, defaut)
    return [element.strip() for element in valeur.split(",") if element.strip()]


def lire_entier(nom: str, defaut: int) -> int:
    """Lit un entier depuis l'environnement avec une valeur de repli."""
    try:
        return int(os.getenv(nom, str(defaut)))
    except (TypeError, ValueError):
        return defaut


# ---------------------------------------------------------------------------
# Sécurité
# ---------------------------------------------------------------------------

SECRET_KEY = os.getenv(
    "CLE_SECRETE",
    "cle-de-developpement-a-remplacer-obligatoirement-en-production",
)
DEBUG = lire_bool("MODE_DEBUG", True)

if not DEBUG and SECRET_KEY.startswith(
    ("cle-de-developpement", "remplacez-cette-cle")
):
    raise ImproperlyConfigured(
        "Définissez une variable CLE_SECRETE robuste dans .env avant de "
        "désactiver le mode DEBUG."
    )

ALLOWED_HOSTS = lire_liste(
    "HOTES_AUTORISES",
    "localhost,127.0.0.1,testserver",
)

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Bibliothèques tierces
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    # Application métier
    "investigation",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Base de données
# ---------------------------------------------------------------------------

MOTEUR_BASE = os.getenv("BASE_DONNEES_MOTEUR", "sqlite3").strip().lower()

if MOTEUR_BASE in {"postgres", "postgresql"}:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("BASE_DONNEES_NOM", "factcheck_mada"),
            "USER": os.getenv("BASE_DONNEES_UTILISATEUR", "factcheck"),
            "PASSWORD": os.getenv("BASE_DONNEES_MOT_DE_PASSE", ""),
            "HOST": os.getenv("BASE_DONNEES_HOTE", "localhost"),
            "PORT": os.getenv("BASE_DONNEES_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / os.getenv("BASE_DONNEES_NOM", "db.sqlite3"),
        }
    }

# ---------------------------------------------------------------------------
# Authentification et JWT
# ---------------------------------------------------------------------------

AUTH_USER_MODEL = "investigation.Journaliste"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Durées de vie des jetons, configurables sans redéploiement du code.
DUREE_ACCES = lire_entier("DUREE_JETON_ACCES_MINUTES", 60)
DUREE_RAFRAICHISSEMENT = lire_entier("DUREE_JETON_RAFRAICHISSEMENT_JOURS", 7)

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=DUREE_ACCES),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=DUREE_RAFRAICHISSEMENT),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
}

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_PAGINATION_CLASS": "investigation.pagination.PaginationFrancaise",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.ScopedRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/minute",
        "user": "1000/minute",
        "authentification": "100/minute",
    },
    "EXCEPTION_HANDLER": "investigation.gestion_erreurs.gestionnaire_exceptions_francais",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

# ---------------------------------------------------------------------------
# Documentation OpenAPI et Swagger
# ---------------------------------------------------------------------------

DOCUMENTATION_ACTIVE = lire_bool("DOCUMENTATION_ACTIVE", True)

SPECTACULAR_SETTINGS = {
    "TITLE": "FactCheck Mada API",
    "DESCRIPTION": (
        "API d'investigation pour documenter la propagation d'une rumeur et "
        "retrouver sa première occurrence publique. Les résultats sont des "
        "indices d'aide à la décision, jamais un verdict de vérité."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": False,
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
        "tryItOutEnabled": True,
    },
}

# ---------------------------------------------------------------------------
# CORS (React en développement)
# ---------------------------------------------------------------------------

CORS_ALLOWED_ORIGINS = lire_liste(
    "ORIGINES_CORS",
    "http://localhost:3000,http://localhost:5173",
)
CORS_ALLOW_CREDENTIALS = False
CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# ---------------------------------------------------------------------------
# Internationalisation et fuseau horaire
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Indian/Antananarivo"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Fichiers statiques et médias
# ---------------------------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Limites d'upload : les validations métier complètent ces garde-fous.
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Divers
# ---------------------------------------------------------------------------

CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS.copy()

# En production, on force les protections de base.
if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = lire_bool("REDIRECTION_HTTPS", True)
