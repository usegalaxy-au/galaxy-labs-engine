"""Utilities for sending mail."""

import logging
import traceback

SEND_MAIL_RETRIES = 3

logger = logging.getLogger('django')


def retry_send_mail(mail):
    """Attempt sending email with error log fallback."""
    tries = 0
    while True:
        try:
            mail.send()
        except Exception:
            logger.warning(f"Send mail error - attempt {tries}")
            tries += 1
            if tries < SEND_MAIL_RETRIES:
                continue
            logger.error(
                "Error sending mail. The user did not receive an error.\n"
                + traceback.format_exc()
                + f"\n\nMail content:\n\n{mail.body}"
            )
