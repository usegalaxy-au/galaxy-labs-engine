"""Render a new lab from form data."""

import logging
import random
import shutil
import string
import time
import zipfile
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.text import slugify
from pathlib import Path

from .ai_generate import generate_lab_content
from .ai_generate.generator import AIGenerationError

logger = logging.getLogger('django')

HOURS_1 = 60 * 60
ALPHANUMERIC = string.ascii_letters + string.digits
TEMPLATE_DIR = Path('labs/bootstrap')
TEMPLATES_TO_RENDER = [
    'base.yml',
    'intro.md',
    'conclusion.md',
    'footer.md',
    'section-1.yml',
    'README.md',
    'custom.css',
    'CONTRIBUTORS',
]
GALAXY_SERVERS = {
    '': 'usegalaxy.org',
    'Europe': 'usegalaxy.eu',
    'Australia': 'usegalaxy.org.au',
}


def random_string(length):
    return ''.join(random.choices(ALPHANUMERIC, k=length))


def lab(form_data):
    """Render a new lab from form data."""
    clean_dir(settings.INTERNAL_ROOT)
    output_dir = settings.INTERNAL_ROOT / random_string(6)
    form_data['logo_filename'] = create_logo(form_data, output_dir)
    render_templates(form_data, output_dir)
    render_server_yml(form_data, output_dir)
    reference_md = form_data.get('reference_md')
    if reference_md:
        try:
            ai_content = generate_lab_content(
                lab_name=form_data['lab_name'],
                reference_md=reference_md,
            )
        except AIGenerationError as exc:
            logger.error("AI lab generation failed: %s", exc)
        else:
            inject_ai_content(ai_content, output_dir)
    zipfile_path = output_dir.with_suffix('.zip')
    root_dir = Path(slugify(form_data['lab_name']))
    with zipfile.ZipFile(zipfile_path, 'w') as zf:
        for path in output_dir.rglob('*'):
            zf.write(path, root_dir / path.relative_to(output_dir))
    logger.debug('Created lab zipfile: %s' % zipfile_path)
    return Path(str(zipfile_path).replace(str(settings.INTERNAL_ROOT), ''))


def inject_ai_content(ai_content, output_dir):
    """Overwrite template files with AI-generated Lab content.

    The AI returns a dict matching ``ai_generate.generator.RESPONSE_SCHEMA``:
    intro_md, conclusion_md, footer_md, base_yml, servers (list of
    {hostname, content}) and sections (list of {filename, content}).
    """
    templates_dir = output_dir / 'templates'
    sections_dir = output_dir / 'sections'
    templates_dir.mkdir(parents=True, exist_ok=True)
    sections_dir.mkdir(parents=True, exist_ok=True)

    (templates_dir / 'intro.md').write_text(ai_content['intro_md'])
    (templates_dir / 'conclusion.md').write_text(
        ai_content['conclusion_md']
    )
    (templates_dir / 'footer.md').write_text(ai_content['footer_md'])
    (output_dir / 'base.yml').write_text(ai_content['base_yml'])

    # Remove the placeholder section file shipped by render_templates so
    # it doesn't conflict with the AI-generated sections.
    placeholder = sections_dir / 'section-1.yml'
    if placeholder.exists():
        placeholder.unlink()
    for section in ai_content.get('sections', []):
        filename = Path(section['filename']).name
        (sections_dir / filename).write_text(section['content'])

    # Replace the default per-server YAML files with AI-generated ones.
    for server in ai_content.get('servers', []):
        hostname = server['hostname'].strip()
        if not hostname:
            continue
        if not hostname.endswith('.yml'):
            filename = f'{hostname}.yml'
        else:
            filename = hostname
        (output_dir / filename).write_text(server['content'])


def render_templates(data, output_dir):
    for template in TEMPLATES_TO_RENDER:
        subdir = None
        if template.endswith('.md') and 'README' not in template:
            subdir = 'templates'
        elif template.endswith('css'):
            subdir = 'static'
        elif template == 'section-1.yml':
            subdir = 'sections'
        render_file(
            data,
            template,
            output_dir,
            subdir=subdir,
        )


def render_file(data, template, output_dir, subdir=None, filename=None):
    outfile_relpath = filename or template
    if subdir:
        outfile_relpath = Path(subdir) / outfile_relpath
    path = output_dir / outfile_relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    content = render_to_string(TEMPLATE_DIR / template, data)
    path.write_text(content)
    return path


def render_server_yml(data, output_dir):
    """Create a YAML file for each Galaxy server."""
    for site_name, root_domain in GALAXY_SERVERS.items():
        data['site_name'] = site_name
        data['galaxy_base_url'] = (
            'https://'
            + data['subdomain']
            + '.'
            + root_domain
        )
        data['root_domain'] = root_domain
        render_file(
            data,
            'server.yml',
            output_dir,
            filename=f'{root_domain}.yml',
        )


def create_logo(data, output_dir):
    """Copy the uploaded logo to the output directory."""
    logo_file = data.get(
        'logo'
    )
    if logo_file:
        logo_dest_path = output_dir / 'static' / logo_file.name
    else:
        logo_file = (
            settings.BASE_DIR
            / 'labs_engine/labs/example_labs/docs/static/flask.svg'
        )
        logo_dest_path = output_dir / 'static/logo.svg'
    logo_dest_path.parent.mkdir(parents=True, exist_ok=True)
    with logo_file.open('rb') as src, logo_dest_path.open('wb') as dest:
        shutil.copyfileobj(src, dest)
    return logo_dest_path.name


def clean_dir(directory):
    """Delete directories that were created more than 7 days ago."""
    if directory.exists():
        for path in directory.iterdir():
            if path.is_dir() and path.stat().st_ctime < time.time() - HOURS_1:
                shutil.rmtree(path)
    return directory
