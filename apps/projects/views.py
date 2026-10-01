from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.db.models import Count, Q

from apps.accounts.permissions import (
    Permission,
    can_manage_project,
    can_view_project,
    role_required,
)

from apps.notifications.services import notify_project_member_added

from .forms import ProjectForm, ProjectMemberForm
from .models import Project, ProjectMember


@login_required
@role_required(Permission.VIEW_PROJECT)
def project_list(request):

    user = request.user

    # -----------------------------------------------------
    # Base queryset based on RBAC
    # -----------------------------------------------------

    if user.is_superuser or user.role == "ADMIN":

        projects = Project.objects.select_related(
            "manager"
        )

    elif user.role == "PROJECT_MANAGER":

        projects = Project.objects.filter(
            manager=user
        ).select_related(
            "manager"
        )

    else:

        projects = Project.objects.filter(
            members__user=user,
            members__is_active=True,
        ).select_related(
            "manager"
        ).distinct()


    # -----------------------------------------------------
    # Search
    # -----------------------------------------------------

    search_query = request.GET.get(
        "search",
        ""
    ).strip()


    if search_query:

        projects = projects.filter(
            Q(name__icontains=search_query)
            | Q(project_key__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(manager__username__icontains=search_query)
            | Q(manager__first_name__icontains=search_query)
            | Q(manager__last_name__icontains=search_query)
        )


    # -----------------------------------------------------
    # Status filter
    # -----------------------------------------------------

    status_filter = request.GET.get(
        "status",
        ""
    ).strip()


    valid_statuses = {
        value
        for value, label in Project.Status.choices
    }


    if status_filter in valid_statuses:

        projects = projects.filter(
            status=status_filter
        )

    else:

        status_filter = ""


    # -----------------------------------------------------
    # Ordering
    # -----------------------------------------------------

    projects = projects.order_by(
        "-created_at"
    )


    # -----------------------------------------------------
    # Pagination
    # -----------------------------------------------------

    paginator = Paginator(
        projects,
        10,
    )

    page_number = request.GET.get(
        "page"
    )

    page_obj = paginator.get_page(
        page_number
    )


    context = {
        "projects": page_obj.object_list,
        "page_obj": page_obj,
        "search_query": search_query,
        "status_filter": status_filter,
        "status_choices": Project.Status.choices,
    }


    if request.headers.get("x-requested-with") == "XMLHttpRequest":

        return render(
            request,
            "projects/_project_list_results.html",
            context,
        )


    return render(
        request,
        "projects/project_list.html",
        context,
    )

@login_required
@role_required(Permission.VIEW_PROJECT)
def project_detail(request, project_id):

    project = get_object_or_404(
        Project.objects
        .select_related("manager")
        .annotate(
            total_bugs=Count("bugs", distinct=True),
            open_bugs=Count(
                "bugs",
                filter=Q(
                    bugs__status__in=[
                        "NEW",
                        "ASSIGNED",
                        "IN_PROGRESS",
                        "REOPENED",
                    ]
                ),
                distinct=True,
            ),
            resolved_bugs=Count(
                "bugs",
                filter=Q(
                    bugs__status__in=[
                        "RESOLVED",
                        "TESTING",
                        "CLOSED",
                    ]
                ),
                distinct=True,
            ),
        ),
        id=project_id,
    )


    if not can_view_project(
        request.user,
        project,
    ):
        raise PermissionDenied


    members = (
        project.members
        .select_related("user")
        .order_by(
            "-is_active",
            "user__first_name",
            "user__username",
        )
    )


    recent_bugs = (
        project.bugs
        .select_related(
            "reporter",
            "assigned_to",
        )
        .order_by("-created_at")[:5]
    )


    return render(
        request,
        "projects/project_detail.html",
        {
            "project": project,
            "members": members,
            "recent_bugs": recent_bugs,
        },
    )


@login_required
@role_required(Permission.CREATE_PROJECT)
def project_create(request):

    if request.method == "POST":

        form = ProjectForm(
            request.POST,
            user=request.user,
        )

        if form.is_valid():

            project = form.save(
                commit=False
            )

            if (
                not request.user.is_superuser
                and request.user.role == request.user.Role.PROJECT_MANAGER
            ):
                project.manager = request.user

            project.save()

            messages.success(
                request,
                f'Project "{project.name}" was created successfully.',
            )

            return redirect(
                "projects:detail",
                project.id,
            )

    else:

        form = ProjectForm(
            user=request.user,
        )

    return render(
        request,
        "projects/project_create.html",
        {
            "form": form,
        },
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

@login_required
@role_required(Permission.MANAGE_PROJECT)
def project_update(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id,
    )

    if not can_manage_project(
        request.user,
        project,
    ):
        raise PermissionDenied


    if request.method == "POST":

        form = ProjectForm(
            request.POST,
            instance=project,
            user=request.user,
        )

        if form.is_valid():

            updated_project = form.save(
                commit=False
            )


            # Project Manager must remain the
            # manager of their own project.

            if (
                not request.user.is_superuser
                and request.user.role
                == request.user.Role.PROJECT_MANAGER
            ):

                updated_project.manager = request.user


            updated_project.save()


            messages.success(
                request,
                f'Project "{updated_project.name}" was updated successfully.',
            )

            return redirect(
                "projects:detail",
                updated_project.id,
            )

    else:

        form = ProjectForm(
            instance=project,
            user=request.user,
        )


    return render(
        request,
        "projects/project_update.html",
        {
            "form": form,
            "project": project,
        },
    )
    
@login_required
@role_required(Permission.MANAGE_PROJECT_MEMBERS)
def project_members(request, project_id):

    project = get_object_or_404(
        Project.objects.select_related("manager"),
        id=project_id,
    )


    if not can_manage_project(
        request.user,
        project,
    ):
        raise PermissionDenied


    members = (
        project.members
        .select_related("user")
        .order_by(
            "-is_active",
            "user__first_name",
            "user__username",
        )
    )


    if request.method == "POST":

        form = ProjectMemberForm(
            request.POST,
            project=project,
        )

        if form.is_valid():

            user = form.cleaned_data["user"]

            membership = ProjectMember.objects.create(
                project=project,
                user=user,
                is_active=True,
            )

            notify_project_member_added(
                user=membership.user,
                project=membership.project,
            )

            messages.success(
                request,
                f"{user.username} was added to the project.",
            )

            return redirect(
                "projects:members",
                project.id,
            )

    else:

        form = ProjectMemberForm(
            project=project,
        )


    return render(
        request,
        "projects/project_members.html",
        {
            "project": project,
            "members": members,
            "form": form,
        },
    )

@login_required
@role_required(Permission.MANAGE_PROJECT_MEMBERS)
def project_member_toggle(request, project_id, member_id):

    if request.method != "POST":
        raise PermissionDenied


    project = get_object_or_404(
        Project,
        id=project_id,
    )


    if not can_manage_project(
        request.user,
        project,
    ):
        raise PermissionDenied


    membership = get_object_or_404(
        ProjectMember.objects.select_related("user"),
        id=member_id,
        project=project,
    )


    was_active = membership.is_active

    membership.is_active = not membership.is_active

    membership.save(
        update_fields=["is_active"]
    )

    if membership.is_active:

        notify_project_member_added(
            user=membership.user,
            project=project,
        )

        messages.success(
            request,
            f"{membership.user.username} was activated in the project.",
        )

    else:

        messages.success(
            request,
            f"{membership.user.username} was deactivated from the project.",
        )

    return redirect(
        "projects:members",
        project.id,
    )