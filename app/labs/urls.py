"""URLS for static pages."""

from django.urls import path

from . import api, views

urlpatterns = [
    path('lab/export', views.export_lab, name="lab_export"),
    path('lab/feedback/<subdomain>', api.lab_feedback, name="lab_feedback"),
]
