"""Cache lab pages because rendering is expensive.

Cached Lab pages are tracked with the CachedLab model, which stores the cache
key, URL and last access time. This information is used when updating the
cache.
"""

import logging
import os
from django.conf import settings
from django.core.cache import cache
from django.db import connection, IntegrityError
from django.http import HttpResponse
from django.utils.http import urlencode
from hashlib import md5

from labs_engine.labs.models import CachedLab

_1_DAY = 60 * 60 * 24
CACHE_KEY_IGNORE_GET_PARAMS = (
    'cache',
    'nonce',
)
NOCACHE = settings.NOCACHE
NO_WEB_CACHE = os.getenv('NO_WEB_CACHE', False)  # Development only

logger = logging.getLogger('django.cache')

if settings.CACHE_TABLE_NAME not in connection.introspection.table_names():
    if not os.getenv('DJANGO_SETTINGS_MODULE') == 'labs_engine.app.settings.test':
        raise EnvironmentError(
            f'Table "{settings.CACHE_TABLE_NAME}" does not exist. Please run'
            ' `python manage.py createcachetable` to create this table.')


class LabCache:
    @classmethod
    def get(cls, request):
        if (
            request.GET.get('cache', '').lower() == 'false'
            or NOCACHE
        ):
            return

        cache_record = cls._get_cached_lab(request)
        if cache_record:
            body = cache.get(cache_record.key)
            if body:
                logger.debug(
                    f"Cache HIT for {request.GET.get('content_root', 'root')}")
                response = HttpResponse(body)
                response['X-Cache-Status'] = 'HIT'
                return response
        logger.debug(
            f"Cache MISS for {request.GET.get('content_root', 'root')}")

    @classmethod
    def put(cls, request, body):
        if NOCACHE:
            return HttpResponse(body)
        response = HttpResponse(body)
        response['X-Cache-Status'] = 'MISS'
        if body and cls.is_labs_request(request):
            logger.debug(
                f"Cache PUT for {request.GET.get('content_root', 'homepage')}")
            cache_record = cls._get_cached_lab(request, create=True)
            # If there was an IntegrityError creating the CachedLab, will
            # return None - we won't cache anything
            if cache_record:
                timeout = (
                    settings.CACHE_TIMEOUT
                    if request.GET.get('content_root')
                    else None)  # No timeout for default "Docs Lab" page
                cache.set(cache_record.key, body, timeout=timeout)
        return response

    @classmethod
    def is_labs_request(cls, request):
        """Check if the request is for a lab page."""
        return (
            request.path in ('', '/')
            and (
                request.GET.get('content_root')
                or not request.GET
            )
        )

    @classmethod
    def _get_cached_lab(cls, request, create=False):
        """Fetch CachedLab object from database.
        If it doesn't exist, create a new one if `create` is True.
        """
        cache_key, url = cls._generate_cache_key(request)
        lab = CachedLab.objects.filter(key=cache_key).first()
        if lab:
            logger.debug(f"CachedLab found for key {cache_key} - {url}")
            try:
                lab.save()
            except IntegrityError as exc:
                if 'NOT NULL constraint failed' in str(exc):
                    logger.warning('IntegrityError: ' + str(exc))
                    return None
                raise exc
        else:
            logger.debug(f"No CachedLab found for key {cache_key} - {url}")

        if create and not lab:
            try:
                lab = CachedLab(
                    key=cache_key,
                    url=url,
                )
                lab.save()
            except IntegrityError as exc:
                if 'UNIQUE constraint failed' in str(exc):
                    logger.warning('IntegrityError: ' + str(exc))
                    return None
                raise exc
            logger.debug(f"Created new CachedLab for key {cache_key} - {url}")

        return lab

    @classmethod
    def _generate_cache_key(cls, request):
        """Create a unique cache key from request path."""
        params = {
            k: v for k, v in request.GET.items()
            if k not in CACHE_KEY_IGNORE_GET_PARAMS
        }
        url = f"{request.path}?{urlencode(params)}" if params else request.path
        md5sum = md5(url.encode('utf-8')).hexdigest()
        logger.debug(f"Cache path: {url}")
        logger.debug(f"Cache url (hashed): {md5sum}")
        return md5sum, url


class WebCache:
    """Cache content from external web requests."""

    @classmethod
    def get(cls, url):
        if NO_WEB_CACHE:
            return
        cache_key = cls._generate_cache_key(url)
        data = cache.get(cache_key)
        if data:
            return data

    @classmethod
    def put(cls, url, data, timeout=_1_DAY):
        if NO_WEB_CACHE:
            return
        cache_key = cls._generate_cache_key(url)
        cache.set(cache_key, data, timeout=timeout)

    @classmethod
    def _generate_cache_key(cls, url):
        return md5(url.encode('utf-8')).hexdigest()
