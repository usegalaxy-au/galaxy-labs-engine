"""Development settings.

See base.py for mail config read from .env.
"""

# flake8: noqa

import os

from .base import *
from .log import config


DEBUG = True

LOGGING = config.configure_logging(LOG_ROOT)

INTERNAL_IPS = [
    "127.0.0.1",
]

DEV_LAB_STATIC_PATH = str(
    (BASE_DIR / '../dev-lab').resolve()
)
print("DEV_LAB_STATIC_PATH:", DEV_LAB_STATIC_PATH)
STATICFILES_DIRS = [
    ('dev-lab', DEV_LAB_STATIC_PATH),
]
