import warnings
from django.core.management.commands.runserver import (
    Command as RunserverCommand,
)
from django.core.management import call_command


class Command(RunserverCommand):
    def handle(self, *args, **options):
        warnings.filterwarnings(
            "ignore",
            message="apply the migration",
        )
        call_command("collectstatic", "--noinput")
        super().handle(*args, **options)
