"""Settings for production.

See base.py for mail config read from .env file.
"""

# flake8: noqa

import os

from .base import *
from . import validate
from .log import config

validate.env()

DEBUG = False

log_levels = {
    'console': os.getenv('LOG_LEVEL_CONSOLE', 'INFO'),
    'cache': os.getenv('LOG_LEVEL_CACHE', 'INFO'),
}

LOGGING = config.configure_logging(LOG_ROOT, log_levels)

ADMIN_NAME = os.getenv('ADMIN_NAME', 'Admin')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL',
                             os.getenv('MAIL_TO_ADDRESS'))
if ADMIN_EMAIL:
    ADMINS = [
        (ADMIN_NAME, ADMIN_EMAIL),
    ]

# Use manifest to manage static file versions for cache busting:
STATICFILES_STORAGE = ('django.contrib.staticfiles.storage'
                       '.ManifestStaticFilesStorage')
