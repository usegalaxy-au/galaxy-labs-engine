"""Logging configuration."""

import re
import os
from django.template.base import VariableDoesNotExist


EXCLUDE_EXCEPTIONS = [
    VariableDoesNotExist,
]

# Lowercase only
EXCLUDE_PATTERNS = [
    r'invalid http_host header',
    r"Field '.+' expected an? \w+ but got '.+'"
]


log_levels = {
    'console': os.getenv('LOG_LEVEL_CONSOLE', 'INFO'),
    'cache': os.getenv('LOG_LEVEL_CACHE', 'INFO'),
}


def filter_exc_by_type(record):
    """Exclude blacklisted exception types."""
    if record.exc_info:
        exc = record.exc_info[1]
        for excluded in EXCLUDE_EXCEPTIONS:
            if isinstance(exc, excluded):
                return False
    return True


def filter_exc_by_pattern(record):
    """Exclude exceptions based on string content."""
    for pattern in EXCLUDE_PATTERNS:
        if re.match(pattern, record.msg.lower()):
            return False
    return True


def configure_logging(log_root):
    """Return logging configuration."""
    return {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'verbose': {
                'format': '{levelname} | {asctime} | {module}: {message}',
                'style': '{',
            },
        },
        'filters': {
            'filter_exc_by_type': {
                '()': 'django.utils.log.CallbackFilter',
                'callback': filter_exc_by_type,
            },
            'filter_exc_by_pattern': {
                '()': 'django.utils.log.CallbackFilter',
                'callback': filter_exc_by_pattern,
            },
        },
        'handlers': {
            'debug_file': {
                'delay': True,
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'maxBytes': 1000000,  # 1MB ~ 20k rows
                'backupCount': 5,
                'filename': log_root / 'debug.log',
                'formatter': 'verbose',
                'filters': ['filter_exc_by_type'],
            },
            'main_file': {
                'delay': True,
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'maxBytes': 1000000,  # 1MB ~ 20k rows
                'backupCount': 5,
                'filename': log_root / 'main.log',
                'formatter': 'verbose',
            },
            'cache_file': {
                'delay': True,
                'level': log_levels.get('cache', 'INFO'),
                'class': 'logging.handlers.RotatingFileHandler',
                'maxBytes': 1000000,  # 1MB ~ 20k rows
                'backupCount': 1,
                'filename': log_root / 'cache.log',
                'formatter': 'verbose',
            },
            'error_file': {
                'delay': True,
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'maxBytes': 1000000,  # 1MB ~ 20k rows
                'backupCount': 5,
                'filename': log_root / 'error.log',
                'formatter': 'verbose',
            },
            'error_mail': {
                'level': 'ERROR',
                'class': 'django.utils.log.AdminEmailHandler',
                'formatter': 'verbose',
                'filters': ['filter_exc_by_pattern'],
            },
            'error_slack': {
                'level': 'ERROR',
                'class': 'app.settings.log.handlers.SlackHandler',
                'filters': ['filter_exc_by_pattern'],
            },
            'debug_slack': {  # For debugging logging only
                'level': 'DEBUG',
                'class': 'app.settings.log.handlers.SlackHandler',
                'filters': ['filter_exc_by_pattern'],
            },
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_levels.get('console', 'INFO'),
                'formatter': 'verbose',
            },
        },
        'loggers': {
            'django': {
                'handlers': [
                    'debug_file',
                    'main_file',
                    'error_file',
                    # 'error_mail',
                    'error_slack',
                    'console',
                ],
                'level': 'DEBUG',
                'propagate': True,
            },
            'django.cache': {
                'handlers': [
                    'cache_file',
                    'console',
                ],
                'level': 'DEBUG',
                'propagate': False,
            },
            'django.utils.autoreload': {
                'level': 'WARNING',  # This logger is way too noisy on DEBUG
            }
        },
    }
