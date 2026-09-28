from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render

from apps.accounts.permissions import (
    Permission,
    can_manage_project,
    can_view_project,
    role_required,
)

from .models import Project


@login_required
@role_required(Permission.VIEW_PROJECT)
def project_list(request):
    user = request.user

    if user.is_superuser or user.role == "ADMIN":
        projects = Project.objects.select_related("manager")

    elif user.role == "PROJECT_MANAGER":
        projects = Project.objects.filter(
            manager=user
        ).select_related("manager")

    else:
        projects = Project.objects.filter(
            members__user=user,
            members__is_active=True,
        ).select_related("manager").distinct()

    return render(
        request,
        "projects/project_list.html",
        {
            "projects": projects,
        },
    )


@login_required
@role_required(Permission.VIEW_PROJECT)
def project_detail(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related("manager"),
        id=project_id,
    )

    if not can_view_project(request.user, project):
        raise PermissionDenied

    return render(
        request,
        "projects/project_detail.html",
        {
            "project": project,
        },
    )


@login_required
@role_required(Permission.CREATE_PROJECT)
def project_create(request):
    return render(
        request,
        "projects/project_create.html",
    )


@login_required
@role_required(Permission.MANAGE_PROJECT)
def project_manage(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if not can_manage_project(request.user, project):
        raise PermissionDenied

    return render(
        request,
        "projects/project_manage.html",
        {
            "project": project,
        },
    )