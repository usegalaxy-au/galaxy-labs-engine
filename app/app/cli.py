"""Command line interface for launching a development server.

This is intended to be used for rendering Lab pages in development.
"""

import os
import sys
from pathlib import Path


def main():
    """CLI entry point for running the development server."""

    if len(sys.argv) == 1:
        print(
            "Please choose from one of the available subcommands:\n\n"
            "  serve    Serve local Lab content as a web page\n"
        )
        sys.exit(1)

    try:
        import django
        from django.core.management import call_command
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Make sure it's installed and "
            "available on your PYTHONPATH environment variable."
        ) from exc

    os.environ["DJANGO_SETTINGS_MODULE"] = "app.settings.cli"
    set_required_env_vars()
    django.setup()

    if sys.argv[1] == "serve":
        BASE_DIR = Path(__file__).resolve().parent.parent
        os.chdir(BASE_DIR)
        sys.path.insert(0, str(BASE_DIR))
        if len(sys.argv) > 2:
            os.environ["LAB_CONTENT_ENTRYPOINT"] = sys.argv[2]
        call_command("createcachetable", verbosity=0)
        call_command(
            "migrate", interactive=False, run_syncdb=True, verbosity=0)
        call_command("collectstatic", interactive=False, verbosity=0)
        call_command("runserver", "127.0.0.1:8000", verbosity=0)
    else:
        print(f"Unknown command: {sys.argv[1]}")


def set_required_env_vars():
    """Set required environment variables for the CLI."""
    os.environ.setdefault("LAB_CONTENT_ROOT", os.getcwd())
    os.environ.setdefault("HOSTNAME", "localhost:8000")
    os.environ.setdefault("MAIL_HOSTNAME", "localhost")
    os.environ.setdefault("MAIL_SMTP_PORT", "22")
    os.environ.setdefault("MAIL_FROM_ADDRESS", "labs@example.com")
    os.environ.setdefault("MAIL_TO_ADDRESS", "admin@example.com")


if __name__ == "__main__":
    main()
