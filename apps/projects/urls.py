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
    path(
        "<int:project_id>/edit/",
        views.project_update,
        name="update",
    ),
    path(
        "<int:project_id>/members/",
        views.project_members,
        name="members",
    ),

    path(
        "<int:project_id>/members/<int:member_id>/toggle/",
        views.project_member_toggle,
        name="member_toggle",
    ),
]