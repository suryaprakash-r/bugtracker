from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Notification

@login_required
def notification_list(request):
    """
    Display notifications belonging only to the logged-in user.
    """

    notifications_queryset = (
        Notification.objects
        .filter(recipient=request.user)
        .select_related("bug", "project")
        .order_by("-created_at")
    )

    paginator = Paginator(
        notifications_queryset,
        10,
    )

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "notifications": page_obj.object_list,
        "page_obj": page_obj,
    }

    return render(
        request,
        "notifications/notification_list.html",
        context,
    )
    
@login_required
@require_POST
def notification_mark_read(request, notification_id):
    """
    Mark a notification as read.

    Only the notification owner can modify it.
    """

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user,
    )

    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=["is_read"])

    return redirect("notifications:list")

@login_required
@require_POST
def notification_mark_unread(request, notification_id):
    """
    Mark a notification as unread.

    Only the notification owner can modify it.
    """

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user,
    )

    if notification.is_read:
        notification.is_read = False
        notification.save(update_fields=["is_read"])

    return redirect("notifications:list")