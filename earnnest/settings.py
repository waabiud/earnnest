import os
import dj_database_url
from decouple import config
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',') + [
    '.onrender.com',
    'exact-viewless-bridged.ngrok-free.dev',
]
INSTALLED_APPS = [
    'unfold',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Local apps
    'accounts',
    'payments',
    'investments',
    'referrals',
    'withdrawals',
    'game',
    'notifications',
    'dashboard',
    # Third party
    'django_celery_beat',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'earnnest.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'earnnest.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default=config(
            'DATABASE_URL',
            default=f'sqlite:///{BASE_DIR}/db.sqlite3'
        ),
        conn_max_age=600,
        ssl_require=True
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'accounts.User'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
    EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
    EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
    EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
    DEFAULT_FROM_EMAIL = config('EMAIL_HOST_USER', default='')
# Celery
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_TIMEZONE = 'Africa/Nairobi'

# App constants
ACTIVATION_FEE = config('ACTIVATION_FEE', default=200, cast=int)
REFERRAL_BONUS = config('REFERRAL_BONUS', default=50, cast=int)
MIN_INVESTMENT = config('MIN_INVESTMENT', default=1000, cast=int)
INVESTMENT_RETURN_PERCENT = config('INVESTMENT_RETURN_PERCENT', default=5, cast=int)
INVESTMENT_MATURITY_HOURS = config('INVESTMENT_MATURITY_HOURS', default=48, cast=int)

# Codian M-Pesa
CODIAN_CLIENT_ID = config("CODIAN_CLIENT_ID")
CODIAN_CLIENT_SECRET = config("CODIAN_CLIENT_SECRET")
CODIAN_SIGNATURE_SECRET = config("CODIAN_SIGNATURE_SECRET")
CODIAN_ACCOUNT_NUMBER = config("CODIAN_ACCOUNT_NUMBER")
CODIAN_CALLBACK_URL = config("CODIAN_CALLBACK_URL")


CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'https://exact-viewless-bridged.ngrok-free.dev',
    'http://127.0.0.1:8000',
    'http://localhost:8000',
]

# ===== UNFOLD ADMIN =====
from django.urls import reverse_lazy

UNFOLD = {
    "SITE_TITLE": "Earnnest Admin",
    "SITE_HEADER": "Earnnest",
    "SITE_SUBHEADER": "Earning Platform Management",
    "SITE_URL": "/dashboard/",
    "SITE_ICON": None,
    "SITE_SYMBOL": "currency_bitcoin",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "COLORS": {
        "primary": {
            "50": "240 253 244",
            "100": "220 252 231",
            "200": "187 247 208",
            "300": "134 239 172",
            "400": "74 222 128",
            "500": "34 197 94",
            "600": "22 163 74",
            "700": "15 118 110",
            "800": "6 78 59",
            "900": "2 44 34",
            "950": "0 20 15",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Overview",
                "items": [
                    {
                        "title": "Dashboard",
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": "Users",
                "items": [
                    {
                        "title": "All Users",
                        "icon": "people",
                        "link": reverse_lazy("admin:accounts_user_changelist"),
                    },
                ],
            },
            {
                "title": "Payments",
                "items": [
                    {
                        "title": "All Payments",
                        "icon": "payments",
                        "link": reverse_lazy("admin:payments_payment_changelist"),
                    },
                ],
            },
            {
                "title": "Investments",
                "items": [
                    {
                        "title": "All Investments",
                        "icon": "trending_up",
                        "link": reverse_lazy("admin:investments_investment_changelist"),
                    },
                ],
            },
            {
                "title": "Withdrawals",
                "items": [
                    {
                        "title": "All Withdrawals",
                        "icon": "account_balance_wallet",
                        "link": reverse_lazy("admin:withdrawals_withdrawal_changelist"),
                    },
                ],
            },
            {
                "title": "Game",
                "items": [
                    {
                        "title": "Game Rounds",
                        "icon": "casino",
                        "link": reverse_lazy("admin:game_gameround_changelist"),
                    },
                    {
                        "title": "Game Entries",
                        "icon": "sports_esports",
                        "link": reverse_lazy("admin:game_gameentry_changelist"),
                    },
                ],
            },
            {
                "title": "Referrals",
                "items": [
                    {
                        "title": "All Referrals",
                        "icon": "share",
                        "link": reverse_lazy("admin:referrals_referral_changelist"),
                    },
                ],
            },
            {
                "title": "Notifications",
                "items": [
                    {
                        "title": "All Notifications",
                        "icon": "notifications",
                        "link": reverse_lazy("admin:notifications_notification_changelist"),
                    },
                ],
            },
        ],
    },
}