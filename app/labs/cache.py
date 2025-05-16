"""Cache lab pages because rendering is expensive.

Cached Lab pages are tracked with the CachedLab model, which stores the cache
key, URL and last access time. This information is used when updating the
cache.
"""

import logging
from django.conf import settings
from django.core.cache import cache
from django.utils.http import urlencode
from django.http import HttpResponse
from hashlib import md5

from labs.models import CachedLab

_1_DAY = 60 * 60 * 24
CACHE_KEY_IGNORE_GET_PARAMS = (
    'cache',
    'nonce',
)
NOCACHE = settings.CLI_DEV or settings.DEBUG

logger = logging.getLogger('django.cache')


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
        logger.debug(
            f"Cache PUT for {request.GET.get('content_root', 'root')}")
        cache_record = cls._get_cached_lab(request, create=True)
        timeout = (settings.CACHE_TIMEOUT
                   if request.GET.get('content_root')
                   else None)  # No timeout for default "Docs Lab" page
        cache.set(cache_record.key, body, timeout=timeout)
        response = HttpResponse(body)
        response['X-Cache-Status'] = 'MISS'
        return response

    @classmethod
    def _get_cached_lab(cls, request, create=False):
        """Fetch CachedLab object from database.
        If it doesn't exist, create a new one if `create` is True.
        """
        cache_key, url = cls._generate_cache_key(request)
        lab = CachedLab.objects.filter(key=cache_key).first()
        if not lab and create:
            lab = CachedLab(
                key=cache_key,
                url=url,
            )
        if lab:
            lab.save()
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
        if NOCACHE:
            return
        cache_key = cls._generate_cache_key(url)
        data = cache.get(cache_key)
        if data:
            return data

    @classmethod
    def put(cls, url, data, timeout=_1_DAY):
        if NOCACHE:
            return
        cache_key = cls._generate_cache_key(url)
        cache.set(cache_key, data, timeout=timeout)

    @classmethod
    def _generate_cache_key(cls, url):
        return md5(url.encode('utf-8')).hexdigest()
