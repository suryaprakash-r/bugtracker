from django.urls import path

from . import views


app_name = "notifications"


urlpatterns = [
    path(
        "",
        views.notification_list,
        name="list",
    ),
    path(
        "<int:notification_id>/read/",
        views.notification_mark_read,
        name="mark_read",
    ),

    path(
        "<int:notification_id>/unread/",
        views.notification_mark_unread,
        name="mark_unread",
    ),
]