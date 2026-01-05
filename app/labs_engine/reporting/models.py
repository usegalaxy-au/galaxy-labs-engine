import re
import secrets
from datetime import datetime
from urllib.parse import urlparse

from django.db import models
from django.utils import timezone


class APIToken(models.Model):
    """API authentication token for external services."""
    name = models.CharField(
        max_length=255,
        help_text="Descriptive name for this token",
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        help_text="The API token",
    )
    created = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive tokens cannot be used for authentication",
    )

    def __str__(self):
        """Return a string representation of self."""
        return f"APIToken({self.name})"

    def save(self, *args, **kwargs):
        """Generate token on creation."""
        if not self.token:
            self.token = secrets.token_urlsafe(48)
        super().save(*args, **kwargs)

    class Meta:
        """Model metadata."""
        verbose_name = "API Token"
        verbose_name_plural = "API Tokens"


class LabVisit(models.Model):
    """Record of a visit to a lab report."""

    lab_name = models.CharField(
        max_length=255,
        help_text="Name of the lab visited",
    )
    datetime = models.DateTimeField(
        help_text="Timestamp of the visit",
    )

    def __str__(self):
        """Return a string representation of self."""
        return f"LabVisit({self.lab_name} at {self.datetime})"

    class Meta:
        """Model metadata."""
        verbose_name = "Lab Visit"
        verbose_name_plural = "Lab Visits"
        ordering = ['-datetime']

    @classmethod
    def from_nginx_log(cls, log_entry):
        """
        Create a LabVisit instance from an Nginx log line.

        Example log format:
        116.179.33.78 - - [30/Dec/2025:13:07:59 +0000] "GET ..." 200 592
        "https://proteomics.usegalaxy.org.au/" "Mozilla/5.0..."

        Args:
            log_entry: String containing a single nginx log line

        Returns:
            LabVisit instance or None if parsing fails
        """
        pattern = (
            r'(?P<ip>[\d.]+) - - '
            r'\[(?P<datetime>[^\]]+)\] '
            r'"(?P<method>\w+) (?P<path>[^\s]+) HTTP/[\d.]+" '
            r'(?P<status>\d+) (?P<size>\d+) '
            r'"(?P<referer>[^"]*)" '
            r'"(?P<user_agent>[^"]*)"'
        )

        match = re.match(pattern, log_entry.strip())
        if not match:
            return None

        # Extract the referer URL to get the lab name
        referer = match.group('referer')
        if not referer or referer == '-':
            return None

        # Parse the lab name from the referer URL
        # Example: https://proteomics.usegalaxy.org.au/ -> proteomics
        parsed_url = urlparse(referer)
        hostname = parsed_url.hostname
        if not hostname:
            return None

        # Extract subdomain (lab name) from hostname
        # Example: proteomics.usegalaxy.org.au -> proteomics
        parts = hostname.split('.')
        if len(parts) < 3:
            return None
        lab_name = parts[0]

        # Parse the timestamp
        # Format: 30/Dec/2025:13:07:59 +0000
        timestamp_str = match.group('datetime')
        dt = datetime.strptime(timestamp_str, '%d/%b/%Y:%H:%M:%S %z')

        # Convert to Django timezone-aware datetime
        dt_aware = timezone.make_aware(
            dt.replace(tzinfo=None),
            timezone.get_current_timezone()
        )

        return cls(
            lab_name=lab_name,
            datetime=dt_aware,
        )


class ToolUsage(models.Model):
    """Record of a tool being used in a lab."""

    lab_name = models.CharField(
        max_length=255,
        help_text="Name of the lab where tool was used",
    )
    tool_id = models.CharField(
        max_length=512,
        help_text="Full tool ID from Galaxy",
    )
    datetime = models.DateTimeField(
        help_text="Timestamp of the tool usage",
    )

    def __str__(self):
        """Return a string representation of self."""
        return f"ToolUsage({self.tool_id} in {self.lab_name})"

    class Meta:
        """Model metadata."""
        verbose_name = "Tool Usage"
        verbose_name_plural = "Tool Usages"
        ordering = ['-datetime']

    @classmethod
    def from_nginx_log(cls, log_entry):
        """
        Create a ToolUsage instance from an Nginx log line.

        Example log format:
        101.115.128.163 - - [04/Jan/2026:07:05:12 +0000] "POST ..." 200
        "https://genome.usegalaxy.org.au/?tool_id=..." "Mozilla/5.0..."

        Args:
            log_entry: String containing a single nginx log line

        Returns:
            ToolUsage instance or None if parsing fails
        """
        from urllib.parse import parse_qs

        pattern = (
            r'(?P<ip>[\d.]+) - - '
            r'\[(?P<datetime>[^\]]+)\] '
            r'"(?P<method>\w+) (?P<path>[^\s]+) HTTP/[\d.]+" '
            r'(?P<status>\d+) (?P<size>\d+) '
            r'"(?P<referer>[^"]*)" '
            r'"(?P<user_agent>[^"]*)"'
        )

        match = re.match(pattern, log_entry.strip())
        if not match:
            return None

        # Extract the referer URL to get the lab name and tool_id
        referer = match.group('referer')
        if not referer or referer == '-':
            return None

        # Parse the URL
        parsed_url = urlparse(referer)
        hostname = parsed_url.hostname
        if not hostname:
            return None

        # Extract subdomain (lab name) from hostname
        # Example: genome.usegalaxy.org.au -> genome
        parts = hostname.split('.')
        if len(parts) < 3:
            return None
        lab_name = parts[0]

        # Extract tool_id from query parameters
        query_params = parse_qs(parsed_url.query)
        tool_id_list = query_params.get('tool_id', [])
        if not tool_id_list:
            return None
        tool_id = tool_id_list[0]

        # Parse the timestamp
        # Format: 04/Jan/2026:07:05:12 +0000
        timestamp_str = match.group('datetime')
        dt = datetime.strptime(timestamp_str, '%d/%b/%Y:%H:%M:%S %z')

        # Convert to Django timezone-aware datetime
        dt_aware = timezone.make_aware(
            dt.replace(tzinfo=None),
            timezone.get_current_timezone()
        )

        return cls(
            lab_name=lab_name,
            tool_id=tool_id,
            datetime=dt_aware,
        )
