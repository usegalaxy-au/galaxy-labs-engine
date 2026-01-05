"""Process Nginx log files."""

from .models import LabVisit, ToolUsage

WELCOME_LOG_STRING = '/static/welcome'
IGNORE_LOG_LINES = (
    'www.usegalaxy',
    'galaxy.usegalaxy',
    'AhrefsBot',
)


class LOG_TYPE:

    WELCOME = 'nginx_welcome'
    TOOL = 'nginx_tool'

    _TYPES = (
        WELCOME,
        TOOL,
    )

    @classmethod
    def from_string(cls, s):
        """Map string to log type constant."""
        sanitized = (
            s.strip().lower()
            if s and isinstance(s, str)
            else None
        )
        if sanitized in cls._TYPES:
            return sanitized
        return None


def import_nginx_log(log_file, log_type):
    if log_type == LOG_TYPE.WELCOME:
        return parse_welcome_log(log_file)
    elif log_type == LOG_TYPE.TOOL:
        return parse_tool_log(log_file)


def parse_welcome_log(log_file, batch_size=1000):
    """
    Import and process an Nginx log file.

    Args:
        log_file: Django UploadedFile instance containing the log data
        batch_size: Number of records to create in each bulk insert

    Returns:
        dict: Processing results containing statistics and status
    """
    lines_processed = 0
    visits_created = 0
    errors = []
    visits_batch = []

    for line in log_file:
        if isinstance(line, bytes):
            line = line.decode('utf-8')

        lines_processed += 1

        if WELCOME_LOG_STRING not in line or _ignore_line(line):
            continue

        try:
            visit = LabVisit.from_nginx_log(line)

            if visit:
                visits_batch.append(visit)

                if len(visits_batch) >= batch_size:
                    LabVisit.objects.bulk_create(visits_batch)
                    visits_created += len(visits_batch)
                    visits_batch = []

        except Exception as e:
            errors.append({
                'line': lines_processed,
                'error': str(e),
            })

    if visits_batch:
        LabVisit.objects.bulk_create(visits_batch)
        visits_created += len(visits_batch)

    return {
        'status': 'success' if not errors else 'partial',
        'lines_processed': lines_processed,
        'visits_created': visits_created,
        'errors': errors[:10],  # Limit to first 10 errors
        'total_errors': len(errors),
        'message': (
            f'Successfully processed {lines_processed} log lines, '
            f'created {visits_created} visit records'
        ),
    }


def parse_tool_log(log_file, batch_size=1000):
    """
    Import and process an Nginx tool usage log file.

    Args:
        log_file: Django UploadedFile instance containing the log data
        batch_size: Number of records to create in each bulk insert

    Returns:
        dict: Processing results containing statistics and status
    """
    lines_processed = 0
    tool_usages_created = 0
    errors = []
    tool_usages_batch = []

    for line in log_file:
        if isinstance(line, bytes):
            line = line.decode('utf-8')

        lines_processed += 1

        if _ignore_line(line) or 'tool_id=' not in line:
            continue

        try:
            tool_usage = ToolUsage.from_nginx_log(line)

            if tool_usage:
                tool_usages_batch.append(tool_usage)

                if len(tool_usages_batch) >= batch_size:
                    ToolUsage.objects.bulk_create(tool_usages_batch)
                    tool_usages_created += len(tool_usages_batch)
                    tool_usages_batch = []

        except Exception as e:
            errors.append({
                'line': lines_processed,
                'error': str(e),
            })

    if tool_usages_batch:
        ToolUsage.objects.bulk_create(tool_usages_batch)
        tool_usages_created += len(tool_usages_batch)

    return {
        'status': 'success' if not errors else 'partial',
        'lines_processed': lines_processed,
        'tool_usages_created': tool_usages_created,
        'errors': errors[:10],  # Limit to first 10 errors
        'total_errors': len(errors),
        'message': (
            f'Successfully processed {lines_processed} log lines, '
            f'created {tool_usages_created} tool usage records'
        ),
    }


def _ignore_line(line):
    """Determine if a log line should be ignored."""
    if not line.strip():
        return True
    for ignore_str in IGNORE_LOG_LINES:
        if ignore_str in line:
            return True
    return False
