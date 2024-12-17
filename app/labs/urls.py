"""URLS for static pages."""

from django.urls import path

from . import api, views

urlpatterns = [
    path('', views.export_lab, name="lab_export"),
    path('bootstrap', views.BootstrapLab.as_view(), name="lab_bootstrap"),
    path('schema', views.schema, name="lab_schema"),
    path('lab/feedback/<subdomain>', api.lab_feedback, name="lab_feedback"),
]
