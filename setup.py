from setuptools import setup, find_packages

setup(
    name="galaxy-labs-engine",
    version="1.0.0",
    packages=find_packages(where='app'),
    package_dir={'': 'app'},
    include_package_data=True,
    install_requires=[
        "django>=4.0",  # Add any dependencies here
        "django>=5.0",
        "pyyaml>=6.0",
        "pydantic>=2.0",
        "markdown2>=2.0",
        "beautifulsoup4>=4.0",
        "requests>=2.0",
        "django-crispy-forms>=2.0",
        "crispy-bootstrap5>=2024.0",
    ],
    entry_points={
        "console_scripts": [
            "labs-engine=app.cli:main",
        ],
    },
)
