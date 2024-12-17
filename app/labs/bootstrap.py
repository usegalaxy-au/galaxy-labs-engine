"""Render a new lab from form data."""

import random
import shutil
import string
import time
import zipfile
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.text import slugify
from pathlib import Path

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
    clean_dir(settings.TEMP_DIR)
    output_dir = settings.TEMP_DIR / random_string(6)
    form_data['logo_filename'] = create_logo(form_data, output_dir)
    render_templates(form_data, output_dir)
    render_server_yml(form_data, output_dir)
    zipfile_path = output_dir.with_suffix('.zip')
    root_dir = Path(slugify(form_data['lab_name']))
    with zipfile.ZipFile(zipfile_path, 'w') as zf:
        for path in output_dir.rglob('*'):
            zf.write(path, root_dir / path.relative_to(output_dir))
    return zipfile_path


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
    ) or settings.BASE_DIR / 'labs/example_labs/docs/static/flask.svg'
    logo_dest_path = output_dir / 'static' / logo_file.name
    logo_dest_path.parent.mkdir(parents=True, exist_ok=True)
    with logo_file.open('rb') as src, logo_dest_path.open('wb') as dest:
        shutil.copyfileobj(src, dest)
    return logo_dest_path.name


def clean_dir(directory):
    """Delete directories that were created more than 7 days ago."""
    for path in directory.iterdir():
        if path.is_dir() and path.stat().st_ctime < time.time() - HOURS_1:
            shutil.rmtree(path)
    return directory
