"""Settings for production.

See base.py for mail config read from .env.
"""

# flake8: noqa

import os

from .base import *
from . import validate
from .log import config

validate.env()

DEBUG = False

LOGGING = config.configure_logging(LOG_ROOT)

ADMIN_NAME = os.getenv('ADMIN_NAME', 'Admin')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL',
                             os.getenv('MAIL_TO_ADDRESS'))
if ADMIN_EMAIL:
    ADMINS = [
        (ADMIN_NAME, ADMIN_EMAIL),
    ]

# Use manifest to manage static file versions for cache busting:
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
