from django.contrib import admin

# Register your models here.
from .models import APIToken


@admin.register(APIToken)
class APITokenAdmin(admin.ModelAdmin):
    """Admin interface for API tokens."""

    list_display = ['name', 'created', 'last_used', 'is_active']
    list_filter = ['is_active', 'created']
    search_fields = ['name']
    readonly_fields = ['token', 'created', 'last_used']

    fieldsets = (
        (None, {
            'fields': ('name', 'is_active'),
        }),
        ('Token Information', {
            'fields': ('token', 'created', 'last_used'),
            'description': (
                'The token will be automatically generated when you save. '
                'Make sure to copy it - it cannot be retrieved later.'
            ),
        }),
    )
