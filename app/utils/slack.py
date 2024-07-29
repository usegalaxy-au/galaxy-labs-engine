"""Slack notifications for log handling."""

import os
import requests

SLACK_URL = "https://slack.com/api/chat.postMessage"


def post(message):
    """Post a message to Slack."""
    key = os.environ.get("SLACK_API_KEY")
    user_id = os.environ.get("SLACK_MENTION_USER_ID")
    channel_id = os.environ.get("SLACK_CHANNEL_ID")

    if key is None:
        return
    if user_id:
        message = f'<@{user_id}> {message}'

    requests.post(
        SLACK_URL,
        json={
            "text": message,
            "channel": channel_id,
        },
        headers={
            "Authorization": f'Bearer {key}',
        },
    )
