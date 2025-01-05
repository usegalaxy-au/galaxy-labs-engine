"""Django settings for Labs Engine project."""

# flake8: noqa

import os
from pathlib import Path
from utils.paths import ensure_dir

if os.getenv('DJANGO_SETTINGS_MODULE') != "app.settings.cli":
    from dotenv import load_dotenv
    load_dotenv('../.env', override=True)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
CLI_DEV = False
AUTH_USER_MODEL = 'labs.User'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or "secretkey"
SILENCED_SYSTEM_CHECKS = ['django_recaptcha.recaptcha_test_key_error']

if os.environ.get('HOSTNAME'):
    HOSTNAME = os.environ.get('HOSTNAME')
else:
    raise EnvironmentError('Env variable HOSTNAME not set')

# Site paths and URLs
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATIC_ROOT = BASE_DIR / 'app/static'
MEDIA_ROOT = BASE_DIR / 'app/media'
LOG_ROOT = ensure_dir(BASE_DIR / 'app/logs')
TEMP_DIR = ensure_dir(os.getenv('TMP_DIR', '/tmp/labs_engine/'))
DEFAULT_EXPORTED_LAB_CONTENT_ROOT = (
    f'http://{HOSTNAME}/static/labs/content/docs/base.yml')

CODEX_REPO = 'galaxyproject/galaxy_codex'
CODEX_GITHUB_URL = f'https://github.com/{CODEX_REPO}'
LABS_ENGINE_GITHUB_REPO = 'usegalaxy-au/galaxy-labs-engine'
LABS_ENGINE_GITHUB_URL = f'https://github.com/{LABS_ENGINE_GITHUB_REPO}'
EXAMPLE_LABS = {
    'FULL': {
        'RAW_URL': (
            f'https://raw.githubusercontent.com/{CODEX_REPO}/refs/heads/main'
            '/communities/genome/lab/base.yml'),
        'WEB_DIR_URL': (
            f'{CODEX_GITHUB_URL}/blob/main'
            '/communities/genome/lab'),
    },
    'DOCS': {
        'RAW_URL': (
            f'https://raw.githubusercontent.com/{LABS_ENGINE_GITHUB_REPO}/refs'
            '/heads/main/app/labs/static/labs/content/docs/base.yml'),
        'WEB_DIR_URL': (
            f'{LABS_ENGINE_GITHUB_URL}/tree/dev/app/labs/static/labs/content'
            '/docs'),
        'WEB_DIR_ROOT': (
            f'{LABS_ENGINE_GITHUB_URL}/blob/dev/app/labs/static/labs/content'
            '/docs'),
    },
    'SIMPLE': {
        'RAW_URL': (
            f'https://raw.githubusercontent.com/{LABS_ENGINE_GITHUB_REPO}'
            '/refs/heads/main/app/labs/static/labs/content/simple/base.yml'),
        'WEB_DIR_URL': (
            f'{LABS_ENGINE_GITHUB_URL}/blob/dev/app/labs/static/labs/content'
            '/simple'),
    },
}

# Hostnames
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    HOSTNAME,
]

# Application definition

INSTALLED_APPS = [
    'django_light',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'labs',
    'crispy_forms',
    "crispy_bootstrap5",
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'labs.context_processors.settings'
            ],
        },
    },
]

WSGI_APPLICATION = 'app.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache',
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.NumericPasswordValidator',
    },
]


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ['MAIL_HOSTNAME']
EMAIL_PORT = os.environ['MAIL_SMTP_PORT']
EMAIL_HOST_USER = os.getenv('MAIL_SMTP_USERNAME')
EMAIL_HOST_PASSWORD = os.getenv('MAIL_SMTP_PASSWORD')
EMAIL_USE_TLS = os.getenv('MAIL_USE_TLS', '').lower() in ('1', 'true')
EMAIL_FROM_ADDRESS = os.environ['MAIL_FROM_ADDRESS']
EMAIL_TO_ADDRESS = os.environ['MAIL_TO_ADDRESS']
SERVER_EMAIL = os.environ['MAIL_FROM_ADDRESS']
EMAIL_SUBJECT_PREFIX = os.getenv('EMAIL_SUBJECT_PREFIX',
                                 'Galaxy Labs Engine: ')

RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '')
RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '')

GITHUB_API_TOKEN = os.getenv('GITHUB_API_TOKEN')
if not GITHUB_API_TOKEN:
    print("\n\033[33mWarning: env variable GITHUB_API_TOKEN not set. Requests"
          " to api.github.com will be rate-limited at 60 requests per hour"
          " which may result in errors (this is used for fetching CONTRIBUTORS"
          " information).\n\033[0m")

CACHE_TIMEOUT = 60 * 60  # 1 hour

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Random bits
LOGOUT_REDIRECT_URL = '/'
