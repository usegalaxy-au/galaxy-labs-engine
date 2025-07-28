import requests_mock
from pathlib import Path
from unittest.mock import Mock, patch

from .lab_export import ExportLabContext
from .audit import (
    extract_tool_links,
    check_tool_exists,
    audit_tools_concurrent,
    perform_template_audit,
)
from .test.data import (
    MOCK_REQUESTS,
    MOCK_LAB_BASE_URL,
)
from app.test import TestCase

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

    @patch('labs.audit.GalaxyInstance')
    def test_check_tool_exists_with_valid_tool(self, mock_galaxy_instance):
        """Test check_tool_exists with a valid tool."""
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

    @patch('labs.audit.GalaxyInstance')
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

    @patch('labs.audit.GalaxyInstance')
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

    @patch('labs.audit.check_tool_exists')
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

    @patch('labs.audit.render_to_string')
    def test_perform_template_audit_without_audit_param(self, mock_render):
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
        mock_render.assert_not_called()

    @patch('labs.audit.render_to_string')
    @patch('labs.audit.audit_tools_concurrent')
    def test_perform_template_audit_with_audit_param(
        self,
        mock_audit_tools,
        mock_render
    ):
        """Test perform_template_audit when audit param is present."""
        request = Mock()
        request.GET = {'audit': '1'}
        context = {'galaxy_base_url': TEST_GALAXY_SERVER_URL}
        template_str = self.html_with_tools

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
        mock_render.return_value = 'rendered_template'

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

        # Check that template is re-rendered
        self.assertEqual(result_template, 'rendered_template')
        mock_render.assert_called_once()

    @patch('labs.audit.render_to_string')
    def test_perform_template_audit_with_no_galaxy_url(self, mock_render):
        """Test perform_template_audit when galaxy_base_url is missing."""
        request = Mock()
        request.GET = {'audit': '1'}
        context = {}  # No galaxy_base_url
        template_str = self.html_with_tools

        mock_render.return_value = 'rendered_template'

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
        self.assertEqual(result_template, 'rendered_template')
