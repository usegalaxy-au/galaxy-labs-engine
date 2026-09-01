import requests
import requests_mock
from django.core.cache import cache
from django.test import override_settings
from django.utils.http import urlencode
from pathlib import Path
from unittest.mock import Mock, patch

from labs_engine.utils.formatters import EmbeddedYouTubeUrl
from .cache import LabCache
from .cloudflare import CLOUDFLARE_PURGE_URL
from .lab_export import ExportLabContext
from .models import CachedLab
from .audit import (
    extract_tool_links,
    check_tool_exists,
    audit_tools_concurrent,
    perform_template_audit,
    add_audit_template_tags,
)
from .test.data import (
    MOCK_REQUESTS,
    MOCK_LAB_BASE_URL,
)
from labs_engine.app.test import TestCase

TEST_DATA_DIR = Path(__file__).parent / 'test/data'
TEST_LAB_NAME = 'Lab Docs'
TEST_LAB_LAB_NAME = 'Galaxy labs engine'.upper()
TEST_LAB_NATIONALITY = 'Antarctican'
TEST_LAB_GALAXY_BASE_URL = 'https://galaxy-antarctica.org'
TEST_LAB_SECTION_TEXT = 'Example section'
TEST_LAB_ACCORDION_TEXT = (
    'Report statistics from sequencing reads',
    'Assemble Nanopore long reads.',
)
TEST_LAB_CONTENT_URL = f'{MOCK_LAB_BASE_URL}/static/labs/content/docs/base.yml'
TEST_LAB_URL = f'/?content_root={TEST_LAB_CONTENT_URL}'

# Test constants for audit functionality
TEST_GALAXY_SERVER_URL = 'https://usegalaxy.org.au'
# Note: URL decoding converts %2F back to / in parsed URLs
TEST_VALID_TOOL_ID = 'toolshed.g2.bx.psu.edu/repos/galaxyp/diann/diann'
TEST_INVALID_TOOL_ID = 'toolshed.g2.bx.psu.edu/repos/galaxyp/blahblah/blahblah'
TEST_VALID_TOOL_URL = (
    f'{TEST_GALAXY_SERVER_URL}/?tool_id='
    'toolshed.g2.bx.psu.edu%2Frepos%2Fgalaxyp%2Fdiann%2Fdiann'
)
TEST_INVALID_TOOL_URL = (
    f'{TEST_GALAXY_SERVER_URL}/?tool_id='
    'toolshed.g2.bx.psu.edu%2Frepos%2Fgalaxyp%2Fblahblah%2Fblahblah'
)

# Test constants for Cloudflare cache purging
TEST_CLOUDFLARE_ZONE_ID = 'testzoneid'
TEST_CLOUDFLARE_API_TOKEN = 'testapitoken'
TEST_CLOUDFLARE_PURGE_URL = CLOUDFLARE_PURGE_URL.format(
    zone_id=TEST_CLOUDFLARE_ZONE_ID)
TEST_CLOUDFLARE_RESPONSE = {'success': True, 'errors': [], 'messages': []}
TEST_SITE_URL = 'http://testserver'
TEST_CONTENT_ROOT_QUERY = f'content_root={TEST_LAB_CONTENT_URL}'
TEST_CACHED_LAB_URL = f'/?{TEST_CONTENT_ROOT_QUERY}'
TEST_CACHED_LAB_AUDIT_URL = f'/?{TEST_CONTENT_ROOT_QUERY}&audit=true'
TEST_CACHED_LAB_ENCODED_URL = '/?' + urlencode({
    'content_root': TEST_LAB_CONTENT_URL,
})
TEST_CACHED_OTHER_LAB_URL = (
    f'/?content_root={MOCK_LAB_BASE_URL}/static/labs/content/other/base.yml')


class LabExportTestCase(TestCase):
    """Test exported lab site building functionality."""

    @requests_mock.Mocker()
    def setUp(self, mock_request):
        for r in MOCK_REQUESTS:
            mock_request.get(r['url_pattern'],
                             text=r['response'],
                             status_code=r.get('status_code', 200))
        self.context = ExportLabContext(TEST_LAB_CONTENT_URL)

    @requests_mock.Mocker()
    def test_exported_lab_docs(self, mock_request):
        """Mock requests to localhost."""
        for r in MOCK_REQUESTS:
            mock_request.get(r['url_pattern'],
                             text=r['response'],
                             status_code=r.get('status_code', 200))
        response = self.client.get(TEST_LAB_URL)
        self.assertEqual(
            response.status_code,
            200,
            f"Unexpected HTTP status from request to {TEST_LAB_URL}",
        )
        self.assertContains(response, TEST_LAB_NAME)
        self.assertContains(response, TEST_LAB_LAB_NAME)
        self.assertContains(response, TEST_LAB_GALAXY_BASE_URL)
        self.assertContains(response, TEST_LAB_SECTION_TEXT)
        for text in TEST_LAB_ACCORDION_TEXT:
            self.assertContains(response, text)

    def test_it_can_make_raw_url(self):
        self.assertEqual(
            self.context._make_raw('https://github.com/neoformit/'
                                   'galaxy-labs-engine/blob/dev/README.md'),
            'https://raw.githubusercontent.com/neoformit/'
            'galaxy-labs-engine/dev/README.md')

    def test_it_can_filter_sections_by_root_domain(self):
        hostname = 'antarctica.org'
        self.context['root_domain'] = hostname
        self.context['sections'] = [
            {'id': 'section1'},
            {
                'id': 'section2',
                'exclude_from': [hostname],
            },
            {
                'id': 'section3',
                'content': [
                    {
                        'id': 'item1',
                    },
                    {
                        'id': 'item2',
                        'exclude_from': [hostname],
                    },
                    {
                        'id': 'item3',
                        'exclude_from': ['other.domain.com'],
                    },
                    {
                        'id': 'item4',
                        'exclude_from': [hostname, 'other.domain.com'],
                    },
                ]
            },
        ]
        self.context._filter_sections()
        self.assertEqual(
            self.context['sections'],
            [
                {'id': 'section1'},
                {
                    'id': 'section3',
                    'content': [
                        {
                            'id': 'item1',
                        },
                        {
                            'id': 'item3',
                            'exclude_from': ['other.domain.com'],
                        },
                    ]
                },
            ],
        )

    @requests_mock.Mocker()
    def test_exported_lab_citations(self, mock_request):
        """Ensure citations are parsed from references.bib and available."""
        for r in MOCK_REQUESTS:
            mock_request.get(r['url_pattern'],
                             text=r['response'],
                             status_code=r.get('status_code', 200))
        context = ExportLabContext(TEST_LAB_CONTENT_URL)
        self.assertIn('citations', context)
        self.assertGreaterEqual(len(context['citations']), 2)
        first = context['citations'][0]
        self.assertIn('formatted', first)
        # Check basic formatting pieces
        self.assertIn('10.1234/example.doi', first['formatted'])
        self.assertTrue(
            any(
                'Example Galaxy Lab' in c['formatted']
                for c in context['citations']
            )
        )

    @requests_mock.Mocker()
    def test_exported_lab_citations_page(self, mock_request):
        """Request exported page and verify References section rendered."""
        for r in MOCK_REQUESTS:
            mock_request.get(r['url_pattern'],
                             text=r['response'],
                             status_code=r.get('status_code', 200))
        response = self.client.get(TEST_LAB_URL)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cite this Lab')
        self.assertContains(response, 'doi.org')


class AuditTestCase(TestCase):
    """Test audit functionality for tool link checking."""

    def setUp(self):
        """Set up test data."""
        self.html_with_tools = f'''
        <html>
            <body>
                <a href="{TEST_VALID_TOOL_URL}">Valid Tool</a>
                <a href="{TEST_INVALID_TOOL_URL}">Invalid Tool</a>
                <a href="https://example.com">Non-tool Link</a>
                <a href="{TEST_GALAXY_SERVER_URL}/?tool_id=another_tool">
                    Another Tool
                </a>
            </body>
        </html>
        '''

        self.html_without_tools = '''
        <html>
            <body>
                <a href="https://example.com">Regular Link</a>
                <a href="https://google.com">Another Link</a>
            </body>
        </html>
        '''

    def test_extract_tool_links_finds_valid_tools(self):
        """Test that extract_tool_links finds all tool links in HTML."""
        tool_links = extract_tool_links(self.html_with_tools)

        self.assertEqual(len(tool_links), 3)

        # Check that all tool URLs are extracted
        urls = [link['url'] for link in tool_links]
        self.assertIn(TEST_VALID_TOOL_URL, urls)
        self.assertIn(TEST_INVALID_TOOL_URL, urls)
        expected_another_tool_url = (
            f'{TEST_GALAXY_SERVER_URL}/?tool_id=another_tool'
        )
        self.assertIn(expected_another_tool_url, urls)

        # Check that tool IDs are correctly parsed
        tool_ids = [link['tool_id'] for link in tool_links]
        self.assertIn(TEST_VALID_TOOL_ID, tool_ids)
        self.assertIn(TEST_INVALID_TOOL_ID, tool_ids)
        self.assertIn('another_tool', tool_ids)

        # Check that link text is extracted
        link_texts = [link['link_text'] for link in tool_links]
        self.assertIn('Valid Tool', link_texts)
        self.assertIn('Invalid Tool', link_texts)

    def test_extract_tool_links_ignores_non_tool_links(self):
        """Test that extract_tool_links ignores non-tool links."""
        tool_links = extract_tool_links(self.html_without_tools)
        self.assertEqual(len(tool_links), 0)

    def test_extract_tool_links_handles_empty_html(self):
        """Test that extract_tool_links handles empty HTML."""
        tool_links = extract_tool_links('')
        self.assertEqual(len(tool_links), 0)

    @patch('labs_engine.labs.audit.WebCache')
    @patch('labs_engine.labs.audit.GalaxyInstance')
    def test_check_tool_exists_with_valid_tool(
        self,
        mock_galaxy_instance,
        mock_cache,
    ):
        """Test check_tool_exists with a valid tool."""
        # Mock cache miss
        mock_cache.get.return_value = None

        mock_gi = Mock()
        mock_galaxy_instance.return_value = mock_gi
        mock_gi.tools.show_tool.return_value = {'id': TEST_VALID_TOOL_ID}

        tool_id, exists, error = check_tool_exists(
            TEST_GALAXY_SERVER_URL,
            TEST_VALID_TOOL_ID
        )

        self.assertEqual(tool_id, TEST_VALID_TOOL_ID)
        self.assertTrue(exists)
        self.assertEqual(error, '')
        mock_gi.tools.show_tool.assert_called_once_with(TEST_VALID_TOOL_ID)
        mock_cache.put.assert_called_once()

    @patch('labs_engine.labs.audit.GalaxyInstance')
    def test_check_tool_exists_with_invalid_tool(self, mock_galaxy_instance):
        """Test check_tool_exists with an invalid tool."""
        mock_gi = Mock()
        mock_galaxy_instance.return_value = mock_gi
        mock_gi.tools.show_tool.side_effect = Exception(
            '404 Not Found'
        )

        tool_id, exists, error = check_tool_exists(
            TEST_GALAXY_SERVER_URL,
            TEST_INVALID_TOOL_ID
        )

        self.assertEqual(tool_id, TEST_INVALID_TOOL_ID)
        self.assertFalse(exists)
        self.assertEqual(error, 'Tool not found')

    @patch('labs_engine.labs.audit.GalaxyInstance')
    def test_check_tool_exists_with_connection_error(
        self, mock_galaxy_instance
    ):
        """Test check_tool_exists with connection error."""
        mock_galaxy_instance.side_effect = Exception('Connection failed')

        tool_id, exists, error = check_tool_exists(
            TEST_GALAXY_SERVER_URL,
            TEST_VALID_TOOL_ID
        )

        self.assertEqual(tool_id, TEST_VALID_TOOL_ID)
        self.assertFalse(exists)
        self.assertIn('Connection error', error)

    @patch('labs_engine.labs.audit.check_tool_exists')
    def test_audit_tools_concurrent_with_mixed_results(
        self, mock_check_tool
    ):
        """Test audit_tools_concurrent with both valid and invalid tools."""
        def mock_check_side_effect(galaxy_url, tool_id, api_key=None):
            del galaxy_url, api_key  # Unused parameters
            """Mock check_tool_exists to return different results."""
            if tool_id == TEST_VALID_TOOL_ID:
                return (tool_id, True, '')
            else:
                return (tool_id, False, 'Tool not found')

        tool_links = [
            {
                'url': TEST_VALID_TOOL_URL,
                'tool_id': TEST_VALID_TOOL_ID,
                'link_text': 'Valid Tool'
            },
            {
                'url': TEST_INVALID_TOOL_URL,
                'tool_id': TEST_INVALID_TOOL_ID,
                'link_text': 'Invalid Tool'
            }
        ]

        mock_check_tool.side_effect = mock_check_side_effect

        results = audit_tools_concurrent(TEST_GALAXY_SERVER_URL, tool_links)

        self.assertEqual(len(results), 2)

        # Check valid tool result
        valid_result = results[TEST_VALID_TOOL_ID]
        self.assertTrue(valid_result['exists'])
        self.assertEqual(valid_result['error'], '')
        self.assertEqual(valid_result['link_text'], 'Valid Tool')

        # Check invalid tool result
        invalid_result = results[TEST_INVALID_TOOL_ID]
        self.assertFalse(invalid_result['exists'])
        self.assertEqual(invalid_result['error'], 'Tool not found')
        self.assertEqual(invalid_result['link_text'], 'Invalid Tool')

    def test_audit_tools_concurrent_with_empty_list(self):
        """Test audit_tools_concurrent with empty tool list."""
        results = audit_tools_concurrent(TEST_GALAXY_SERVER_URL, [])
        self.assertEqual(results, {})

    def test_perform_template_audit_without_audit_param(self):
        """Test perform_template_audit when audit param is not present."""
        request = Mock()
        request.GET = {}
        context = {'galaxy_base_url': TEST_GALAXY_SERVER_URL}
        template_str = self.html_with_tools

        result_template, result_context = perform_template_audit(
            template_str,
            context,
            request
        )

        # Should return unchanged template and context
        self.assertEqual(result_template, template_str)
        self.assertEqual(result_context, context)

    @patch('labs_engine.labs.audit.audit_tools_concurrent')
    def test_perform_template_audit_with_audit_param(
        self,
        mock_audit_tools
    ):
        """Test perform_template_audit when audit param is present."""
        request = Mock()
        request.GET = {'audit': '1'}
        context = {'galaxy_base_url': TEST_GALAXY_SERVER_URL}
        template_str = '<section>Header</section>' + self.html_with_tools

        # Mock audit results for all 3 tools in html_with_tools
        mock_audit_results = {
            TEST_VALID_TOOL_ID: {
                'tool_id': TEST_VALID_TOOL_ID,
                'exists': True,
                'error': ''
            },
            TEST_INVALID_TOOL_ID: {
                'tool_id': TEST_INVALID_TOOL_ID,
                'exists': False,
                'error': 'Tool not found'
            },
            'another_tool': {
                'tool_id': 'another_tool',
                'exists': False,
                'error': 'Tool not found'
            }
        }
        mock_audit_tools.return_value = mock_audit_results

        result_template, result_context = perform_template_audit(
            template_str,
            context,
            request
        )

        # Check that audit flag is set
        self.assertTrue(result_context['audit'])

        # Check that audit results are in context
        self.assertEqual(result_context['audit_results'], mock_audit_results)

        # Check that audit summary is calculated
        # Note: html_with_tools contains 3 tool links
        expected_summary = {
            'total_tools': 3,
            'working_tools': 1,
            # TEST_INVALID_TOOL_ID and another_tool both fail
            'broken_tools': 2
        }
        self.assertEqual(result_context['audit_summary'], expected_summary)

        # Check that template is rendered (contains HTML from audit.html)
        self.assertIn('auditModal', result_template)
        self.assertIn('Show Audit Results', result_template)

    def test_perform_template_audit_with_no_galaxy_url(self):
        """Test perform_template_audit when galaxy_base_url is missing."""
        request = Mock()
        request.GET = {'audit': '1'}
        context = {}  # No galaxy_base_url
        template_str = '<section>Header</section>' + self.html_with_tools

        result_template, result_context = perform_template_audit(
            template_str,
            context,
            request
        )

        # Should set audit error
        self.assertTrue(result_context['audit'])
        self.assertEqual(
            result_context['audit_error'],
            'No Galaxy server URL found'
        )
        # Check that template is rendered (contains HTML from audit.html)
        self.assertIn('auditModal', result_template)
        self.assertIn('Audit Error:', result_template)

    def test_add_audit_template_tags(self):
        """Test add_audit_template_tags function."""
        template_str = (
            '<section>Header content</section><div>Body content</div>')

        result = add_audit_template_tags(template_str)

        # Check that audit tags are inserted after the first </section>
        self.assertIn('{% if audit %}', result)
        self.assertIn('{% include \'labs/snippets/audit.html\' %}', result)
        self.assertIn('</section>', result)

        # Verify the tags are after the first </section>
        section_end = result.find('</section>') + len('</section>')
        audit_start = result.find('{% if audit %}')
        self.assertGreater(audit_start, section_end)

    def test_add_audit_template_tags_no_section(self):
        """Test add_audit_template_tags when no section tag exists."""
        template_str = '<div>Content without section</div>'

        result = add_audit_template_tags(template_str)

        # Should return unchanged template when no </section> found
        self.assertEqual(result, template_str)


@override_settings(
    CLOUDFLARE_ZONE_ID=TEST_CLOUDFLARE_ZONE_ID,
    CLOUDFLARE_API_TOKEN=TEST_CLOUDFLARE_API_TOKEN,
)
class CloudflarePurgeTestCase(TestCase):
    """Test purging of the Cloudflare cache on ?cache=false requests."""

    def setUp(self):
        super().setUp()
        # Reset the purge debounce between tests
        cache.clear()
        CachedLab.objects.create(key='a' * 32, url=TEST_CACHED_LAB_URL)
        CachedLab.objects.create(key='b' * 32, url=TEST_CACHED_LAB_AUDIT_URL)
        CachedLab.objects.create(key='c' * 32, url=TEST_CACHED_OTHER_LAB_URL)

    def mock_lab_requests(self, mock_request):
        """Mock the remote Lab content requests made while rendering."""
        for r in MOCK_REQUESTS:
            mock_request.get(r['url_pattern'],
                             text=r['response'],
                             status_code=r.get('status_code', 200))

    def get_lab(self, mock_request, cache_param='false'):
        """Request the test Lab page, optionally bypassing the cache."""
        self.mock_lab_requests(mock_request)
        url = TEST_LAB_URL
        if cache_param is not None:
            url += f'&cache={cache_param}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return response

    def get_purge_requests(self, mock_request):
        """Return requests made to the Cloudflare purge endpoint."""
        return [
            r for r in mock_request.request_history
            if r.url == TEST_CLOUDFLARE_PURGE_URL
        ]

    @requests_mock.Mocker()
    def test_it_purges_all_urls_for_content_root(self, mock_request):
        mock_request.post(
            TEST_CLOUDFLARE_PURGE_URL, json=TEST_CLOUDFLARE_RESPONSE)
        self.get_lab(mock_request)

        purge_requests = self.get_purge_requests(mock_request)
        self.assertEqual(len(purge_requests), 1)
        self.assertEqual(
            purge_requests[0].headers['Authorization'],
            f'Bearer {TEST_CLOUDFLARE_API_TOKEN}')

        files = purge_requests[0].json()['files']
        self.assertIn(TEST_SITE_URL + TEST_CACHED_LAB_URL, files)
        self.assertIn(TEST_SITE_URL + TEST_CACHED_LAB_AUDIT_URL, files)
        self.assertNotIn(TEST_SITE_URL + TEST_CACHED_OTHER_LAB_URL, files)
        # The cache=false param must not be purged - it isn't cached
        for url in files:
            self.assertNotIn('cache=false', url)

    @requests_mock.Mocker()
    def test_it_purges_urls_as_requested_by_the_client(self, mock_request):
        """The content_root must not be re-encoded - Cloudflare caches the
        URL exactly as the client requested it.
        """
        mock_request.post(
            TEST_CLOUDFLARE_PURGE_URL, json=TEST_CLOUDFLARE_RESPONSE)
        self.get_lab(mock_request)

        files = self.get_purge_requests(mock_request)[0].json()['files']
        self.assertIn(
            f'{TEST_SITE_URL}/?content_root={TEST_LAB_CONTENT_URL}', files)
        self.assertNotIn(TEST_SITE_URL + TEST_CACHED_LAB_ENCODED_URL, files)

    @requests_mock.Mocker()
    def test_it_purges_urls_cached_in_encoded_form(self, mock_request):
        """A URL-encoded content_root is a valid request in its own right."""
        mock_request.post(
            TEST_CLOUDFLARE_PURGE_URL, json=TEST_CLOUDFLARE_RESPONSE)
        CachedLab.objects.create(
            key='d' * 32, url=TEST_CACHED_LAB_ENCODED_URL)
        self.get_lab(mock_request)

        files = self.get_purge_requests(mock_request)[0].json()['files']
        self.assertIn(TEST_SITE_URL + TEST_CACHED_LAB_ENCODED_URL, files)

    @requests_mock.Mocker()
    def test_it_does_not_purge_without_cache_param(self, mock_request):
        mock_request.post(
            TEST_CLOUDFLARE_PURGE_URL, json=TEST_CLOUDFLARE_RESPONSE)
        self.get_lab(mock_request, cache_param=None)
        self.assertEqual(len(self.get_purge_requests(mock_request)), 0)

    @override_settings(CLOUDFLARE_ZONE_ID=None, CLOUDFLARE_API_TOKEN=None)
    @requests_mock.Mocker()
    def test_it_does_not_purge_without_credentials(self, mock_request):
        mock_request.post(
            TEST_CLOUDFLARE_PURGE_URL, json=TEST_CLOUDFLARE_RESPONSE)
        self.get_lab(mock_request)
        self.assertEqual(len(self.get_purge_requests(mock_request)), 0)

    @requests_mock.Mocker()
    def test_it_debounces_repeated_purge_requests(self, mock_request):
        mock_request.post(
            TEST_CLOUDFLARE_PURGE_URL, json=TEST_CLOUDFLARE_RESPONSE)
        self.get_lab(mock_request)
        self.get_lab(mock_request)
        self.assertEqual(len(self.get_purge_requests(mock_request)), 1)

    @requests_mock.Mocker()
    def test_it_batches_purge_requests(self, mock_request):
        mock_request.post(
            TEST_CLOUDFLARE_PURGE_URL, json=TEST_CLOUDFLARE_RESPONSE)
        batch_size = 30
        for i in range(batch_size * 2):
            CachedLab.objects.create(
                key=f'{i:032d}',
                url=f'{TEST_CACHED_LAB_URL}&nonce={i}')
        self.get_lab(mock_request)

        purge_requests = self.get_purge_requests(mock_request)
        self.assertEqual(len(purge_requests), 3)
        for request in purge_requests:
            self.assertLessEqual(len(request.json()['files']), batch_size)

    @patch('labs_engine.labs.cache.NOCACHE', False)
    @patch('labs_engine.labs.cache.purge_cache_for_request')
    @requests_mock.Mocker()
    def test_it_purges_after_the_page_has_been_recached(
        self,
        mock_purge,
        mock_request,
    ):
        """The fresh page must be cached before the edge can re-request it."""
        cached_body = {}

        def record_cached_body(request, url):
            key, _ = LabCache._generate_cache_key(request)
            cached_body['value'] = cache.get(key)

        mock_purge.side_effect = record_cached_body
        self.get_lab(mock_request)

        mock_purge.assert_called_once()
        self.assertIn(TEST_LAB_NAME, cached_body['value'])

    @requests_mock.Mocker()
    def test_it_serves_page_when_purge_fails(self, mock_request):
        mock_request.post(TEST_CLOUDFLARE_PURGE_URL, status_code=500)
        response = self.get_lab(mock_request)
        self.assertContains(response, TEST_LAB_NAME)

    @requests_mock.Mocker()
    def test_it_reports_zero_purged_on_cloudflare_error(self, mock_request):
        """Cloudflare returns HTTP 200 with success=false for bad URLs."""
        mock_request.post(TEST_CLOUDFLARE_PURGE_URL, json={
            'success': False,
            'errors': [{'code': 1140, 'message': 'Unable to purge'}],
        })
        with self.assertLogs('django.cache', level='INFO') as logs:
            self.get_lab(mock_request)
        self.assertTrue(
            any('Purged 0/' in message for message in logs.output),
            f'Expected a zero-purge log message, got: {logs.output}')

    @requests_mock.Mocker()
    def test_it_serves_page_when_purge_times_out(self, mock_request):
        mock_request.post(
            TEST_CLOUDFLARE_PURGE_URL, exc=requests.Timeout)
        response = self.get_lab(mock_request)
        self.assertContains(response, TEST_LAB_NAME)


class FormatterTestCase(TestCase):
    """Test data formatters."""

    def test_youtube_url_formatter(self):
        """Test YouTube URL formatter."""

        WEB_URL = 'https://www.youtube.com/watch/'
        WEB_URL_SHORT = 'https://youtu.be/'
        EMBED_URL = 'https://www.youtube.com/embed/'

        test_cases = {
            f'{WEB_URL}?v=dQw4w9WgXcQ':
                f'{EMBED_URL}dQw4w9WgXcQ?rel=0&showinfo=0',
            f'{WEB_URL_SHORT}dQw4w9WgXcQ':
                f'{EMBED_URL}dQw4w9WgXcQ?rel=0&showinfo=0',
            f'{WEB_URL}?v=dQw4w9WgXcQ&ab_channel=RickAmp':
                f'{EMBED_URL}dQw4w9WgXcQ?rel=0&showinfo=0',
            f'{WEB_URL_SHORT}dQw4w9WgXcQ?t=42':
                f'{EMBED_URL}dQw4w9WgXcQ?t=42&rel=0&showinfo=0',
            'https://example.com/video':
                'https://example.com/video',
            '': '',
            None: '',
        }

        for raw_url, expected_formatted_url in test_cases.items():
            formatter = EmbeddedYouTubeUrl(raw_url)
            self.assertEqual(
                str(formatter),
                expected_formatted_url,
                f"Failed to format URL: {raw_url}"
            )
