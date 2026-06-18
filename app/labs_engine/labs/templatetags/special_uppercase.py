"""String template filters."""

import re

from django import template

register = template.Library()

# Words with a leading lowercase letter followed by uppercase (e.g. eDNA)
LEADING_LOWERCASE_WORD = re.compile(r'^[a-z][A-Z]')


@register.filter()
def considerate_upper_case(value):
    """Uppercase a string, preserving words that start with a lowercase letter
    followed by uppercase (e.g. eDNA, eResearch)."""
    return ' '.join(
        word if LEADING_LOWERCASE_WORD.match(word) else word.upper()
        for word in str(value).split()
    )
