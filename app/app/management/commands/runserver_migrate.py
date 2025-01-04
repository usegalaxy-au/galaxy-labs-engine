from django.core.management.commands.runserver import (
    Command as RunserverCommand,
)
from django.core.management import call_command


class Command(RunserverCommand):
    def handle(self, *args, **options):
        self.stdout.write("Applying migrations...")
        call_command("migrate")
        self.stdout.write("Migrations applied successfully.")
        super().handle(*args, **options)
