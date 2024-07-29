"""String replace filter."""

from django import template

register = template.Library()


@register.filter()
def replace(string, pattern):
    """Replace characters in string."""
    target, replacement = pattern.split(',')
    return string.replace(target, replacement)
