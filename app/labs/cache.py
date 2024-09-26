"""Cache lab pages because rendering is expensive."""

import logging
from django.core.cache import cache
from django.utils.http import urlencode
from django.http import HttpResponse
from hashlib import md5

CACHE_KEY_IGNORE_GET_PARAMS = (
    'cache',
)

logger = logging.getLogger('django.cache')


class LabCache:
    @classmethod
    def get(cls, request):
        if request.GET.get('cache', '').lower() == 'false':
            return

        cache_key = cls._generate_cache_key(request)
        body = cache.get(cache_key)
        if body:
            logger.debug(f"Cache HIT for {request.path}")
            response = HttpResponse(body)
            response['X-Cache-Status'] = 'HIT'
            return response
        logger.debug(f"Cache MISS for {request.path}")

    @classmethod
    def put(cls, request, body):
        logger.debug(f"Cache PUT for {request.path}")
        cache_key = cls._generate_cache_key(request)
        cache.set(cache_key, body, timeout=3600)
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
        cache_key = cls._generate_cache_key(url)
        data = cache.get(cache_key)
        if data:
            return data

    @classmethod
    def put(cls, url, data, timeout=3600):
        cache_key = cls._generate_cache_key(url)
        cache.set(cache_key, data, timeout=timeout)

    @classmethod
    def _generate_cache_key(cls, url):
        return md5(url.encode('utf-8')).hexdigest()
