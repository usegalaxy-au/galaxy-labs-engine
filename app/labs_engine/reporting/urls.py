"""URLS for reporting API."""

from django.urls import path

from . import api

urlpatterns = [
    path('api/logs/upload', api.upload_logs, name='upload_logs'),
]
