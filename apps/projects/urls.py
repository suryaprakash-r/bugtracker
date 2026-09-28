from django.urls import path

from . import views


app_name = "projects"


urlpatterns = [
    path(
        "",
        views.project_list,
        name="list",
    ),

    path(
        "create/",
        views.project_create,
        name="create",
    ),

    path(
        "<int:project_id>/",
        views.project_detail,
        name="detail",
    ),

    path(
        "<int:project_id>/manage/",
        views.project_manage,
        name="manage",
    ),
]