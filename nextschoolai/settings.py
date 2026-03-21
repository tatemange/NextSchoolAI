"""
Paramètres Django pour le projet NextSchoolAI.

Architecture 3 couches :
- Couche 1 : Présentation (Templates Django / HTML5 / CSS3 / JS)
- Couche 2 : Logique métier (Django, Auth, Services IA)
- Couche 3 : Données (SQLite dev / MySQL prod)
"""

import os
from pathlib import Path
from decouple import config, Csv

# =============================================================================
# CHEMINS DE BASE
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# =============================================================================
# SÉCURITÉ
# =============================================================================

SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-changez-moi-en-production-nextschoolai-2025'
)

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())


# =============================================================================
# APPLICATIONS INSTALLÉES
# =============================================================================

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

LOCAL_APPS = [
    'accounts',   # Gestion utilisateurs et rôles
    'documents',  # Gestion documentaire (PDF, cours, épreuves, livres)
    'quiz',       # QCM et évaluations générés par IA
    'ia',         # Service IA (Gemini / Hugging Face)
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS


# =============================================================================
# MIDDLEWARE
# =============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# =============================================================================
# URLS ET WSGI
# =============================================================================

ROOT_URLCONF = 'nextschoolai.urls'

WSGI_APPLICATION = 'nextschoolai.wsgi.application'


# =============================================================================
# TEMPLATES
# =============================================================================

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


# =============================================================================
# BASE DE DONNÉES
# =============================================================================

_db_name = config('DB_NAME', default='')
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': _db_name if _db_name else str(BASE_DIR / 'db.sqlite3'),
        'USER': config('DB_USER', default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default=''),
        'PORT': config('DB_PORT', default=''),
        'OPTIONS': {},
        'CONN_MAX_AGE': 600,  # Connexions persistantes (10 min)
    }
}


# =============================================================================
# MODÈLE UTILISATEUR PERSONNALISÉ
# =============================================================================

AUTH_USER_MODEL = 'accounts.Utilisateur'


# =============================================================================
# AUTHENTIFICATION
# =============================================================================

LOGIN_URL = '/comptes/connexion/'
LOGIN_REDIRECT_URL = '/comptes/tableau-de-bord/'
LOGOUT_REDIRECT_URL = '/comptes/connexion/'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

SESSION_COOKIE_AGE = 86400 * 7  # 7 jours
SESSION_COOKIE_HTTPONLY = True
SESSION_SAVE_EVERY_REQUEST = False


# =============================================================================
# INTERNATIONALISATION
# =============================================================================

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'Africa/Douala'

USE_I18N = True

USE_TZ = True


# =============================================================================
# FICHIERS STATIQUES ET MÉDIAS
# =============================================================================

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Taille maximale des fichiers uploadés (50 Mo)
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800

# Types de fichiers autorisés pour les documents
ALLOWED_DOCUMENT_TYPES = ['application/pdf', 'image/jpeg', 'image/png', 'image/webp']
MAX_DOCUMENT_SIZE_MB = 50


# =============================================================================
# CLÉ PRIMAIRE PAR DÉFAUT
# =============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Messages Django
from django.contrib.messages import constants as message_constants
MESSAGE_TAGS = {
    message_constants.DEBUG:   'debug',
    message_constants.INFO:    'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR:   'error',
}


# =============================================================================
# SERVICE IA (GEMINI / HUGGING FACE)
# =============================================================================

GEMINI_API_KEY = config('GEMINI_API_KEY', default='')
GEMINI_MODEL = config('GEMINI_MODEL', default='gemini-1.5-flash')

HUGGINGFACE_API_KEY = config('HUGGINGFACE_API_KEY', default='')
HUGGINGFACE_MODEL = config('HUGGINGFACE_MODEL', default='facebook/bart-large-cnn')

# Nombre max de tokens pour les résumés
IA_MAX_TOKENS = 2048
IA_TIMEOUT_SECONDS = 30


# =============================================================================
# EMAIL (notifications)
# =============================================================================

EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='NextSchoolAI <noreply@nextschoolai.cm>')


# =============================================================================
# SÉCURITÉ PRODUCTION (activée quand DEBUG=False)
# =============================================================================

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'
