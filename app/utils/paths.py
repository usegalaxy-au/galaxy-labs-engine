"""Utility functions for interacting with paths and filesystem."""

import os


def ensure_dir(path):
    """Ensure given dirs exist."""
    if not os.path.exists(path):
        os.makedirs(path)
    return path
