"""Purge the Cloudflare edge cache for Lab pages.

Django's LabCache is only half the story - Lab pages are also cached by
Cloudflare in front of the site. When a Lab maintainer busts the Django cache
with `?cache=false`, Cloudflare must be purged too, or they will keep being
served the stale page from the edge.

Cloudflare's cache key includes the full query string, so a single Lab can be
cached under several URLs (e.g. with `&audit=true`). Every URL that has been
served for the requested `content_root` is purged, as recorded by the CachedLab
model.
"""

import logging
import requests
from django.conf import settings
from django.core.cache import cache
from django.utils.http import urlencode
from hashlib import md5

from labs_engine.labs.models import CachedLab

CLOUDFLARE_PURGE_URL = (
    'https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache')
DEBOUNCE_CACHE_KEY = 'cf-purge:{md5sum}'

logger = logging.getLogger('django.cache')


def purge_cache_for_request(request, url):
    """Purge the Cloudflare cache for every URL served for this Lab.

    `url` is the canonical (cache key) path and query string for the request,
    as built by ``LabCache._generate_cache_key``.

    This never raises - a Cloudflare outage must not break the Lab page.
    """
    try:
        _purge_cache_for_request(request, url)
    except Exception:
        logger.exception('Error purging Cloudflare cache')


def _purge_cache_for_request(request, url):
    """Purge the Cloudflare cache, raising on any error."""
    zone_id = settings.CLOUDFLARE_ZONE_ID
    token = settings.CLOUDFLARE_API_TOKEN
    if not (zone_id and token):
        logger.debug(
            'Cloudflare credentials not configured - skipping cache purge')
        return

    content_root = request.GET.get('content_root', '')
    if _is_debounced(content_root):
        logger.debug(
            f'Cloudflare purge debounced for content_root={content_root}')
        return

    urls = _get_purge_urls(request, url, content_root)
    purged = _post_purge(zone_id, token, urls)
    logger.info(
        f'Purged {purged}/{len(urls)} Cloudflare URLs for'
        f' content_root={content_root or "homepage"}')


def _is_debounced(content_root):
    """Return True if this content_root was purged too recently.

    Prevents repeated `cache=false` requests from exhausting the Cloudflare
    API purge rate limit.
    """
    key = DEBOUNCE_CACHE_KEY.format(
        md5sum=md5(content_root.encode('utf-8')).hexdigest())
    if cache.get(key):
        return True
    cache.set(key, True, timeout=settings.CLOUDFLARE_PURGE_DEBOUNCE_SECONDS)
    return False


def _get_purge_urls(request, url, content_root):
    """Return absolute URLs to purge for the requested content_root.

    CachedLab.url records every path/query string that has been served, but is
    relative to the site root, so the requested scheme and host are prepended.
    """
    paths = [url]
    if content_root:
        query = urlencode({'content_root': content_root})
        paths += [
            lab.url
            for lab in CachedLab.objects.filter(url__contains=query)
        ]
    base_url = f'{request.scheme}://{request.get_host()}'
    # dict.fromkeys dedupes while preserving order
    return list(dict.fromkeys(base_url + path for path in paths))


def _post_purge(zone_id, token, urls):
    """Post URLs to the Cloudflare cache purge API in batches.

    Returns the number of URLs that were successfully purged. Cloudflare
    rejects a whole batch if any URL in it is invalid, so a failed batch
    counts for nothing.
    """
    endpoint = CLOUDFLARE_PURGE_URL.format(zone_id=zone_id)
    headers = {'Authorization': f'Bearer {token}'}
    batch_size = settings.CLOUDFLARE_PURGE_BATCH_SIZE
    purged = 0

    for i in range(0, len(urls), batch_size):
        batch = urls[i:i + batch_size]
        logger.debug(f'Purging Cloudflare URLs: {batch}')
        response = requests.post(
            endpoint,
            headers=headers,
            json={'files': batch},
            timeout=settings.CLOUDFLARE_API_TIMEOUT,
        )
        if not response.ok:
            logger.error(
                f'Cloudflare purge returned HTTP {response.status_code}:'
                f' {response.text}')
            continue
        data = response.json()
        if not data.get('success'):
            logger.error(
                f'Cloudflare purge was unsuccessful: {data.get("errors")}')
            continue
        purged += len(batch)

    return purged
