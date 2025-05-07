"""Evaluate the Lab cache and update cachedbs that are in use.

Delete cached labs that are not in use.
"""

import requests
import time

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.urls import resolve
from django.conf import settings
from django.utils import timezone

from labs.models import CachedLab


class Command(BaseCommand):
    """Fe1ch all active cached lab pages and call their views to update the
    cache. Delete any cached labs that are not in use.
    """

    help = __doc__

    def add_arguments(self, parser):
        """Add arguments to the command."""
        parser.add_argument(
            '-f', '--force',
            action='store_true',
            help='Do not ask for confirmation',
        )

    def handle(self, *args, **kwargs):
        if not kwargs['force']:
            reply = input(
                '\nThis command will clear the cache and re-render all active'
                ' cached labs (visited in last'
                f' {settings.CACHE_UPDATE_RETAIN_DAYS} days).'
                '\nAre you sure you want to continue? (y/n) > ')
            if reply.lower() != 'y':
                self.stdout.write(self.style.ERROR(
                    '\nCache update aborted\n'))
                return

        self.stdout.write(
            f'Waiting for server at {settings.HOSTNAME} to come online',
            ending='')
        while True:
            try:
                response = requests.get(f'http://{settings.HOSTNAME}')
                if response.status_code == 200:
                    self.stdout.write(self.style.SUCCESS(
                        f'\nServer at {settings.HOSTNAME} is online.'))
                    break
            except requests.ConnectionError:
                pass
            self.stdout.write('.', ending='')
            time.sleep(1)

        self.stdout.write(self.style.SUCCESS(
            '\nClearing cache...'))
        cache.clear()

        self.stdout.write(self.style.SUCCESS('Reading CachedLab records...'))
        cached_labs = CachedLab.objects.all()
        self.stdout.write(self.style.SUCCESS(
            f'Found {cached_labs.count()} cached labs'))

        active_labs = CachedLab.objects.filter(
            modified__gt=timezone.now() - timezone.timedelta(
                days=settings.CACHE_UPDATE_RETAIN_DAYS,
            )
        )
        self.stdout.write(self.style.SUCCESS(
            f'Found {active_labs.count()} active labs'))

        factory = RequestFactory()
        for lab in cached_labs:
            if lab in active_labs:
                url = (
                    lab.url + '&cache=false'
                    if '?' in lab.url
                    else lab.url + '?cache=false'
                )
                request = factory.get(url)
                view_func, args, kwargs = resolve(request.path_info)
                response = view_func(request, *args, **kwargs)
                if response.status_code == 200:
                    self.stdout.write(self.style.SUCCESS(
                        f'Lab updated successfully: {lab.url}'))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'HTTP error code updating Lab: {lab.url}'
                        ' This should have resulted in an error notification.'
                    ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'Deleting old cached lab: {lab.url} (last modified'
                    f' {lab.modified.strftime("%Y-%m-%d %H:%M:%S")})'))
                lab.delete()

        self.stdout.write(self.style.SUCCESS(
            '\nCache update complete\n'))
