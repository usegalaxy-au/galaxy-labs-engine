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
from urllib.parse import unquote

from labs_engine.labs.cloudflare import purge_cache_for_request
from labs_engine.labs.models import CachedLab

_1_DAY = 60 * 60 * 24
CACHE_KEY_IGNORE_GET_PARAMS = (
    'cache',
    'nonce',
)
NOCACHE = settings.NOCACHE
NO_WEB_CACHE = os.getenv('NO_WEB_CACHE', False)  # Development only
IGNORE_ERRORS = (
    'UNIQUE constraint failed',
    'NOT NULL constraint failed',
)

logger = logging.getLogger('django.cache')

if settings.CACHE_TABLE_NAME not in connection.introspection.table_names():
    if not (
        os.getenv('DJANGO_SETTINGS_MODULE') == 'labs_engine.app.settings.test'
    ):
        raise EnvironmentError(
            f'Table "{settings.CACHE_TABLE_NAME}" does not exist. Please run'
            ' `python manage.py createcachetable` to create this table.')


class LabCache:
    @classmethod
    def get(cls, request):
        if cls.is_cache_bypass(request) or NOCACHE:
            # The Cloudflare cache is purged in put(), once the page has been
            # re-rendered and re-cached
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
        response = HttpResponse(body)
        if not NOCACHE:
            response['X-Cache-Status'] = 'MISS'
            if body and cls.is_labs_request(request):
                logger.debug(
                    f"Cache PUT for"
                    f" {request.GET.get('content_root', 'homepage')}")
                cache_record = cls._get_cached_lab(request, create=True)
                # If there was an IntegrityError creating the CachedLab, will
                # return None - we won't cache anything
                if cache_record:
                    timeout = (
                        settings.CACHE_TIMEOUT
                        if request.GET.get('content_root')
                        else None)  # No timeout for default "Docs Lab" page
                    cache.set(cache_record.key, body, timeout=timeout)

        # Purge Cloudflare last, so that the fresh page has been cached before
        # the edge can request it again
        if cls.is_cache_bypass(request) and cls.is_labs_request(request):
            _, url = cls._generate_cache_key(request)
            purge_cache_for_request(request, url)

        return response

    @classmethod
    def is_cache_bypass(cls, request):
        """Check if the request explicitly asked to bypass the cache."""
        return request.GET.get('cache', '').lower().startswith('f')

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
                # Refresh the stored URL - records created before URLs were
                # stored verbatim hold a re-encoded URL that Cloudflare won't
                # match
                lab.url = url
                lab.save()
            except IntegrityError as exc:
                for phrase in IGNORE_ERRORS:
                    if phrase in str(exc):
                        logger.warning(
                            f'Ignoring error updating CachedLab: {exc}')
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
                for phrase in IGNORE_ERRORS:
                    if phrase in str(exc):
                        logger.warning(
                            f'Ignoring error updating CachedLab: {exc}')
                        return None
                raise exc
            logger.debug(f"Created new CachedLab for key {cache_key} - {url}")

        return lab

    @classmethod
    def _generate_cache_key(cls, request):
        """Create a unique cache key from request path.

        Returns the key and the URL that was requested. The key is hashed from
        a normalized (URL-encoded) form so that equivalent requests share a
        cache entry, but the returned URL is the raw path/query string as sent
        by the client - that is what Cloudflare caches under, and a
        `content_root` may legitimately contain URL-encoded characters that a
        decode/re-encode round trip would mangle.
        """
        params = {
            k: v for k, v in request.GET.items()
            if k not in CACHE_KEY_IGNORE_GET_PARAMS
        }
        key_url = (
            f"{request.path}?{urlencode(params)}" if params else request.path)
        md5sum = md5(key_url.encode('utf-8')).hexdigest()
        url = cls._get_raw_url(request)
        logger.debug(f"Cache path: {url}")
        logger.debug(f"Cache url (hashed): {md5sum}")
        return md5sum, url

    @classmethod
    def _get_raw_url(cls, request):
        """Return the requested path and query string, verbatim.

        Cache-control params are stripped, but the remaining params are left
        exactly as the client encoded them.
        """
        query = '&'.join(
            pair
            for pair in request.META.get('QUERY_STRING', '').split('&')
            if pair
            and unquote(pair.split('=', 1)[0])
            not in CACHE_KEY_IGNORE_GET_PARAMS
        )
        return f"{request.path}?{query}" if query else request.path


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
