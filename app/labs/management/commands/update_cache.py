"""Evaluate the Lab cache and update cachedbs that are in use.

Delete cached labs that are not in use.
"""

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.urls import resolve
from django.conf import settings
from django.utils import timezone

from labs.models import CachedLab
from utils.runserver import Runserver


class Command(BaseCommand):
    """Fe1ch all active cached lab pages and call their views to update the
    cache. Delete any cached labs that are not in use.
    """

    help = __doc__

    def add_arguments(self, parser):
        """Add arguments to the command."""
        parser.add_argument(
            '-y', '--non-interactive',
            action='store_true',
            help='Do not ask for confirmation',
        )

    def handle(self, *args, **kwargs):
        if not kwargs['non_interactive']:
            reply = input(
                '\nThis command will clear the cache and re-render all active'
                ' cached labs (visited in last'
                f' {settings.CACHE_UPDATE_RETAIN_DAYS} days).'
                '\nAre you sure you want to continue? (y/n) > ')
            if reply.lower() != 'y':
                self.stdout.write(self.style.ERROR(
                    '\nCache update aborted\n'))
                return

        self.stdout.write()
        with Runserver():
            # Use runserver so that local static files can still be served
            self.stdout.write(self.style.SUCCESS('\nServer is online.\n'))
            self.update_cache()

        self.stdout.write(self.style.SUCCESS(
            '\nCache update complete\n'))

    def update_cache(self):
        """Update the cache for all active cached labs."""
        self.stdout.write('Clearing cache...')
        cache.clear()

        self.stdout.write('Reading CachedLab records...')
        cached_labs = CachedLab.objects.all()
        self.stdout.write(f'Found {cached_labs.count()} cached labs')
        active_labs = CachedLab.objects.filter(
            modified__gt=timezone.now() - timezone.timedelta(
                days=settings.CACHE_UPDATE_RETAIN_DAYS,
            )
        )
        self.stdout.write(f'Found {active_labs.count()} active labs\n')

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
                    length = len(response.content)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Lab updated for URL [{length} bytes]: '),
                        ending='')
                else:
                    self.stdout.write(
                        self.style.ERROR('HTTP error code updating Lab: '),
                        ending='')
                self.stdout.write(lab.url)
            else:
                self.stdout.write(
                    self.style.WARNING('Deleting old cached lab '),
                    ending='')
                self.stdout.write(
                    f' (last modified'
                    f' {lab.modified.strftime("%Y-%m-%d %H:%M:%S")}):'
                    f' {lab.url}')
                lab.delete()
