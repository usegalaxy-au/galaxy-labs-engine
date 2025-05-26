# flake8: noqa

"""Settings for application build e.g. cache update."""

import os
import logging
import sentry_sdk

from .base import *
from . import validate
from .log import config

validate.env()

DEBUG = True
LOGGING = config.configure_logging(LOG_ROOT)
print('Running with HOSTNAME:', HOSTNAME)

SENTRY_DNS = os.getenv('SENTRY_DNS')
if SENTRY_DNS:
    sentry_sdk.init(
        dsn=SENTRY_DNS,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for tracing.
        traces_sample_rate=1.0,
    )
    logging.getLogger('sentry_sdk').setLevel(logging.ERROR)
