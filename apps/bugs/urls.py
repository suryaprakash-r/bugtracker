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
    path(
        "<int:bug_id>/assign/",
        views.bug_assign,
        name="assign",
    ),
    path(
        "<int:bug_id>/status/",
        views.bug_status_change,
        name="status_change",
    ),
    path(
        "<int:bug_id>/comments/",
        views.bug_comment_create,
        name="comment_create",
    ),
    path(
        "<int:bug_id>/attachments/upload/",
        views.bug_attachment_upload,
        name="attachment_upload",
    ),
    path(
        "attachments/<int:attachment_id>/view/",
        views.bug_attachment_view,
        name="attachment_view",
    ),

    path(
        "attachments/<int:attachment_id>/download/",
        views.bug_attachment_download,
        name="attachment_download",
    ),
    
    path(
        "attachments/<int:attachment_id>/delete/",
        views.bug_attachment_delete,
        name="attachment_delete",
    ),
]