from django.urls import path

from . import views


app_name = "bugs"


urlpatterns = [
    path(
        "",
        views.bug_list,
        name="list",
    ),

    path(
        "create/",
        views.bug_create,
        name="create",
    ),

    path(
        "<int:bug_id>/",
        views.bug_detail,
        name="detail",
    ),

    path(
        "<int:bug_id>/edit/",
        views.bug_update,
        name="update",
    ),
]