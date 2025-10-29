"""Validation functions for settings and environment.

These should provide useful feedback to site administrators.
"""

import os


def env():
    """Validate environment variables."""
    validate_hostname()


def validate_hostname():
    """Ensure that hostname format is valid for application."""
    hostname = os.environ.get('HOSTNAME')
    if not hostname:
        raise ValueError(
            "HOSTNAME must be defined in the applcation .env file."
            " Please see .env.sample for example variables.\n\n"
            "# Your site domain. Do not include schema or slashes.\n"
            "HOSTNAME=mysite.com"
        )
    if hostname.startswith('http'):
        raise ValueError(
            "HOSTNAME should not include a schema."
            " Please see .env.sample for example variables.\n\n"
            f"Provided HOSTNAME: {hostname}\n"
            f"Example HOSTNAME:  mysite.com"
        )
    if '/' in hostname:
        raise ValueError(
            "HOSTNAME should not include slashes."
            " Please see .env.sample for example variables.\n\n"
            f"Provided HOSTNAME: {hostname}\n"
            f"Example HOSTNAME:  mysite.com"
        )
