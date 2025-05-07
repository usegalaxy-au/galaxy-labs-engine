"""Models for interacting with database."""

from django.db import models
from django.contrib.auth.models import AbstractUser

from .managers import CustomUserManager


class User(AbstractUser):
    """Staff user for managing site content."""

    username = None
    email = models.EmailField(unique=True, max_length=255)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    objects = CustomUserManager()

    def __str__(self):
        """Return a string representation of self."""
        return f"{self.first_name} {self.last_name} <{self.email}>"


class CachedLab(models.Model):
    """Track usage of a cached lab page."""
    key = models.CharField(max_length=32, primary_key=True, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    url = models.URLField(max_length=255)

    def __str__(self):
        """Return a string representation of self."""
        return f"CachedLab({self.url})"
