from django.urls import path

from . import views


app_name = "reports"


urlpatterns = [
    path(
        "",
        views.report_index,
        name="index",
    ),
    path(
        "export/<str:export_format>/",
        views.report_export,
        name="export",
    ),
]