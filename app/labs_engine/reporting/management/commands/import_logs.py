"""Django management command to import nginx log files."""

from django.core.management.base import BaseCommand, CommandError
from pathlib import Path

from labs_engine.reporting.nginx_logs import import_nginx_log, LOG_TYPE


class Command(BaseCommand):
    """Import nginx log files into the database."""

    help = 'Import nginx log files (lab visits or tool usage)'

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            'path',
            type=str,
            help='Path to the log file to import',
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['visit', 'tool'],
            required=True,
            help=(
                'Type of log file '
                '(visit for welcome logs, tool for tool usage logs)'
            ),
        )

    def handle(self, *args, **options):
        """Execute the command."""
        log_path = Path(options['path'])
        log_type_arg = options['type']

        # Validate file exists
        if not log_path.exists():
            raise CommandError(f'File not found: {log_path}')

        if not log_path.is_file():
            raise CommandError(f'Path is not a file: {log_path}')

        # Map command arg to LOG_TYPE
        log_type_map = {
            'visit': LOG_TYPE.WELCOME,
            'tool': LOG_TYPE.TOOL,
        }
        log_type = log_type_map[log_type_arg]

        self.stdout.write(f'Importing {log_type_arg} logs from: {log_path}')

        # Open and process the file
        try:
            with open(log_path, 'r', encoding='utf-8') as log_file:
                result = import_nginx_log(log_file, log_type)

            # Display results
            self.stdout.write(self.style.SUCCESS('\n' + result['message']))
            self.stdout.write(f"Status: {result['status']}")
            self.stdout.write(f"Lines processed: {result['lines_processed']}")

            if log_type == LOG_TYPE.WELCOME:
                visits = result['visits_created']
                self.stdout.write(f"Visits created: {visits}")
            elif log_type == LOG_TYPE.TOOL:
                tool_usages = result['tool_usages_created']
                self.stdout.write(f"Tool usages created: {tool_usages}")

            if result.get('total_errors', 0) > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"\nTotal errors: {result['total_errors']}"
                    )
                )
                self.stdout.write('First 10 errors:')
                for error in result.get('errors', []):
                    self.stdout.write(
                        f"  Line {error['line']}: {error['error']}"
                    )

        except Exception as e:
            raise CommandError(f'Error processing log file: {str(e)}')
