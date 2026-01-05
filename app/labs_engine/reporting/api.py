"""API endpoints."""

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from .auth import authenticated
from .nginx_logs import import_nginx_log


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

    try:
        result = import_nginx_log(uploaded_file)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse(
            {
                'error': 'Failed to process log file',
                'details': str(e),
            },
            status=500,
        )
