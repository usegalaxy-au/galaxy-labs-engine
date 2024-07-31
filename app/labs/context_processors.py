"""Add variables to global template context."""

from django.conf import settings as app_settings


def settings(request):
    """Include some settings variables."""
    return {
        'title': None,  # prevents variable not found templating error
        'HOSTNAME': app_settings.HOSTNAME,
        "GITHUB_CONTENT_ROOT_BASE_URL":
            app_settings.GITHUB_CONTENT_ROOT_BASE_URL,
    }
