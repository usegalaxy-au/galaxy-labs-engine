"""Add variables to global template context."""

from django.conf import settings as app_settings


def settings(request):
    """Include some settings variables."""
    return {
        'HOSTNAME': app_settings.HOSTNAME,
    }
