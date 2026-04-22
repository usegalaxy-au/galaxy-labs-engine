from django.shortcuts import render
from django.db import models

from .models import LabVisit, ToolUsage


def dashboard(request):
    """Render the reporting dashboard page."""
    # Get data ranges for subtitle
    visit_range = LabVisit.objects.aggregate(
        min_date=models.Min('datetime'),
        max_date=models.Max('datetime'),
    )
    tool_range = ToolUsage.objects.aggregate(
        min_date=models.Min('datetime'),
        max_date=models.Max('datetime'),
    )

    # Get list of labs for dropdown
    labs = list(
        LabVisit.objects.values_list('lab_name', flat=True)
        .distinct()
        .order_by('lab_name')
    )

    context = {
        'visit_range': visit_range,
        'tool_range': tool_range,
        'labs': labs,
    }
    return render(request, 'reporting/dashboard.html', context)
