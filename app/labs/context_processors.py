"""Add variables to global template context."""

from django.conf import settings as app_settings


def settings(request):
    """Include some settings variables."""
    return {
        'title': None,  # prevent variable not found templating error
        'HOSTNAME': app_settings.HOSTNAME,
        'GALAXY_SITE_NAME': app_settings.GALAXY_SITE_NAME,
        'GALAXY_SITE_SUFFIX': app_settings.GALAXY_SITE_SUFFIX,
    }
