from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render

from apps.accounts.permissions import (
    Permission,
    can_update_bug,
    can_view_bug,
    role_required,
)

from .models import Bug

@login_required
@role_required(Permission.VIEW_BUG)
def bug_list(request):
    user = request.user

    base_queryset = Bug.objects.select_related(
        "project",
        "reporter",
        "assigned_to",
    )

    if user.is_superuser or user.role == "ADMIN":
        bugs = base_queryset

    elif user.role == "PROJECT_MANAGER":
        bugs = base_queryset.filter(
            project__manager=user
        )

    elif user.role in {"DEVELOPER", "TESTER"}:
        bugs = base_queryset.filter(
            project__members__user=user,
            project__members__is_active=True,
        ).distinct()

    else:
        bugs = Bug.objects.none()

    return render(
        request,
        "bugs/bug_list.html",
        {
            "bugs": bugs,
        },
    )


@login_required
@role_required(Permission.VIEW_BUG)
def bug_detail(request, bug_id):
    bug = get_object_or_404(
        Bug.objects.select_related(
            "project",
            "reporter",
            "assigned_to",
        ),
        id=bug_id,
    )

    if not can_view_bug(request.user, bug):
        raise PermissionDenied

    return render(
        request,
        "bugs/bug_detail.html",
        {
            "bug": bug,
        },
    )


@login_required
@role_required(Permission.CREATE_BUG)
def bug_create(request):
    return render(
        request,
        "bugs/bug_create.html",
    )


@login_required
@role_required(Permission.UPDATE_BUG)
def bug_update(request, bug_id):
    bug = get_object_or_404(
        Bug,
        id=bug_id,
    )

    if not can_update_bug(request.user, bug):
        raise PermissionDenied

    return render(
        request,
        "bugs/bug_update.html",
        {
            "bug": bug,
        },
    )