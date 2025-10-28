"""Development settings.

See base.py for mail config read from .env.
"""

# flake8: noqa

from .base import *


DEBUG = True

INTERNAL_IPS = [
    "127.0.0.1",
]
