import secrets

from django.db import models


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
        return f"LabVisit({self.lab_name} at {self.visit_time})"

    class Meta:
        """Model metadata."""
        verbose_name = "Lab Visit"
        verbose_name_plural = "Lab Visits"
        ordering = ['-datetime']

    @classmethod
    def from_nginx_log(cls, log_entry):
        """Create a LabVisit instance from an Nginx log line."""
        return cls(
            lab_name=name,
            datetime=timestamp,
        )
