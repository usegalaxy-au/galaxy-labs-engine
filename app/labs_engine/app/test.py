"""Custom test components for GMS."""

import os
import logging
import shutil
from django.conf import settings
from django.test import TestCase as DjangoTestCase


class TestCase(DjangoTestCase):

    def setUp(self):
        logging.getLogger('django').setLevel(logging.ERROR)
        settings_module = os.environ.get('DJANGO_SETTINGS_MODULE')
        if settings_module != 'app.settings.test':
            raise RuntimeError(
                'Do not run tests without using app.settings.test!'
                f' (Using {settings_module})')

    def tearDown(self) -> None:
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
