from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.db import models
from datetime import timedelta, datetime
from django.utils import timezone

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


def get_usage_data(request):
    """
    API endpoint to fetch usage data for charts.

    Query parameters:
        - metric: 'visits' or 'tools' (default: 'visits')
        - days: number of days to look back (optional)
        - start_date: custom start date (optional, YYYY-MM-DD)
        - end_date: custom end date (optional, YYYY-MM-DD)
        - lab: filter by lab name (optional, 'all' for all labs)
    """
    metric = request.GET.get('metric', 'visits')
    lab_filter = request.GET.get('lab', 'all')

    # Handle custom date range
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        # Parse custom date range
        start_date = timezone.make_aware(
            datetime.strptime(start_date_str, '%Y-%m-%d')
        )
        end_date = timezone.make_aware(
            datetime.strptime(end_date_str, '%Y-%m-%d')
        )
        end_date = end_date.replace(hour=23, minute=59, second=59)
    else:
        # Use days parameter
        days = int(request.GET.get('days', 90))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

    if metric == 'visits':
        # Query LabVisit data
        queryset = LabVisit.objects.filter(
            datetime__gte=start_date,
            datetime__lte=end_date
        )
        if lab_filter and lab_filter != 'all':
            queryset = queryset.filter(lab_name=lab_filter)

        data = (
            queryset
            .annotate(date=TruncDate('datetime'))
            .values('lab_name', 'date')
            .annotate(count=Count('id'))
            .order_by('date', 'lab_name')
        )

        # Transform data for lab-based grouping
        lab_data = {}
        for item in data:
            lab = item['lab_name']
            if lab not in lab_data:
                lab_data[lab] = {'dates': [], 'counts': []}
            lab_data[lab]['dates'].append(item['date'].isoformat())
            lab_data[lab]['counts'].append(item['count'])

        # Format for Plotly
        traces = []
        for lab_name, values in lab_data.items():
            traces.append({
                'name': lab_name,
                'x': values['dates'],
                'y': values['counts'],
                'type': 'scatter',
                'mode': 'lines+markers',
            })

    elif metric == 'tools':
        # Query ToolUsage data - group by tool_id
        queryset = ToolUsage.objects.filter(
            datetime__gte=start_date,
            datetime__lte=end_date
        )
        if lab_filter and lab_filter != 'all':
            queryset = queryset.filter(lab_name=lab_filter)

        data = (
            queryset
            .annotate(date=TruncDate('datetime'))
            .values('tool_id', 'date')
            .annotate(count=Count('id'))
            .order_by('date', 'tool_id')
        )

        # Transform data for tool-based grouping
        tool_data = {}
        for item in data:
            tool = item['tool_id']
            if tool not in tool_data:
                tool_data[tool] = {'dates': [], 'counts': []}
            tool_data[tool]['dates'].append(item['date'].isoformat())
            tool_data[tool]['counts'].append(item['count'])

        # Format for Plotly - show tool names
        traces = []
        for tool_id, values in tool_data.items():
            # Extract tool name from full ID for better readability
            tool_name = tool_id.split('/')[-1] if '/' in tool_id else tool_id
            traces.append({
                'name': tool_name,
                'x': values['dates'],
                'y': values['counts'],
                'type': 'scatter',
                'mode': 'lines+markers',
                'hovertext': tool_id,  # Show full ID on hover
            })
    else:
        return JsonResponse({'error': 'Invalid metric parameter'}, status=400)

    return JsonResponse({
        'traces': traces,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
    })
