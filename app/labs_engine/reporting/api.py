"""API endpoints."""

import csv
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta, datetime
from collections import defaultdict

from .auth import authenticated
from .nginx_logs import LOG_TYPE, import_nginx_log
from .models import LabVisit, ToolUsage


def generate_date_range(start_date, end_date):
    """
    Generate a list of dates between start_date and end_date (inclusive).

    Args:
        start_date: datetime object
        end_date: datetime object

    Returns:
        list of date objects
    """
    dates = []
    current = start_date.date() if hasattr(start_date, 'date') else start_date
    end = end_date.date() if hasattr(end_date, 'date') else end_date

    while current <= end:
        dates.append(current)
        current += timedelta(days=1)

    return dates


@csrf_exempt
@authenticated
def upload_logs(request):
    """Process Nginx logs uploaded from Galaxy server."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Only POST requests are allowed')

    if 'file' not in request.FILES:
        return JsonResponse(
            {'error': 'No file provided in request'},
            status=400,
        )

    uploaded_file = request.FILES['file']
    log_type = LOG_TYPE.from_string(request.POST.get('log_type'))
    if log_type is None:
        return JsonResponse(
            {'error': 'Invalid or missing log_type parameter'},
            status=400,
        )

    try:
        result = import_nginx_log(uploaded_file, log_type)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse(
            {
                'error': 'Failed to process log file',
                'details': str(e),
            },
            status=500,
        )


def get_usage_data(request):
    """
    API endpoint to fetch usage data for charts.

    Query parameters:
        - metric: 'visits' or 'tools' (default: 'visits')
        - days: number of days to look back (optional)
        - start_date: custom start date (optional, YYYY-MM-DD)
        - end_date: custom end date (optional, YYYY-MM-DD)
        - lab: filter by lab name (optional, 'all' for all labs)
        - tool: filter by tool_id (optional, 'all' for all tools aggregated)
    """
    metric = request.GET.get('metric', 'visits')
    lab_filter = request.GET.get('lab', 'all')
    tool_filter = request.GET.get('tool', 'all')

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

        # Get all dates in range
        all_dates = generate_date_range(start_date, end_date)

        # Get all unique labs
        all_labs = set()
        for item in data:
            all_labs.add(item['lab_name'])

        # Build data dict with actual counts
        lab_data_dict = defaultdict(dict)
        for item in data:
            lab = item['lab_name']
            date_obj = item['date']
            lab_data_dict[lab][date_obj] = item['count']

        # Format for Plotly with zeros for missing dates
        traces = []
        for lab_name in sorted(all_labs):
            dates = []
            counts = []
            for date_obj in all_dates:
                dates.append(date_obj.isoformat())
                counts.append(lab_data_dict[lab_name].get(date_obj, 0))

            traces.append({
                'name': lab_name,
                'x': dates,
                'y': counts,
                'type': 'scatter',
                'mode': 'lines',
            })

    elif metric == 'tools':
        # Query ToolUsage data
        queryset = ToolUsage.objects.filter(
            datetime__gte=start_date,
            datetime__lte=end_date
        )
        if lab_filter and lab_filter != 'all':
            queryset = queryset.filter(lab_name=lab_filter)

        # Get all dates in range
        all_dates = generate_date_range(start_date, end_date)

        traces = []

        if tool_filter == 'all':
            # Aggregate all tools together
            data = (
                queryset
                .annotate(date=TruncDate('datetime'))
                .values('date')
                .annotate(count=Count('id'))
                .order_by('date')
            )

            # Build data dict with actual counts
            data_dict = {}
            for item in data:
                data_dict[item['date']] = item['count']

            # Fill in zeros for missing dates
            dates = []
            counts = []
            for date_obj in all_dates:
                dates.append(date_obj.isoformat())
                counts.append(data_dict.get(date_obj, 0))

            traces.append({
                'name': 'All Tools',
                'x': dates,
                'y': counts,
                'type': 'scatter',
                'mode': 'lines',
            })
        else:
            # Filter by specific tool
            queryset = queryset.filter(tool_id=tool_filter)

            data = (
                queryset
                .annotate(date=TruncDate('datetime'))
                .values('date')
                .annotate(count=Count('id'))
                .order_by('date')
            )

            # Build data dict with actual counts
            data_dict = {}
            for item in data:
                data_dict[item['date']] = item['count']

            # Fill in zeros for missing dates
            dates = []
            counts = []
            for date_obj in all_dates:
                dates.append(date_obj.isoformat())
                counts.append(data_dict.get(date_obj, 0))

            # Get tool name from database
            tool_record = queryset.filter(tool_id=tool_filter).first()
            tool_name = (
                tool_record.tool_name
                if tool_record
                else tool_filter
            )

            traces.append({
                'name': tool_name,
                'x': dates,
                'y': counts,
                'type': 'scatter',
                'mode': 'lines',
                'hovertext': tool_filter,
            })
    else:
        return JsonResponse({'error': 'Invalid metric parameter'}, status=400)

    return JsonResponse({
        'traces': traces,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
    })


def get_tools_list(request):
    """
    API endpoint to get list of tools ordered by frequency.

    Query parameters:
        - lab: filter by lab name (optional, 'all' for all labs)
    """
    lab_filter = request.GET.get('lab', 'all')

    queryset = ToolUsage.objects.all()

    if lab_filter and lab_filter != 'all':
        queryset = queryset.filter(lab_name=lab_filter)

    # Get tools ordered by frequency (descending)
    tools = (
        queryset
        .values('tool_id', 'tool_name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Format the response
    tools_list = [
        {
            'tool_id': item['tool_id'],
            'count': item['count'],
            'display_name': item['tool_name'],
        }
        for item in tools
    ]

    return JsonResponse({'tools': tools_list})


def download_csv(request):
    """
    Download CSV of usage data.

    Query parameters:
        - metric: 'visits' or 'tools' (required)
        - days: number of days to look back (optional)
        - start_date: custom start date (optional, YYYY-MM-DD)
        - end_date: custom end date (optional, YYYY-MM-DD)
        - lab: filter by lab name (optional, 'all' for all labs)
        - tool: filter by tool_id (optional, 'all' for all tools)
    """
    metric = request.GET.get('metric', 'visits')
    lab_filter = request.GET.get('lab', 'all')
    tool_filter = request.GET.get('tool', 'all')

    # Handle custom date range
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        start_date = timezone.make_aware(
            datetime.strptime(start_date_str, '%Y-%m-%d')
        )
        end_date = timezone.make_aware(
            datetime.strptime(end_date_str, '%Y-%m-%d')
        )
        end_date = end_date.replace(hour=23, minute=59, second=59)
    else:
        days = int(request.GET.get('days', 90))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    filename = (
        f'galaxy_labs_{metric}_'
        f'{start_date.date()}_to_{end_date.date()}.csv'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # QUOTE_MINIMAL automatically quotes fields with special chars (commas)
    writer = csv.writer(response, quoting=csv.QUOTE_MINIMAL)

    if metric == 'visits':
        # Write header
        writer.writerow(['date', 'lab', 'visits'])

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

        # Write data rows
        for item in data:
            writer.writerow([
                item['date'].isoformat(),
                item['lab_name'],
                item['count'],
            ])

    elif metric == 'tools':
        # Write header
        writer.writerow(['date', 'lab', 'tool_id', 'jobs'])

        # Query ToolUsage data
        queryset = ToolUsage.objects.filter(
            datetime__gte=start_date,
            datetime__lte=end_date
        )
        if lab_filter and lab_filter != 'all':
            queryset = queryset.filter(lab_name=lab_filter)
        if tool_filter and tool_filter != 'all':
            queryset = queryset.filter(tool_id=tool_filter)

        data = (
            queryset
            .annotate(date=TruncDate('datetime'))
            .values('lab_name', 'tool_id', 'date')
            .annotate(count=Count('id'))
            .order_by('date', 'lab_name', 'tool_id')
        )

        # Write data rows
        # Note: csv.writer automatically quotes fields containing commas
        for item in data:
            writer.writerow([
                item['date'].isoformat(),
                item['lab_name'],
                item['tool_id'],
                item['count'],
            ])

    return response
