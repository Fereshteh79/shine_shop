"""
Django settings for Shine Shop.

تمام مقادیر حساس و قابل تغییر محیطی از فایل .env خوانده می‌شوند.

برای production حتماً حداقل موارد زیر تنظیم شوند:

    DEBUG=False
    SECRET_KEY=<secure-random-secret>
    ALLOWED_HOSTS=example.com,www.example.com
    CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com

نمونه تنظیمات پرداخت:

    ZARINPAL_MERCHANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    ZARINPAL_SANDBOX=True
    ZARINPAL_AMOUNT_MULTIPLIER=10
    PAYMENT_GATEWAY_TIMEOUT=15
"""

from __future__ import annotations

from decimal import Decimal

from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

# =============================================================================
# BASE DIRECTORY
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

ENV_FILE = BASE_DIR / ".env"

env = environ.Env(
    DEBUG=(bool, True),
    ALLOWED_HOSTS=(list, ["127.0.0.1", "localhost"]),
    CSRF_TRUSTED_ORIGINS=(list, []),
)

if ENV_FILE.exists():
    environ.Env.read_env(ENV_FILE)

# =============================================================================
# SECURITY
# =============================================================================

DEBUG = env.bool(
    "DEBUG",
    default=True,
)

SECRET_KEY = env(
    "SECRET_KEY",
    default="django-insecure-dev-only-change-me",
)

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[
        "127.0.0.1",
        "localhost",
    ],
)

CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[],
)

if not DEBUG:
    if (
            not SECRET_KEY
            or SECRET_KEY.startswith("django-insecure-")
            or len(SECRET_KEY) < 40
    ):
        raise ImproperlyConfigured(
            "در حالت DEBUG=False باید SECRET_KEY امن "
            "حداقل ۴۰ کاراکتری و بدون پیشوند "
            "django-insecure- در .env تنظیم شود."
        )

    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured(
            "در حالت DEBUG=False باید ALLOWED_HOSTS "
            "در .env تنظیم شود."
        )

# =============================================================================
# APPLICATIONS
# =============================================================================

INSTALLED_APPS = [
    # -------------------------------------------------------------------------
    # Django
    # -------------------------------------------------------------------------
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sitemaps",
    "django.contrib.sites",

    # -------------------------------------------------------------------------
    # Third-party
    # -------------------------------------------------------------------------
    "django_filters",
    "rest_framework",

    # -------------------------------------------------------------------------
    # Project
    # -------------------------------------------------------------------------
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

# django.contrib.sites
SITE_ID = 1

# =============================================================================
# MIDDLEWARE
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
# URL / APPLICATION ENTRY POINTS
# =============================================================================

ROOT_URLCONF = "shine_shop.urls"

WSGI_APPLICATION = "shine_shop.wsgi.application"

ASGI_APPLICATION = "shine_shop.asgi.application"

# =============================================================================
# ADMIN URL
# =============================================================================

_admin_url = env(
    "ADMIN_URL",
    default="admin/",
).strip("/")

ADMIN_URL = (
    f"{_admin_url}/"
    if _admin_url
    else "admin/"
)

# =============================================================================
# TEMPLATES
# =============================================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.media",
                "django.template.context_processors.static",

                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",

                "core.context_processors.site_info",
                "core.context_processors.site_counters",
            ],
        },
    },
]

# =============================================================================
# DATABASE
# =============================================================================

DATABASE_URL = env(
    "DATABASE_URL",
    default="",
).strip()

if DATABASE_URL:
    DATABASES = {
        "default": env.db(
            "DATABASE_URL",
        ),
    }

    DATABASES["default"]["CONN_MAX_AGE"] = env.int(
        "DB_CONN_MAX_AGE",
        default=60,
    )

    DATABASES["default"]["ATOMIC_REQUESTS"] = False

else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
            "OPTIONS": {
                "timeout": 20,
            },
        },
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# CACHE
# =============================================================================

CACHE_BACKEND = env(
    "CACHE_BACKEND",
    default="django.core.cache.backends.locmem.LocMemCache",
)

CACHE_LOCATION = env(
    "CACHE_LOCATION",
    default="shine-cache",
)

CACHE_TIMEOUT = env.int(
    "CACHE_TIMEOUT",
    default=300,
)

CACHE_KEY_PREFIX = env(
    "CACHE_KEY_PREFIX",
    default="shine",
)

CACHES = {
    "default": {
        "BACKEND": CACHE_BACKEND,
        "LOCATION": CACHE_LOCATION,
        "TIMEOUT": CACHE_TIMEOUT,
        "KEY_PREFIX": CACHE_KEY_PREFIX,
    },
}

# =============================================================================
# STATIC FILES
# =============================================================================

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# =============================================================================
# MEDIA FILES
# =============================================================================

MEDIA_URL = env(
    "MEDIA_URL",
    default="/media/",
)

MEDIA_ROOT = BASE_DIR / "media"

# =============================================================================
# STORAGE
# =============================================================================

if DEBUG:
    STATIC_STORAGE_BACKEND = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
else:
    STATIC_STORAGE_BACKEND = (
        "whitenoise.storage.CompressedManifestStaticFilesStorage"
    )

STORAGES = {
    "default": {
        "BACKEND": (
            "django.core.files.storage.FileSystemStorage"
        ),
    },
    "staticfiles": {
        "BACKEND": STATIC_STORAGE_BACKEND,
    },
}
API_PAGE_SIZE = env.int(
    "API_PAGE_SIZE",
    default=12,
)

# =============================================================================
# REST FRAMEWORK
# =============================================================================

REST_FRAMEWORK = {
    # -------------------------------------------------------------------------
    # Exception Handler
    # -------------------------------------------------------------------------
    "EXCEPTION_HANDLER": (
        "core.exceptions.api_exception_handler"
    ),

    # -------------------------------------------------------------------------
    # Permissions
    # -------------------------------------------------------------------------
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],

    # -------------------------------------------------------------------------
    # Authentication
    # -------------------------------------------------------------------------
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],

    # -------------------------------------------------------------------------
    # Filtering / Search / Ordering
    # -------------------------------------------------------------------------
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],

    # -------------------------------------------------------------------------
    # Pagination
    # -------------------------------------------------------------------------
    "DEFAULT_PAGINATION_CLASS": (
        "rest_framework.pagination.PageNumberPagination"
    ),

    "PAGE_SIZE": API_PAGE_SIZE,

    # -------------------------------------------------------------------------
    # Throttling
    # -------------------------------------------------------------------------
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],

    "DEFAULT_THROTTLE_RATES": {
        "anon": env(
            "API_ANON_RATE",
            default="60/min",
        ),
    },
}

# =============================================================================
# SESSIONS
# =============================================================================

SESSION_ENGINE = env(
    "SESSION_ENGINE",
    default="django.contrib.sessions.backends.cached_db",
)

SESSION_COOKIE_HTTPONLY = True

SESSION_COOKIE_SAMESITE = "Lax"

SESSION_COOKIE_AGE = 60 * 60 * 24 * 14

# =============================================================================
# CSRF
# =============================================================================

CSRF_COOKIE_SAMESITE = "Lax"

# برای خواندن CSRF token از JavaScript در صورت نیاز.
CSRF_COOKIE_HTTPONLY = False

# =============================================================================
# CUSTOM USER
# =============================================================================

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "accounts.backends.EmailOrPhoneModelBackend",
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_URL = "accounts:login"

LOGIN_REDIRECT_URL = "shop:home"

LOGOUT_REDIRECT_URL = "shop:home"

# =============================================================================
# PASSWORD VALIDATION
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
        "OPTIONS": {
            "min_length": 8,
        },
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
# OTP
# =============================================================================

OTP_CODE_LENGTH = env.int(
    "OTP_CODE_LENGTH",
    default=6,
)

OTP_CODE_TTL = env.int(
    "OTP_CODE_TTL",
    default=120,
)

OTP_RESEND_INTERVAL = env.int(
    "OTP_RESEND_INTERVAL",
    default=90,
)

OTP_MAX_VERIFY_ATTEMPTS = env.int(
    "OTP_MAX_VERIFY_ATTEMPTS",
    default=5,
)

# =============================================================================
# SMS PROVIDER
# =============================================================================

SMS_PROVIDER = env(
    "SMS_PROVIDER",
    default="console",
)

SMS_API_KEY = env(
    "SMS_API_KEY",
    default="",
)

SMS_SENDER = env(
    "SMS_SENDER",
    default="",
)

# =============================================================================
# PAYMENT
# =============================================================================

ZARINPAL_MERCHANT_ID = env(
    "ZARINPAL_MERCHANT_ID",
    default="",
)

ZARINPAL_SANDBOX = env.bool(
    "ZARINPAL_SANDBOX",
    default=True,
)

# مبلغ داخلی پروژه -> واحد موردنیاز درگاه.
#
# اگر قیمت‌های پروژه تومان باشند و زرین‌پال مبلغ را ریال دریافت کند:
#
#     1 تومان = 10 ریال
#
ZARINPAL_AMOUNT_MULTIPLIER = Decimal(
    env("ZARINPAL_AMOUNT_MULTIPLIER", default="10")
)

PAYMENT_GATEWAY_TIMEOUT = env.int(
    "PAYMENT_GATEWAY_TIMEOUT",
    default=15,
)

# =============================================================================
# ORDER / PAYMENT SETTINGS
# =============================================================================

ORDER_PAYMENT_TIMEOUT = env.int(
    "ORDER_PAYMENT_TIMEOUT",
    default=15 * 60,
)
ORDER_PAYMENT_TIMEOUT_MINUTES = 30

ORDER_MAX_ITEMS = env.int(
    "ORDER_MAX_ITEMS",
    default=100,
)

PAYMENT_VERIFY_MAX_ATTEMPTS = env.int(
    "PAYMENT_VERIFY_MAX_ATTEMPTS",
    default=3,
)

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = "fa-ir"

TIME_ZONE = "Asia/Tehran"

USE_I18N = True

USE_TZ = True

USE_THOUSAND_SEPARATOR = env.bool(
    "USE_THOUSAND_SEPARATOR",
    default=False,
)

THOUSAND_SEPARATOR = ","

NUMBER_GROUPING = 3

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

# =============================================================================
# SITE INFORMATION
# =============================================================================

SITE_NAME = env(
    "SITE_NAME",
    default="شاین شاپ",
)

SITE_PHONE = env(
    "SITE_PHONE",
    default="",
)

SITE_EMAIL = env(
    "SITE_EMAIL",
    default="",
)

SITE_STREET = env(
    "SITE_STREET",
    default="",
)

SITE_CITY = env(
    "SITE_CITY",
    default="",
)

SITE_REGION = env(
    "SITE_REGION",
    default="",
)

SITE_COUNTRY = env(
    "SITE_COUNTRY",
    default="ایران",
)

SITE_INSTAGRAM_URL = env(
    "SITE_INSTAGRAM_URL",
    default="",
)

SITE_TELEGRAM_URL = env(
    "SITE_TELEGRAM_URL",
    default="",
)

# =============================================================================
# SITE COUNTERS CACHE
# =============================================================================

SITE_COUNTER_CACHE_TIMEOUT = env.int(
    "SITE_COUNTER_CACHE_TIMEOUT",
    default=300,
)

# =============================================================================
# LOGGING
# =============================================================================

LOG_DIR = BASE_DIR / "logs"

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

LOG_LEVEL = env(
    "LOG_LEVEL",
    default="INFO",
).upper()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "verbose": {
            "format": (
                "[{asctime}] {levelname} {name} "
                "({module}.{funcName}:{lineno}) {message}"
            ),
            "style": "{",
        },

        "simple": {
            "format": (
                "[{asctime}] {levelname} "
                "{name}: {message}"
            ),
            "style": "{",
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },

        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "shine.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
            "formatter": "verbose",
        },
    },

    "root": {
        "handlers": [
            "console",
            "file",
        ],
        "level": LOG_LEVEL,
    },

    "loggers": {
        "django": {
            "level": LOG_LEVEL,
            "propagate": True,
        },

        "django.db.backends": {
            "level": "WARNING",
            "propagate": True,
        },

        "django.request": {
            "level": "WARNING",
            "propagate": True,
        },
    },
}

# =============================================================================
# SECURITY HARDENING
# =============================================================================

SECURE_CONTENT_TYPE_NOSNIFF = True

X_FRAME_OPTIONS = "DENY"

SECURE_REFERRER_POLICY = env(
    "SECURE_REFERRER_POLICY",
    default="same-origin",
)

if not DEBUG:
    # -------------------------------------------------------------------------
    # HTTPS / Reverse Proxy
    # -------------------------------------------------------------------------

    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )

    SECURE_SSL_REDIRECT = env.bool(
        "SECURE_SSL_REDIRECT",
        default=True,
    )

    # -------------------------------------------------------------------------
    # Secure Cookies
    # -------------------------------------------------------------------------

    SESSION_COOKIE_SECURE = True

    CSRF_COOKIE_SECURE = True

    # -------------------------------------------------------------------------
    # HSTS
    # -------------------------------------------------------------------------

    SECURE_HSTS_SECONDS = env.int(
        "SECURE_HSTS_SECONDS",
        default=31536000,
    )

    SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
        "SECURE_HSTS_INCLUDE_SUBDOMAINS",
        default=True,
    )

    SECURE_HSTS_PRELOAD = env.bool(
        "SECURE_HSTS_PRELOAD",
        default=True,
    )

# =============================================================================
# DEVELOPMENT HELPERS
# =============================================================================

if DEBUG:
    # در development اجازه استفاده از همه hostهای محلی متداول
    # در صورتی که کاربر آن‌ها را در ALLOWED_HOSTS قرار داده باشد.
    pass

# =============================================================================
# FINAL VALIDATION
# =============================================================================

if not isinstance(ALLOWED_HOSTS, list):
    raise ImproperlyConfigured(
        "ALLOWED_HOSTS باید به صورت list تنظیم شود."
    )

if not isinstance(CSRF_TRUSTED_ORIGINS, list):
    raise ImproperlyConfigured(
        "CSRF_TRUSTED_ORIGINS باید به صورت list تنظیم شود."
    )

if OTP_CODE_LENGTH < 4:
    raise ImproperlyConfigured(
        "OTP_CODE_LENGTH نباید کمتر از ۴ باشد."
    )

if OTP_CODE_TTL <= 0:
    raise ImproperlyConfigured(
        "OTP_CODE_TTL باید بیشتر از صفر باشد."
    )

if OTP_RESEND_INTERVAL <= 0:
    raise ImproperlyConfigured(
        "OTP_RESEND_INTERVAL باید بیشتر از صفر باشد."
    )

if OTP_MAX_VERIFY_ATTEMPTS <= 0:
    raise ImproperlyConfigured(
        "OTP_MAX_VERIFY_ATTEMPTS باید بیشتر از صفر باشد."
    )

if PAYMENT_GATEWAY_TIMEOUT <= 0:
    raise ImproperlyConfigured(
        "PAYMENT_GATEWAY_TIMEOUT باید بیشتر از صفر باشد."
    )

if ZARINPAL_AMOUNT_MULTIPLIER <= 0:
    raise ImproperlyConfigured(
        "ZARINPAL_AMOUNT_MULTIPLIER باید بیشتر از صفر باشد."
    )

if not 1 <= API_PAGE_SIZE <= 100:
    raise ImproperlyConfigured(
        "API_PAGE_SIZE باید بین ۱ تا ۱۰۰ باشد."
    )
