"""Custom logging handlers."""

import os
from logging import StreamHandler
from utils import slack

REQUIRED_KEYS = ('SLACK_API_KEY', 'SLACK_CHANNEL_ID')


class SlackHandler(StreamHandler):
    """Post log messages to Slack."""

    def __init__(self):
        """Configure Slack API connection."""
        super().__init__()
        for key in REQUIRED_KEYS:
            if not os.environ.get(key):
                return print(
                    f"Missing environment variable '{key}'"
                    " - Slack notifications are disabled. ")

    def emit(self, record):
        """Log a message to Slack."""
        slack.post(self.format(record))
