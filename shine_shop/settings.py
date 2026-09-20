from pathlib import Path

import environ

# =============================================================================
# Base
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
)

environ.Env.read_env(BASE_DIR / ".env")

# =============================================================================
# Security
# =============================================================================

SECRET_KEY = env(
    "SECRET_KEY",
    default="django-insecure-change-this-in-production",
)

DEBUG = env("DEBUG")

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=["127.0.0.1", "localhost"],
)

CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[],
)

# =============================================================================
# Applications
# =============================================================================

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "django_filters",
    "rest_framework",

    # Project
    "core",
    "accounts",
    "products",
    "shop",
    "cart",
    "orders",
    "payments",
    "reviews",
    "wishlist",
]

# =============================================================================
# Middleware
# =============================================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# =============================================================================
# URL / WSGI
# =============================================================================

ROOT_URLCONF = "shine_shop.urls"

WSGI_APPLICATION = "shine_shop.wsgi.application"

# =============================================================================
# Templates
# =============================================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
                "core.context_processors.site_info",
            ],
        },
    },
]

# =============================================================================
# Database
# =============================================================================

DATABASE_URL = env("DATABASE_URL", default="")

if DATABASE_URL:
    DATABASES = {"default": env.db("DATABASE_URL")}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        },
    }

# =============================================================================
# Cache
# =============================================================================

CACHE_BACKEND = env(
    "CACHE_BACKEND",
    default="django.core.cache.backends.locmem.LocMemCache",
)

CACHES = {
    "default": {
        "BACKEND": CACHE_BACKEND,
        "LOCATION": env("CACHE_LOCATION", default="shine-cache"),
        "TIMEOUT": env.int("CACHE_TIMEOUT", default=300),
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

# =============================================================================
# Custom User
# =============================================================================

AUTH_USER_MODEL = "accounts.User"

# =============================================================================
# Authentication
# =============================================================================

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "shop:home"
LOGOUT_REDIRECT_URL = "shop:home"

# =============================================================================
# Password Validation
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]

# =============================================================================
# Internationalization
# =============================================================================

LANGUAGE_CODE = "fa-ir"

TIME_ZONE = "Asia/Tehran"

USE_I18N = True

USE_TZ = True

THOUSAND_SEPARATOR = ","

NUMBER_GROUPING = 3

# =============================================================================
# Static Files
# =============================================================================

STATIC_URL = "/static/"

STATICFILES_DIRS = [BASE_DIR / "static"]

STATIC_ROOT = BASE_DIR / "staticfiles"

# =============================================================================
# Media Files
# =============================================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"

# =============================================================================
# Storage
# =============================================================================

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if not DEBUG
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}

# =============================================================================
# Default Primary Key
# =============================================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# Django REST Framework
# =============================================================================

REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_PAGINATION_CLASS": (
        "rest_framework.pagination.PageNumberPagination"
    ),
    "PAGE_SIZE": 12,
}

# =============================================================================
# Session / CSRF
# =============================================================================

SESSION_COOKIE_HTTPONLY = True

SESSION_COOKIE_SAMESITE = "Lax"

SESSION_COOKIE_AGE = 60 * 60 * 24 * 14

CSRF_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_HTTPONLY = False

# =============================================================================
# Security Headers
# =============================================================================

SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

X_FRAME_OPTIONS = "DENY"

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# =============================================================================
# File Upload Limits
# =============================================================================

DATA_UPLOAD_MAX_MEMORY_SIZE = env.int(
    "DATA_UPLOAD_MAX_MEMORY_SIZE",
    default=10 * 1024 * 1024,
)

FILE_UPLOAD_MAX_MEMORY_SIZE = env.int(
    "FILE_UPLOAD_MAX_MEMORY_SIZE",
    default=5 * 1024 * 1024,
)

# =============================================================================
# Order / Payment
# =============================================================================

ORDER_PAYMENT_TIMEOUT_MINUTES = env.int(
    "ORDER_PAYMENT_TIMEOUT_MINUTES",
    default=30,
)

# =============================================================================
# ZarinPal
# =============================================================================

ZARINPAL_MERCHANT_ID = env("ZARINPAL_MERCHANT_ID", default="")

PAYMENT_GATEWAY_TIMEOUT = env.int("PAYMENT_GATEWAY_TIMEOUT", default=15)

ZARINPAL_AMOUNT_MULTIPLIER = env.int("ZARINPAL_AMOUNT_MULTIPLIER", default=10)

# =============================================================================
# Logging
# =============================================================================

LOG_LEVEL = env("LOG_LEVEL", default="INFO")

LOG_DIR = BASE_DIR / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "shine.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}
# =============================================================================
# Authentication Backends
# =============================================================================

AUTHENTICATION_BACKENDS = [
    "accounts.backends.EmailOrPhoneModelBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# =============================================================================
# SMS / OTP
# =============================================================================

SMS_PROVIDER = env("SMS_PROVIDER", default="console")

KAVENEGAR_API_KEY = env("KAVENEGAR_API_KEY", default="")

OTP_TTL_SECONDS = env.int("OTP_TTL_SECONDS", default=120)

OTP_MAX_ATTEMPTS = env.int("OTP_MAX_ATTEMPTS", default=5)

OTP_COOLDOWN_SECONDS = env.int("OTP_COOLDOWN_SECONDS", default=90)
