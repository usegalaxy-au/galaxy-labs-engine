"""Views for home app."""

import logging
import os
import traceback
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.views.static import serve
from django.template import (
    RequestContext,
    Template,
)
from django.template.loader import render_to_string
from django.utils.text import slugify
from django.views import View
from pathlib import Path

from utils.exceptions import LabBuildError
from .cache import LabCache
from .forms import LabBootstrapForm
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

    template = 'labs/exported.html'

    try:
        if request.GET.get('content_root'):
            context = ExportLabContext(request.GET.get('content_root'))
        else:
            context = ExportLabContext(
                settings.DEFAULT_EXPORTED_LAB_CONTENT_ROOT)
            context.update({
                'LABS_ENGINE_GITHUB_URL': settings.LABS_ENGINE_GITHUB_URL,
                'EXAMPLE_LABS': settings.EXAMPLE_LABS,
            })
        context.validate()
    except LabBuildError as exc:
        logger.warning(f"Error building lab: {traceback.format_exc()}")
        return render(request, 'labs/export-error.html', {
            'exc': exc,
        }, status=400)

    # Multiple rounds of templating to render recursive template tags from
    # remote data with embedded template tags
    try:
        i = 0
        prev_template_str = ''
        template_str = render_to_string(template, context, request)
        while (
            prev_template_str.strip('\n') != template_str.strip('\n')
            and i < 4
        ):
            prev_template_str = template_str
            t = Template('{% load markdown %}\n\n' + template_str)
            template_str = t.render(RequestContext(request, context))
            i += 1
    except Exception as exc:
        logger.error(
            f"Error rendering template for"
            f" content_root={request.GET.get('content_root')}:"
            f"\n{traceback.format_exc()}")
        return report_exception_response(request, exc)

    template_str = context.render_relative_uris(template_str)
    response = LabCache.put(request, template_str)

    return response


def schema(request):
    """Render the schema page."""
    return render(request, 'labs/schema.html')


class BootstrapLab(View):
    """Generate new lab content from submitted form data."""

    form = LabBootstrapForm

    def get(self, request):
        form = self.form()
        return render(request, 'labs/bootstrap.html', {
            'form': form,
        })

    def post(self, request):
        form = self.form(request.POST, request.FILES)
        if form.is_valid():
            zipfile_relpath = form.bootstrap_lab()
            return self.force_download(
                request,
                zipfile_relpath,
                filename=slugify(form.cleaned_data['lab_name']) + '.zip',
            )
        return render(request, 'labs/bootstrap.html', {
            'form': form,
        }, status=400)

    def force_download(self, request, relpath: Path, filename=None):
        if settings.DEBUG:
            logger.debug('Returning Django static serve (DEBUG mode)')
            logger.debug('Serving file %s' % relpath)
            response = serve(
                request,
                relpath,
                settings.INTERNAL_ROOT,
            )
            response['Content-Disposition'] = (
                f"attachment; filename={filename}")
            return response

        url = settings.INTERNAL_URL + str(relpath).strip('/')
        logger.debug('Serving file via Nginx X-Accel-Redirect: %s' % relpath)
        response = HttpResponse()
        response['Content-Type'] = ''
        response['Content-Disposition'] = "attachment; filename=lab.zip"
        response['X-Accel-Redirect'] = url
        return response


def report_exception_response(request, exc, title=None):
    """Report an exception to the user."""
    return render(request, 'generic.html', {
        'message': str(exc),
        'title': title or "Sorry, an error occurred rendering this page.",
    }, status=400)


def custom_400(request, exception, template_name="400.html"):
    """Custom view to show error messages."""
    return render(request, template_name, {
        'exc': exception,
    }, status=400)
