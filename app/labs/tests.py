import requests_mock
from pathlib import Path

from .lab_export import ExportSubsiteContext
from .test.data import (
    MOCK_REQUESTS,
    MOCK_LAB_BASE_URL,
)
from app.test import TestCase

TEST_DATA_DIR = Path(__file__).parent / 'test/data'
TEST_LAB_NAME = 'Antarctica'
TEST_LAB_LAB_NAME = 'Galaxy Lab Pages'.upper()
TEST_LAB_NATIONALITY = 'Antarctican'
TEST_LAB_GALAXY_BASE_URL = 'https://galaxy-antarctica.org'
TEST_LAB_SECTION_TEXT = 'Example section'
TEST_LAB_ACCORDION_TEXT = (
    'Report statistics from sequencing reads',
    'Assemble Nanopore long reads.',
)
TEST_LAB_CONTENT_URL = f'{MOCK_LAB_BASE_URL}/static/home/labs/docs/main.yml'
TEST_LAB_URL = f'/lab/export?content_root={TEST_LAB_CONTENT_URL}'


def test_lab_url_for(lab):
    """Return the URL for the given lab name."""
    return TEST_LAB_URL.replace('docs', lab)


class LabExportTestCase(TestCase):
    """Test exported lab site building functionality."""

    @requests_mock.Mocker()
    def setUp(self, mock_request):
        for url, text in MOCK_REQUESTS.items():
            mock_request.get(url, text=text, status_code=200)
        self.context = ExportSubsiteContext(TEST_LAB_CONTENT_URL)

    @requests_mock.Mocker()
    def test_exported_lab_docs(self, mock_request):
        """Mock requests to localhost."""
        for url, text in MOCK_REQUESTS.items():
            mock_request.get(url, text=text, status_code=200)
        response = self.client.get(TEST_LAB_URL)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, TEST_LAB_NAME)
        self.assertContains(response, TEST_LAB_LAB_NAME)
        self.assertContains(response, TEST_LAB_GALAXY_BASE_URL)
        self.assertContains(response, TEST_LAB_SECTION_TEXT)
        for text in TEST_LAB_ACCORDION_TEXT:
            self.assertContains(response, text)

    @requests_mock.Mocker()
    def test_genome_lab(self, mock_request):
        """Mock requests to localhost."""
        for url, text in MOCK_REQUESTS.items():
            mock_request.get(url, text=text, status_code=200)
        response = self.client.get(test_lab_url_for('genome'))
        self.assertEqual(response.status_code, 200)

    @requests_mock.Mocker()
    def test_proteomics_lab(self, mock_request):
        """Mock requests to localhost."""
        for url, text in MOCK_REQUESTS.items():
            mock_request.get(url, text=text, status_code=200)
        response = self.client.get(test_lab_url_for('proteomics'))
        self.assertEqual(response.status_code, 200)

    def test_it_can_make_raw_url(self):
        self.assertEqual(
            self.context._make_raw('https://github.com/usegalaxy-au/'
                                   'galaxy-media-site/blob/dev/README.md'),
            'https://raw.githubusercontent.com/usegalaxy-au/'
            'galaxy-media-site/dev/README.md')

    def test_it_can_filter_sections_by_root_domain(self):
        root_domain = 'antarctica.org'
        self.context['root_domain'] = root_domain
        self.context['sections'] = [
            {'id': 'section1'},
            {
                'id': 'section2',
                'exclude_from': [root_domain],
            },
            {
                'id': 'section3',
                'content': [
                    {
                        'id': 'item1',
                    },
                    {
                        'id': 'item2',
                        'exclude_from': [root_domain],
                    },
                    {
                        'id': 'item3',
                        'exclude_from': ['other.domain.com'],
                    },
                    {
                        'id': 'item4',
                        'exclude_from': [root_domain, 'other.domain.com'],
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
