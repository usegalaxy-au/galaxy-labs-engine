"""Authentication utilities for API endpoints."""

from functools import wraps
from django.http import JsonResponse
from django.utils import timezone

from .models import APIToken


def authenticated(view_func):
    """
    Decorator to require API token authentication.

    Expects the token in the X-API-TOKEN header.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        token_value = request.headers.get('X-API-TOKEN')

        if not token_value:
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401,
            )

        try:
            token = APIToken.objects.get(
                token=token_value,
                is_active=True,
            )
            # Update last_used timestamp
            token.last_used = timezone.now()
            token.save(update_fields=['last_used'])

            # Attach token to request for use in view
            request.api_token = token

            return view_func(request, *args, **kwargs)

        except APIToken.DoesNotExist:
            return JsonResponse(
                {'error': 'Invalid or inactive token'},
                status=401,
            )

    return wrapper
