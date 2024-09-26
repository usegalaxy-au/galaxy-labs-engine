"""Views for home app."""

import logging
from django.conf import settings
from django.shortcuts import render
from django.template import (
    RequestContext,
    Template,
)
from django.template.loader import render_to_string

from utils.exceptions import LabBuildError
from .cache import LabCache
from .lab_export import ExportLabContext

logger = logging.getLogger('django')


def export_lab(request):
    """Generic Galaxy Lab landing page build with externally hosted content.

    These pages are built on the fly and can be requested by third parties on
    an ad hoc basis, where the content would typically be hosted in a GitHub
    repo with a YAML file root which is specified as a GET parameter.
    """

    if response := LabCache.get(request):
        return response

    template = 'labs//exported.html'

    try:
        if request.GET.get('content_root'):
            context = ExportLabContext(request.GET.get('content_root'))
        else:
            context = ExportLabContext(
                settings.DEFAULT_EXPORTED_LAB_CONTENT_ROOT)
        context['HOSTNAME'] = settings.HOSTNAME
        context.validate()
    except LabBuildError as exc:
        return render(request, 'labs//export-error.html', {
            'exc': exc,
        }, status=400)

    # Multiple rounds of templating to render recursive template tags from
    # remote data with embedded template tags
    i = 0
    prev_template_str = ''
    template_str = render_to_string(template, context, request)
    while prev_template_str.strip('\n') != template_str.strip('\n') and i < 4:
        prev_template_str = template_str
        t = Template('{% load markdown %}\n\n' + template_str)
        template_str = t.render(RequestContext(request, context))
        i += 1

    response = LabCache.put(request, template_str)

    return response


def report_exception_response(request, exc, title=None):
    """Report an exception to the user."""
    return render(request, 'generic.html', {
        'message': str(exc),
        'title': title or "Sorry, an error has occurred",
    })


def custom_400(request, exception, template_name="400.html"):
    """Custom view to show error messages."""
    return render(request, template_name, {
        'exc': exception,
    }, status=400)
