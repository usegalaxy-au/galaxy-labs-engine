"""Utility functions for interacting with paths and filesystem."""

from pathlib import Path


def ensure_dir(path):
    """Ensure given dirs exist."""
    path = Path(path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    return path
