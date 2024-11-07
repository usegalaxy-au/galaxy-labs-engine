import requests_mock
from pathlib import Path

from .lab_export import ExportLabContext
from .test.data import (
    MOCK_REQUESTS,
    MOCK_LAB_BASE_URL,
)
from app.test import TestCase

TEST_DATA_DIR = Path(__file__).parent / 'test/data'
TEST_LAB_NAME = 'Lab Docs'
TEST_LAB_LAB_NAME = 'Galaxy Lab Pages'.upper()
TEST_LAB_NATIONALITY = 'Antarctican'
TEST_LAB_GALAXY_BASE_URL = 'https://galaxy-antarctica.org'
TEST_LAB_SECTION_TEXT = 'Example section'
TEST_LAB_ACCORDION_TEXT = (
    'Report statistics from sequencing reads',
    'Assemble Nanopore long reads.',
)
TEST_LAB_CONTENT_URL = f'{MOCK_LAB_BASE_URL}/static/labs/content/docs/base.yml'
TEST_LAB_URL = f'/?content_root={TEST_LAB_CONTENT_URL}'


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
        self.assertEqual(response.status_code, 200)
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
