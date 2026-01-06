"""URLS for reporting API."""

from django.urls import path

from . import api, views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/usage', views.get_usage_data, name='usage_data'),
    path('api/logs/upload', api.upload_logs, name='upload_logs'),
]
