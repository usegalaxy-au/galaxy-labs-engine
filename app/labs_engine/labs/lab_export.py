"""Exported landing pages to be requested by external Galaxy servers.

Example with local YAML:
http://127.0.0.1:8000/?content_root=http://127.0.0.1:8000/static/labs/content/simple/base.yml

Example URL with remote YAML:
http://127.0.0.1:8000/?content_root=https://raw.githubusercontent.com/usegalaxy-au/galaxy-labs-engine/blob/main/app/labs_engine/labs/content/simple/base.yml

"""

import concurrent.futures
import logging
import re
import requests
import warnings
import yaml
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from django.conf import settings
from markdown2 import Markdown
from pydantic import BaseModel, ValidationError

from types import SimpleNamespace
from labs_engine.utils.exceptions import LabBuildError
from labs_engine.utils.formatters import EmbeddedYouTubeUrl
from labs_engine.utils.terminal import ANSI_GREEN, ANSI_RESET, ANSI_YELLOW
from .lab_schema import LabSchema, LabSectionSchema
from .cache import WebCache

logger = logging.getLogger('django')

ACCEPTED_IMG_EXTENSIONS = ('png', 'jpg', 'jpeg', 'svg', 'webp')
CITATIONS_FILE = 'references.bib'
CONTRIBUTORS_FILE = 'CONTRIBUTORS'
GITHUB_USERNAME_URL = "https://api.github.com/users/{username}"
CONTENT_TYPES = SimpleNamespace(
    WEBPAGE='webpage',
    YAML='yaml',
    TEXT='text',
)

if not settings.GITHUB_API_TOKEN:
    print(
        f"\n{ANSI_YELLOW}"
        "Warning: env variable GITHUB_API_TOKEN not set. Requests"
        " to api.github.com will be rate-limited at 60 requests per hour"
        " which may result in errors (this is used for fetching CONTRIBUTORS"
        f" information).{ANSI_RESET}")
if settings.CLI_DEV:
    print(
        f"\n{ANSI_GREEN} Serving your Lab page at"
        f" http://localhost:8000/{ANSI_RESET}\n")


class ExportLabContext(dict):
    """Build and validate render context for exported lab landing page.

    These page are intended to be displayed externally to the host Galaxy
    (i.e. on a different Galaxy server).

    The context can be built from GET params or from an externally hosted YAML
    context specified by a ``content_root`` GET param.
    """

    FETCH_SNIPPETS = (
        'header_logo',
        'intro_md',
        'footer_md',
        'conclusion_md',
        'custom_css',
    )

    def __init__(self, content_root):
        """Init context from dict."""
        super().__init__(self)
        self['snippets'] = {}
        self.content_root = content_root
        self.parent_url = content_root.rsplit('/', 1)[0] + '/'
        self._fetch_yaml_context()
        self._fetch_sections()
        self._fetch_contributors()
        self._fetch_citations()
        self['title'] = self['lab_name']
        self['video_url'] = EmbeddedYouTubeUrl(self['video_url'])

    def _clean(self):
        """Format params for rendering."""
        self['galaxy_base_url'] = self['galaxy_base_url'].rstrip('/')
        self._filter_sections()

    def validate(self):
        """Validate against required params."""
        self._validate_sections()
        self._clean()

    def _validate_sections(self):
        """Validate sections against Pydantic schema."""
        validated_sections = []
        for section in self['sections']:
            try:
                if not isinstance(section, dict):
                    raise ValidationError(
                        'Section YAML content must be a dictionary.'
                        f' Received type {type(section).__name__} instead.',
                    )
                validated_sections.append(
                    LabSectionSchema(**section).model_dump()
                )
            except ValidationError as e:
                raise LabBuildError(
                    e,
                    section_id=section["id"],
                    source='YAML',
                )
        self['sections'] = validated_sections

    def _get(
        self,
        url,
        expected_type=None,
        ignore_404=False,
    ):
        """Fetch content from URL and validate returned content."""
        url = self._make_raw(url)
        self._validate_url(url, expected_type)
        try:
            res = requests.get(url)
        except requests.exceptions.RequestException as exc:
            raise LabBuildError(exc, url=url)
        if res.status_code >= 300:
            if ignore_404 and res.status_code == 404:
                return
            raise LabBuildError(
                f'HTTP {res.status_code} fetching file.',
                url=url)
        if expected_type != CONTENT_TYPES.WEBPAGE:
            self._validate_not_webpage(url, res, expected_type)
        return res

    def _validate_not_webpage(self, url, response, expected_type=None):
        """Assert that the response body is not a webpage."""
        def looks_like_a_webpage(response):
            body = response.content.decode('utf-8')
            lines = [
                x.strip()
                for x in body.split('\n')
                if x.strip()
            ]
            return any([
                # raw.githubusercontent.com does not set content-type
                'text/html' in response.headers.get('content-type', ''),
                lines and '<!doctype html>' in lines[0].lower(),
                lines and lines[0].lower().startswith('<html'),
            ])

        if looks_like_a_webpage(response):
            expected = expected_type or 'a raw file'
            raise LabBuildError(
                (
                    "Unexpected HTML content in file.\n"
                    'The URL provided returned a webpage (HTML) when'
                    f' {expected} was expected.\n\n'
                    'Response content:\n\n'
                    f'{response.content.decode("utf-8")}'
                ),
                url=url,
                source=expected_type,
            )

    def _validate_url(self, url, expected_type):
        """Validate URL to prevent circular request."""
        if url.strip('/').split('/')[-1] == settings.HOSTNAME:
            raise LabBuildError(
                "URL cannot match the root URL of this server",
                url=url,
                source=expected_type,
            )

    def _make_raw(self, url):
        """Make raw URL for fetching content."""
        if '//github.com' in url:
            url = (
                url.replace('github.com', 'raw.githubusercontent.com')
                .replace('/blob/', '/'))
        return url

    def _fetch_yaml_context(self):
        """Fetch template context from remote YAML file.

        This file is conventionally named <hostname>.yml or base.yml.
        """
        if not self.content_root:
            raise ValueError(
                "GET parameter 'content_root' required for root URL")

        context = self._fetch_yaml_content(self.content_root, extend=False)

        if not self.content_root.endswith('base.yml'):
            # Attempt to extend base.yml with the given content_root
            base_content_url = (self.parent_url + 'base.yml')
            base_context = self._fetch_yaml_content(
                base_content_url, ignore_404=True, extend=False)
            if base_context:
                base_context.update(context)
                context = base_context

        try:
            context = LabSchema(**context).model_dump()
        except ValidationError as exc:
            raise LabBuildError(exc, url=self.content_root, source='YAML')

        self.update(context)
        self._fetch_snippets()

    def _fetch_sections(self):
        """Fetch webpage sections content from remote YAML file."""
        sections = self.get('sections')
        if isinstance(sections, str):
            self['sections'] = [
                self._fetch_yaml_content(self.get('sections'))
            ]
        elif isinstance(sections, list):
            self['sections'] = [
                self._fetch_yaml_content(s)
                for s in sections
            ]
        else:
            raise LabBuildError(
                'The "sections" field must be a string or list of strings,'
                ' each defining the path to a YAML file, relative to base.yml'
                f' (recevied type: {type(sections).__name__})',
                source='YAML',
                url=self.content_root,
            )
        return sections

    def _filter_sections(self):
        """Iterate over sections and remove items based on exclusion tags."""
        def filter_excluded_items(data):
            def is_excluded_item(item):
                return (
                    isinstance(item, dict)
                    and 'exclude_from' in item
                    and self['root_domain'] in item['exclude_from']
                )

            if isinstance(data, dict):
                data = {
                    k: filter_excluded_items(v)
                    for k, v in data.items()
                }
            elif isinstance(data, list):
                data = [
                    filter_excluded_items(item)
                    for item in data
                    if not is_excluded_item(item)
                ]
            elif isinstance(data, BaseModel):
                data = {
                    k: filter_excluded_items(v)
                    for k, v in data.model_dump().items()
                }
            return data

        if self.get('root_domain'):
            self['sections'] = filter_excluded_items(self['sections'])

    def _fetch_yaml_content(self, relpath, ignore_404=False, extend=True):
        """Recursively fetch web content from remote YAML file."""
        yaml_url = self.content_root
        if not (yaml_url and relpath):
            return
        url = (
            relpath if relpath.startswith('http')
            else yaml_url.rsplit('/', 1)[0] + '/' + relpath.lstrip('./')
        )
        res = self._get(
            url,
            expected_type=CONTENT_TYPES.YAML,
            ignore_404=ignore_404,
        )
        if not res:
            return
        yaml_str = res.content.decode('utf-8')

        try:
            data = yaml.safe_load(yaml_str)
        except yaml.YAMLError as exc:
            raise LabBuildError(exc, url=url, source='YAML')
        if isinstance(data, str):
            raise LabBuildError(
                'YAML file must contain a dictionary or list.'
                f' Got a string instead:\n{data}',
                url=url,
                source='YAML',
            )

        if extend and isinstance(data, dict):
            data = {
                # Fetch remote YAML if value is <str>.yml
                k: self._fetch_yaml_content(v) or v
                if isinstance(v, str) and v.split('.')[-1] in ('yml', 'yaml')
                else v
                for k, v in data.items()
            }

        return data

    def _fetch_contributors(self):
        """Attempt to fetch list of contributors from repo."""
        url = self.parent_url + CONTRIBUTORS_FILE
        res = self._get(url, ignore_404=True, expected_type=CONTENT_TYPES.TEXT)
        if res:
            usernames_list = [
                x.strip() for x in res.content.decode('utf-8').split('\n')
                if x.strip()
                and not x.strip().startswith('#')
            ]
            self['contributors'] = fetch_names(usernames_list)
        else:
            self['contributors'] = []

    def _fetch_citations(self):
        """Fetch and parse BibTeX citations into context."""
        url = self.parent_url + CITATIONS_FILE
        res = self._get(url, ignore_404=True, expected_type=CONTENT_TYPES.TEXT)
        if not res:
            self['citations'] = []
            return
        bib_content = res.content.decode('utf-8')
        entries = parse_bibtex_entries(bib_content)
        self['citations'] = [
            {
                'key': e['key'],
                'entry_type': e['entry_type'],
                'fields': e['fields'],
                'raw': e['raw'],
                'formatted': format_citation(e['fields'])
            }
            for e in entries
        ]

    def _fetch_snippets(self):
        """Fetch HTML snippets and add to context.snippets."""
        for name in self.FETCH_SNIPPETS:
            if relpath := self.get(name):
                if relpath.rsplit('.', 1)[1] in ACCEPTED_IMG_EXTENSIONS:
                    self['snippets'][name] = self._fetch_img_src(relpath)
                else:
                    self['snippets'][name] = self._fetch_snippet(relpath)

    def _fetch_img_src(self, relpath):
        """Build URL for image."""
        url = relpath
        if not relpath.startswith('http'):
            url = self.parent_url + relpath.lstrip('./')
        if settings.BUILD_HOSTNAME and settings.BUILD_HOSTNAME in url:
            # When updating cache with local server on localhost, make sure
            # that image URLs contain the real (public) URL
            url = url.replace(
                settings.BUILD_HOSTNAME,
                settings.PUBLIC_HOSTNAME)
        if 'github.com' in url:
            return self._make_raw(url)
        return url

    def _fetch_snippet(self, relpath):
        """Fetch HTML snippet from remote URL."""
        url = (self.parent_url + relpath.lstrip('./'))
        res = self._get(url, expected_type=CONTENT_TYPES.WEBPAGE)
        body = res.content.decode('utf-8')
        if url.endswith('.md'):
            body = self._convert_md(body)
        if url.rsplit('.', 1)[1] in ('html', 'md'):
            self._validate_html(body)
        return body

    def _convert_md(self, text):
        """Render markdown to HTML."""
        engine = Markdown(extras={
            "tables": True,
            "code-friendly": True,
            "html-classes": {
                'table': 'table table-striped',
            },
        })
        return engine.convert(text)

    def _validate_html(self, body):
        """Validate HTML content."""
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', MarkupResemblesLocatorWarning)
                BeautifulSoup(body, 'html.parser')
        except Exception as exc:
            raise LabBuildError(exc, source='HTML')

    def render_relative_uris(self, template_str):
        """Render relative URIs in HTML content."""
        def replace_relative_uri(match):
            attr = match.group(1)
            relpath = match.group(2)
            url = self._make_raw(self.parent_url + relpath)
            return f'{attr}="{url}"'

        return re.sub(
            r'(src|href)="\./([^"]+)"',
            replace_relative_uri,
            template_str,
        )


def get_github_user(username):
    url = GITHUB_USERNAME_URL.format(username=username)
    if cached := WebCache.get(url):
        return cached
    headers = {
        'X-GitHub-Api-Version': '2022-11-28',
    }
    token = settings.GITHUB_API_TOKEN
    if token:
        headers['Authorization'] = f'Bearer {token}'
    try:
        response = requests.get(url, headers=headers)
    except requests.exceptions.ConnectionError as exc:
        logger.warning(f'GitHub API request failed: {exc}')
        return {'login': username}
    if response.status_code == 200:
        user_data = response.json()
        WebCache.put(url, user_data, timeout=2_592_000)
        return user_data
    elif response.status_code == 401:
        logger.warning(
            'GitHub API token unauthorized. Request blocked by rate-limiting.')
    elif response.status_code == 404:
        logger.warning(f'GitHub user not found: {username}')
        WebCache.put(url, {'login': username}, timeout=2_592_000)
    return {'login': username}


def fetch_names(usernames):
    def fetch_name(username):
        return (username, get_github_user(username))

    users = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_username = {
            executor.submit(fetch_name, username): username
            for username in usernames
        }
        for future in concurrent.futures.as_completed(future_to_username):
            _, user_data = future.result()
            users.append(user_data)
    users.sort(key=lambda x:
               usernames.index(x.get('login'))
               if x and x.get('avatar_url') and x.get('login') in usernames
               else 9999)

    return users


def parse_bibtex_entries(text):
    """Very small BibTeX parser for simple entries."""
    entries = []
    # Split on '@' but keep it for reconstruction
    chunks = [c for c in text.split('@') if c.strip()]
    for chunk in chunks:
        raw_entry = '@' + chunk.strip()
        header_match = re.match(r'(\w+)\s*\{\s*([^,]+)\s*,', chunk, re.DOTALL)
        if not header_match:
            continue
        entry_type, key = header_match.groups()
        body = chunk[header_match.end():]
        # Remove enclosing final brace if present
        body = body.rsplit('}', 1)[0]
        fields = {}
        # Regex to capture field lines like: field = {value} or field = "value"
        field_pattern = re.compile(
            r'(\w+)\s*=\s*(\{[^}]*\}|"[^"]*"|[^,]+)',
            re.MULTILINE)
        for m in field_pattern.finditer(body):
            fkey = m.group(1).strip().lower()
            fval = m.group(2).strip().strip(',').strip()
            if (
                fval.startswith('{')
                and fval.endswith('}')
            ) or (
                fval.startswith('"')
                and fval.endswith('"')
            ):
                fval = fval[1:-1].strip()
            fields[fkey] = fval
        entries.append({
            'entry_type': entry_type.lower(),
            'key': key.strip(),
            'fields': fields,
            'raw': raw_entry,
        })
    return entries


def format_citation(fields):
    """Build a simple HTML string for a citation from parsed fields."""
    authors_raw = fields.get('author', '')
    authors = []
    if authors_raw:
        for part in authors_raw.split(' and '):
            part = part.strip()
            if ',' in part:
                # Already Last, First
                authors.append(part)
            else:
                bits = part.split()
                if len(bits) > 1:
                    authors.append(bits[-1] + ', ' + ' '.join(bits[:-1]))
                else:
                    authors.append(part)
    authors_str = '; '.join(authors)
    year = fields.get('year', '')
    title = fields.get('title', '')
    journal = fields.get('journal') or fields.get('booktitle') or ''
    doi = fields.get('doi', '')
    url = fields.get('url', '')
    parts = []
    if authors_str:
        parts.append(authors_str)
    if year:
        parts.append(f' ({year}).')
    if title:
        parts.append(f' <i>{title}</i>.')
    if journal:
        parts.append(f' {journal}.')
    if doi:
        # Prefer DOI link
        doi_link = doi
        if not doi.startswith('http'):  # Assume raw DOI identifier
            doi_link = 'https://doi.org/' + doi
        parts.append(f' <a href="{doi_link}" target="_blank">{doi}</a>.')
    if url and not doi:
        parts.append(f' <a href="{url}" target="_blank">Link</a>.')
    formatted = ''.join(parts).strip()
    return formatted or title or authors_str or ''
