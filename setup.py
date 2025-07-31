from pathlib import Path
from setuptools import setup, find_packages

version = (Path(__file__).parent / "VERSION").read_text().strip()

setup(
    name="galaxy-labs-engine",
    version=version,
    packages=find_packages(where='app'),
    package_dir={'': 'app'},
    include_package_data=True,
    install_requires=[
        "beautifulsoup4",
        "bioblend==1.*",
        "crispy-bootstrap5==2024.*",
        "django==5.*",
        "django-crispy-forms==2.*",
        "django_light",
        "gunicorn==22.*",
        "markdown2==2.*",
        "pydantic==2.*",
        "python-dotenv==0.*",
        "pyyaml==6.*",
        "requests==2.*",
        "requests_mock==1.*",
        "sentry-sdk==2.*",
    ],
    entry_points={
        "console_scripts": [
            "labs-engine=app.cli:main",
        ],
    },
    python_requires=">=3.10",
)
