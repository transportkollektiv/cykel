"""Django settings for cykel project.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path

import environ
import sentry_sdk
from django.utils.timezone import timedelta
from sentry_sdk.integrations.django import DjangoIntegration

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False),
    USE_X_FORWARDED_PROTO=(bool, False),
)
# reading .env file
environ.Env.read_env()


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
# set env DJANGO_SECRET_KEY
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])


# Application definition

INSTALLED_APPS = [
    "cykel",
    "bikesharing.apps.BikesharingConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "django.contrib.sites",
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_api_key",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.twitter",
    "allauth.socialaccount.providers.github",
    "allauth.socialaccount.providers.stackexchange",
    "fragdenstaat_auth",
    "eventphone_auth",
    "allauth.socialaccount.providers.slack",
    "admin_override",
    "gbfs",
    "corsheaders",
    "leaflet",
    "preferences",
]

try:
    import django_extensions  # noqa

    INSTALLED_APPS.append("django_extensions")
except ImportError:
    pass

SHELL_PLUS_IMPORTS = [
    "from django.contrib.gis.geos import Point",
    "from django.contrib.gis.measure import D, Distance, A, Area",
]

SITE_ID = 1

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "cykel.urls"

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

WSGI_APPLICATION = "cykel.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases


defaultdbuser = env.str("USER", default="postgres")
# Use DATABASE_URL env with default:
DATABASES = {
    "default": env.db(
        "DATABASE_URL", default="postgis://" + defaultdbuser + "@localhost/cykel"
    )
}

# Celery / Redis

CELERY_BROKER_URL = env.str("REDIS_URL", default="redis://localhost:6379/0")

CELERY_BEAT_SCHEDULE = {
    "log_long_running_rents": {
        "task": "bikesharing.tasks.log_long_running_rents",
        "schedule": timedelta(minutes=5),
    },
    "log_unused_bikes": {
        "task": "bikesharing.tasks.log_unused_bikes",
        "schedule": timedelta(hours=3),
    },
}

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",  # noqa: E501
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


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "de-de"

TIME_ZONE = "Europe/Berlin"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_ROOT = BASE_DIR / "public"

STATIC_URL = "/static/"

# Rest Framework
REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly"
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "EXCEPTION_HANDLER": "api.views.custom_exception_handler",
}

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)


CORS_ORIGIN_WHITELIST = env.list("CORS_ORIGIN_WHITELIST", default=[])
CORS_ALLOW_CREDENTIALS = True
CSRF_COOKIE_SAMESITE = None
SESSION_COOKIE_SAMESITE = None
LOGIN_REDIRECT_URL = "/bikesharing/redirect/"
UI_URL = env("UI_SITE_URL")

USE_X_FORWARDED_PROTO = env("USE_X_FORWARDED_PROTO")
if USE_X_FORWARDED_PROTO:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

AUTH_USER_MODEL = "cykel.User"

ACCOUNT_AUTHENTICATION_METHOD = "username"
ACCOUNT_EMAIL_VERIFICATION = None
SOCIALACCOUNT_QUERY_EMAIL = False
ACCOUNT_ADAPTER = "cykel.auth.account_adapter.NoSignupAccountAdapter"
SOCIALACCOUNT_ADAPTER = "cykel.auth.account_adapter.SocialAccountAdapter"

SOCIALACCOUNT_PROVIDERS = {}

OWNCLOUD_URL = env("OWNCLOUD_URL", default=None)
if OWNCLOUD_URL is not None:
    INSTALLED_APPS.append("owncloud_auth")
    SOCIALACCOUNT_PROVIDERS["sub"] = {"SERVER": OWNCLOUD_URL}

AUTOENROLLMENT_PROVIDERS = env.list("AUTOENROLLMENT_PROVIDERS", default=[])

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

SENTRY_DSN = env("SENTRY_DSN", default=None)
if SENTRY_DSN is not None:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
    )
