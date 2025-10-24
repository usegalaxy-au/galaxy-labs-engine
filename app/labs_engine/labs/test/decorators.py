"""Decorator utilities for wrapping test methods."""

import logging


def suppress_request_warnings(func):
    """
    If we need to test for 404s or 405s this decorator can prevent the
    request class from throwing warnings.
    """
    def wrapper(*args, **kwargs):
        # raise logging level to ERROR
        logger = logging.getLogger('django.request')
        previous_logging_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        # trigger original function that would throw warning
        func(*args, **kwargs)

        # lower logging level back to previous
        logger.setLevel(previous_logging_level)

    return wrapper
