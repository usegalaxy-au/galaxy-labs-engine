"""Data for test setup.

TODO: this needs to be updated for new exported lab pages.
"""

import os
from pathlib import Path

CONTENT_DIRS = (
    Path(__file__).parent.parent.parent
    / 'static/labs/content/docs',
    Path(__file__).parent.parent.parent
    / 'static/labs/content/simple',
)
MOCK_LAB_BASE_URL = 'http://mockserver'


# Collect all the files from the lab's content dir and assign each
# file's content to a URL in the mock server.
MOCK_REQUESTS = {}
for content_dir in CONTENT_DIRS:
    if not content_dir.exists():
        raise FileNotFoundError(f"Content directory not found: {content_dir}")
    for root, dirs, files in os.walk(content_dir):
        for file in files:
            filepath = os.path.join(root, file)
            with open(filepath) as f:
                static_path = 'static/' + filepath.split('/static/', 1)[1]
                url = f'{MOCK_LAB_BASE_URL}/{static_path}'
                try:
                    MOCK_REQUESTS[url] = f.read()
                except UnicodeDecodeError:
                    # Binary files not required for testing
                    pass
