"""API endpoints."""

from django.http import JsonResponse, HttpResponseBadRequest

from .forms import LabFeedbackForm


def lab_feedback(request, subdomain):
    """Process feedback form for *.usegalaxy.org.au subsites."""
    if request.method != 'POST':
        return HttpResponseBadRequest()
    form = LabFeedbackForm(request.POST)
    if form.is_valid():
        form.dispatch(subject=f"{subdomain.title()} Lab feedback")
        return JsonResponse({'success': True})
    return JsonResponse({
        'success': False,
        'errors_json': form.errors.as_json(),
    })
