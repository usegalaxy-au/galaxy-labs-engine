"""Custom validators for model/form fields."""

import re
from django.core.exceptions import ValidationError


def validate_github_username(value):
    if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$', value):
        raise ValidationError(
            "Invalid GitHub username. It must be 1-39 characters long, contain"
            " only letters, numbers, or single hyphens, and cannot start or"
            " end with a hyphen."
        )
