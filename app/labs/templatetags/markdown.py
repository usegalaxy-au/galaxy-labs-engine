"""Markdown rendering with python-markdown2.

https://github.com/trentm/python-markdown2
"""

import markdown2
import re
import requests
from django import template
from django.http import Http404
from django.utils.safestring import mark_safe

register = template.Library()

ICONS = {
    'run': 'play_arrow',
    'tutorial': 'school',
    'social': 'group',
    'help': 'help',
}


def render_markdown(md):
    if not md:
        return ""
    # Prevent floating angle-brackets from triggering tag sanitizer:
    md = re.sub(r'\s+\>', '>', md)
    html = markdown2.markdown(md.strip(), extras={
        "tables": True,
        "code-friendly": True,
        "html-classes": {
            'table': 'table table-striped',
        },
    })
    return html.strip(' \n')


def expand_tags(html):
    if '{gtn modal}<a' in html:
        html = html.replace('{gtn modal}<a ', '<a class="gtn-modal" ')
    return html


@register.filter()
def markdown(md):
    """Render html from markdown string."""
    html = render_markdown(md)
    html = expand_tags(html)
    return mark_safe(html)


@register.filter()
def inline_markdown(md):
    """Render markdown to HTML and strip enclosing <p> tags."""
    html = render_markdown(md)
    if html.startswith('<p>'):
        html = html[3:-4]
    html = expand_tags(html)
    return mark_safe(html)


@register.simple_tag()
def markdown_from_url(url):
    """Fetch content from URL and render html from markdown string.

    This is intended to be used by exported Galaxy Labs, where a markdown url
    comes from a remote source.
    """
    res = requests.get(url)
    if res.status_code >= 300:
        raise Http404(f"URL {url} returned status code {res.status_code}")
    body = res.text

    # Remove YAML header if present
    liquid_md = (
        body.rsplit('---\n', 1)[1]
        if '---\n' in body
        else body
    )
    # Remove any Liquid syntax {: ... }
    md = re.sub(r'\{:.*\}', '', liquid_md)

    html = markdown2.markdown(md, extras={
        "tables": True,
        "code-friendly": False,
        "html-classes": {
            'table': 'table table-striped',
        },
    })

    return mark_safe(html)


@register.filter()
def iconkey(key):
    """Map icon keyword to material icons ID."""
    return ICONS.get(key, 'play_arrow')
