"""URLS for static pages."""

from django.urls import path

from . import api, views
from django.views.generic import TemplateView

urlpatterns = [
    path('', views.export_lab, name='lab_export'),
    path('bootstrap', views.BootstrapLab.as_view(), name='lab_bootstrap'),
    path(
        'schema',
        TemplateView.as_view(template_name='docs/schema.html'),
        name='lab_schema',
    ),
    path(
        'tool-install',
        TemplateView.as_view(template_name='docs/tool-install.html'),
        name='lab_tool_install',
    ),
    path('lab/feedback/<subdomain>', api.lab_feedback, name='lab_feedback'),
]
