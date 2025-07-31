"""URLS for static pages."""

from django.urls import path

from . import api, views

urlpatterns = [
    path('', views.export_lab, name="lab_export"),
    path('bootstrap', views.BootstrapLab.as_view(), name="lab_bootstrap"),
    path('builder', views.LabBuilderView.as_view(), name="lab_builder"),
    path('builder/api', views.LabBuilderAPI.as_view(), name="lab_builder_api"),
    path('schema', views.schema, name="lab_schema"),
    path('lab/feedback/<subdomain>', api.lab_feedback, name="lab_feedback"),
]
