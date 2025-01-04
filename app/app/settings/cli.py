"""Local Lab development settings.

To be used when pip-installed and running as `labs-engine serve`.
"""

# flake8: noqa

import os

from .base import *

DEBUG = True
CLI_DEV = True
LAB_CONTENT_ROOT = os.environ.get('LAB_CONTENT_ROOT')
if not LAB_CONTENT_ROOT:
    raise EnvironmentError('Env variable LAB_CONTENT_ROOT not set')
LAB_CONTENT_ENTRYPOINT = os.environ.get('LAB_CONTENT_ENTRYPOINT', 'base.yml')

INTERNAL_IPS = [
    "127.0.0.1",
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

STATICFILES_DIRS = [
    ("local", LAB_CONTENT_ROOT),
]

DEFAULT_EXPORTED_LAB_CONTENT_ROOT = (
    f"http://{HOSTNAME}/static/local/{LAB_CONTENT_ENTRYPOINT}")

INSTALLED_APPS.remove('django_light')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
