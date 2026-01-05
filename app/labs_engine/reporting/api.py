"""API endpoints."""

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from .auth import authenticated
from .nginx_logs import LOG_TYPE, import_nginx_log


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
