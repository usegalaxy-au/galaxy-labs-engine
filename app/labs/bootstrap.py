"""Render a new lab from form data."""

import random
import shutil
import string
import time
import zipfile
from django.conf import settings
from django.template.loader import render_to_string
from pathlib import Path

HOURS_72 = 3 * 24 * 60 * 60
ALPHANUMERIC = string.ascii_letters + string.digits
TEMPLATE_DIR = Path('labs/boilerplate')
TEMPLATES_TO_RENDER = [
    'base.yml',
    'intro.md',
    'conclusion.md',
    'footer.md',
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
    form_data.update({
        'intro_md': 'Welcome to the Galaxy {{ site_name }} {{ lab_name }}!',
        'conclusion_md': ('Thanks for checking out the Galaxy {{ site_name }}'
                          ' {{ lab_name }}!'),
        'footer_md': 'Some text to be displayed in the footer.',
        'galaxy_base_url': f"https://{form_data['subdomain']}.usegalaxy.org",
    })
    render_templates(form_data, output_dir)
    render_server_yml(form_data, output_dir)
    insert_logo(form_data, output_dir)
    zipfile_path = output_dir.with_suffix('.zip')
    with zipfile.ZipFile(zipfile_path, 'w') as zf:
        for path in output_dir.rglob('*'):
            zf.write(path, path.relative_to(output_dir))
    return zipfile_path


def render_templates(data, output_dir):
    for template in TEMPLATES_TO_RENDER:
        subdir = 'templates' if template.endswith('.md') else None
        filename = (
            data['root_domain'] + '.yml'
            if template == 'server.yml'
            else None
        )
        render_file(
            data,
            template,
            output_dir,
            subdir=subdir,
            filename=filename,
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


def insert_logo(data, output_dir):
    """Copy the uploaded logo to the output directory."""
    logo = data.get('logo')
    if logo:
        logo_path = output_dir / 'static' / logo.name
        logo_path.parent.mkdir(parents=True, exist_ok=True)
        with logo.open('rb') as src, logo_path.open('wb') as dest:
            shutil.copyfileobj(src, dest)


def clean_dir(directory):
    """Delete directories that were created more than 7 days ago."""
    for path in directory.iterdir():
        if path.is_dir() and path.stat().st_ctime < time.time() - HOURS_72:
            shutil.rmtree(path)
    return directory
