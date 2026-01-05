from django.contrib import admin

from .models import APIToken, LabVisit, ToolUsage


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


@admin.register(LabVisit)
class LabVisitAdmin(admin.ModelAdmin):
    """Admin interface for lab visits."""

    list_display = ['lab_name', 'datetime']
    list_filter = ['lab_name', 'datetime']
    search_fields = ['lab_name']
    readonly_fields = ['lab_name', 'datetime']
    date_hierarchy = 'datetime'

    def has_add_permission(self, request):
        """Disable manual creation - only via log import."""
        return False

    def has_change_permission(self, request, obj=None):
        """Make visits read-only."""
        return False


@admin.register(ToolUsage)
class ToolUsageAdmin(admin.ModelAdmin):
    """Admin interface for tool usage records."""

    list_display = ['tool_id', 'lab_name', 'datetime']
    list_filter = ['lab_name', 'datetime']
    search_fields = ['tool_id', 'lab_name']
    readonly_fields = ['tool_id', 'lab_name', 'datetime']
    date_hierarchy = 'datetime'

    def has_add_permission(self, request):
        """Disable manual creation - only via log import."""
        return False

    def has_change_permission(self, request, obj=None):
        """Make tool usage records read-only."""
        return False
