"""Views for home app."""

import logging
import traceback
import json
import yaml
import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.static import serve
from django.template import (
    RequestContext,
    Template,
)
from django.template.loader import render_to_string
from django.utils.text import slugify
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from pathlib import Path

from utils.exceptions import LabBuildError
from .cache import LabCache
from .forms import LabBootstrapForm
from .lab_export import ExportLabContext
from .lab_schema import DEPRECATED_PROPS, LabSectionSchema, LabSchema
from .audit import perform_template_audit

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
            'deprecated_props': DEPRECATED_PROPS,
        }, status=400)

    context['audit'] = 'audit' in request.GET

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
            f"Error rendering template for "
            f"content_root={request.GET.get('content_root')}: "
            f"\n{traceback.format_exc()}"
        )
        return report_exception_response(request, exc)

    template_str = context.render_relative_uris(template_str)

    # Perform tool auditing (function checks if audit is requested)
    template_str, context = perform_template_audit(
        template_str,
        context,
        request
    )

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
        logger.debug(
            'Serving file via Nginx X-Accel-Redirect: %s' % relpath
        )
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


class LabBuilderView(View):
    """Visual Lab builder interface."""

    def get(self, request):
        """Render the Lab builder interface."""
        return render(request, 'labs/builder.html')


@method_decorator(csrf_exempt, name='dispatch')
class LabBuilderAPI(View):
    """API endpoints for the Lab builder."""

    def post(self, request):
        """Handle Lab builder actions."""
        try:
            data = json.loads(request.body)
            action = data.get('action')

            if action == 'validate_section':
                return self.validate_section(data.get('section_data'))
            elif action == 'validate_lab':
                return self.validate_lab(data.get('lab_data'))
            elif action == 'export_yaml':
                return self.export_yaml(data.get('lab_data'))
            elif action == 'import_github':
                return self.import_from_github(data.get('github_url'))
            elif action == 'create_pr':
                return self.create_github_pr(data.get('pr_data'))
            else:
                return JsonResponse({
                    'error': 'Invalid action'
                }, status=400)

        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON'
            }, status=400)
        except Exception as e:
            logger.error(f"Lab builder API error: {e}")
            return JsonResponse({
                'error': str(e)
            }, status=500)

    def validate_section(self, section_data):
        """Validate a single section against the schema."""
        try:
            LabSectionSchema(**section_data)
            return JsonResponse({'valid': True})
        except Exception as e:
            return JsonResponse({
                'valid': False,
                'errors': [str(e)]
            })

    def validate_lab(self, lab_data):
        """Validate the complete lab configuration."""
        try:
            LabSchema(**lab_data)
            return JsonResponse({'valid': True})
        except Exception as e:
            return JsonResponse({
                'valid': False,
                'errors': [str(e)]
            })

    def export_yaml(self, lab_data):
        """Export lab data as YAML files."""
        try:
            # Validate first
            LabSchema(**lab_data)

            # Create YAML files
            files = {}

            # Base YAML
            base_data = {
                k: v for k, v in lab_data.items()
                if k not in ['sections_data']
            }
            files['base.yml'] = yaml.dump(
                base_data,
                default_flow_style=False,
                allow_unicode=True
            )

            # Section YAML files
            sections_data = lab_data.get('sections_data', [])
            for i, section in enumerate(sections_data, 1):
                filename = f'section_{i}.yml'
                files[filename] = yaml.dump(
                    section,
                    default_flow_style=False,
                    allow_unicode=True
                )

            return JsonResponse({
                'success': True,
                'files': files
            })

        except Exception as e:
            logger.error(f"Export YAML error: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

    def import_from_github(self, github_url):
        """Import Lab content from a GitHub repository."""
        try:
            # Parse GitHub URL to get raw content URLs
            if not github_url:
                return JsonResponse({
                    'error': 'GitHub URL is required'
                }, status=400)

            # Convert GitHub URL to raw content URL
            if 'github.com' in github_url and '/blob/' in github_url:
                github_url = github_url.replace(
                    'github.com', 'raw.githubusercontent.com'
                ).replace('/blob/', '/')
            elif 'github.com' in github_url and '/tree/' in github_url:
                github_url = github_url.replace(
                    'github.com', 'raw.githubusercontent.com'
                ).replace('/tree/', '/')

            # If URL doesn't end with base.yml, append it
            if not github_url.endswith('base.yml'):
                if not github_url.endswith('/'):
                    github_url += '/'
                github_url += 'base.yml'

            # Fetch base.yml
            logger.info(f"Fetching GitHub content from: {github_url}")
            response = requests.get(github_url, timeout=10)
            response.raise_for_status()

            base_content = yaml.safe_load(response.text)

            # Extract base URL for section files
            base_url = github_url.rsplit('/', 1)[0] + '/'

            # Fetch section files
            sections_data = []
            if 'sections' in base_content:
                sections = base_content['sections']
                if isinstance(sections, str):
                    sections = [sections]

                for section_file in sections:
                    section_url = base_url + section_file
                    logger.info(f"Fetching section: {section_url}")

                    try:
                        section_response = requests.get(
                            section_url, timeout=10
                        )
                        section_response.raise_for_status()
                        section_data = yaml.safe_load(section_response.text)
                        sections_data.append(section_data)
                    except Exception as e:
                        logger.warning(
                            f"Failed to fetch section {section_file}: {e}"
                        )
                        # Continue with other sections

            # Prepare lab data for the builder
            lab_data = {
                'site_name': base_content.get('site_name', ''),
                'lab_name': base_content.get('lab_name', ''),
                'nationality': base_content.get('nationality', ''),
                'galaxy_base_url': base_content.get('galaxy_base_url', ''),
                'subdomain': base_content.get('subdomain', ''),
                'root_domain': base_content.get('root_domain', ''),
                'sections': base_content.get('sections', []),
                'sections_data': sections_data,
                'header_logo': base_content.get('header_logo', ''),
                'custom_css': base_content.get('custom_css', ''),
                'intro_md': base_content.get('intro_md', ''),
                'footer_md': base_content.get('footer_md', ''),
                'conclusion_md': base_content.get('conclusion_md', ''),
                'video_url': base_content.get('video_url', ''),
                'video_tooltip': base_content.get('video_tooltip', ''),
            }

            return JsonResponse({
                'success': True,
                'lab_data': lab_data
            })

        except requests.RequestException as e:
            logger.error(f"GitHub import request error: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Failed to fetch content from GitHub: {str(e)}'
            }, status=400)
        except yaml.YAMLError as e:
            logger.error(f"GitHub import YAML error: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Invalid YAML content: {str(e)}'
            }, status=400)
        except Exception as e:
            logger.error(f"GitHub import error: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    def create_github_pr(self, pr_data):
        """Create a GitHub pull request with the Lab content."""
        try:
            # This is a basic implementation that would need GitHub auth
            # In a real implementation, you'd need:
            # 1. GitHub API token from user
            # 2. Fork the repository
            # 3. Create a branch
            # 4. Commit the YAML files
            # 5. Create a pull request

            # For now, return instructions for manual PR creation
            files = pr_data.get('files', {})

            instructions = [
                "To create a pull request with your Lab content:",
                "1. Fork the target repository on GitHub",
                "2. Create a new branch for your changes",
                "3. Add/update the following files:"
            ]

            for filename in files.keys():
                instructions.append(f"   - {filename}")

            instructions.extend([
                "4. Commit your changes with a descriptive message",
                "5. Push your branch to your fork",
                "6. Create a pull request from your fork to the original "
                "repository"
            ])

            return JsonResponse({
                'success': True,
                'message': 'PR creation instructions generated',
                'instructions': instructions,
                'files': files
            })

        except Exception as e:
            logger.error(f"GitHub PR creation error: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
