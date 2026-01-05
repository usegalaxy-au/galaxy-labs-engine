"""Process Nginx log files."""

from .models import LabVisit, ToolUsage

WELCOME_LOG_STRING = '/static/welcome'


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


def parse_nginx_log(log_file, log_type):
    if log_type == LOG_TYPE.WELCOME:
        return parse_welcome_log(log_file)
    elif log_type == LOG_TYPE.TOOL:
        return parse_tool_log(log_file)


def parse_welcome_log(log_file):
    """
    Import and process an Nginx log file.

    Args:
        log_file: Django UploadedFile instance containing the log data

    Returns:
        dict: Processing results containing statistics and status
    """
    lines_processed = 0
    visits_created = 0
    errors = []

    for line in log_file:
        # Decode bytes to string if necessary
        if isinstance(line, bytes):
            line = line.decode('utf-8')

        lines_processed += 1

        # Skip empty lines
        if not line.strip():
            continue

        if WELCOME_LOG_STRING not in line:
            continue

        try:
            # Parse the log line and create a LabVisit instance
            visit = LabVisit.from_nginx_log(line)

            # Save if parsing was successful
            if visit:
                visit.save()
                visits_created += 1

        except Exception as e:
            errors.append({
                'line': lines_processed,
                'error': str(e),
            })

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


def parse_tool_log(log_file):
    """
    Import and process an Nginx tool usage log file.

    Args:
        log_file: Django UploadedFile instance containing the log data

    Returns:
        dict: Processing results containing statistics and status
    """
    lines_processed = 0
    tool_usages_created = 0
    errors = []

    for line in log_file:
        # Decode bytes to string if necessary
        if isinstance(line, bytes):
            line = line.decode('utf-8')

        lines_processed += 1

        # Skip empty lines
        if not line.strip():
            continue

        # Skip lines that don't contain tool_id in the referer
        if 'tool_id=' not in line:
            continue

        try:
            # Parse the log line and create a ToolUsage instance
            tool_usage = ToolUsage.from_nginx_log(line)

            # Save if parsing was successful
            if tool_usage:
                tool_usage.save()
                tool_usages_created += 1

        except Exception as e:
            errors.append({
                'line': lines_processed,
                'error': str(e),
            })

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


def import_nginx_log(log_file, log_type):
    """
    Import and process an Nginx log file based on type.

    Args:
        log_file: Django UploadedFile instance containing the log data
        log_type: Type of log file (from LOG_TYPE constants)

    Returns:
        dict: Processing results containing statistics and status
    """
    return parse_nginx_log(log_file, log_type)
