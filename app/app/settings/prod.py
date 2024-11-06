# flake8: noqa

"""Settings for production.

See base.py for mail config read from .env file.
"""

import os
import logging
import sentry_sdk

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

SENTRY_DNS = os.getenv('SENTRY_DNS')
if SENTRY_DNS:
    sentry_sdk.init(
        dsn=SENTRY_DNS,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for tracing.
        traces_sample_rate=1.0,
    )
logging.getLogger('sentry_sdk').setLevel(logging.ERROR)
