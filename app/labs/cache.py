"""Cache lab pages because rendering is expensive."""

import logging
from django.conf import settings
from django.core.cache import cache
from django.utils.http import urlencode
from django.http import HttpResponse
from hashlib import md5

CACHE_KEY_IGNORE_GET_PARAMS = (
    'cache',
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

        cache_key = cls._generate_cache_key(request)
        body = cache.get(cache_key)
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
        logger.debug(
            f"Cache PUT for {request.GET.get('content_root', 'root')}")
        cache_key = cls._generate_cache_key(request)
        timeout = (settings.CACHE_TIMEOUT
                   if request.GET.get('content_root')
                   else None)  # No timeout for default "Docs Lab" page

        cache.set(cache_key, body, timeout=timeout)
        response = HttpResponse(body)
        response['X-Cache-Status'] = 'MISS'
        return response

    @classmethod
    def _generate_cache_key(cls, request):
        """Create a unique cache key from request path."""
        params = {
            k: v for k, v in request.GET.items()
            if k not in CACHE_KEY_IGNORE_GET_PARAMS
        }
        key = f"{request.path}?{urlencode(params)}"
        md5hash = md5(key.encode('utf-8')).hexdigest()
        logger.debug(f"Cache path: {key}")
        logger.debug(f"Cache key (hashed): {md5hash}")
        return md5hash


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
    def put(cls, url, data, timeout=3600):
        if NOCACHE:
            return
        cache_key = cls._generate_cache_key(url)
        cache.set(cache_key, data, timeout=timeout)

    @classmethod
    def _generate_cache_key(cls, url):
        return md5(url.encode('utf-8')).hexdigest()
