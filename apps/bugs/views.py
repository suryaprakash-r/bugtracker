import mimetypes
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.http import FileResponse, JsonResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from apps.accounts.permissions import (
    Permission,
    can_add_comment,
    can_assign_bug,
    can_update_bug,
    can_view_bug,
    can_delete_attachment,
    role_required,
)

from .forms import (
    BugAssignmentForm,
    BugCommentForm,
    BugCreateForm,
    BugStatusChangeForm,
    BugUpdateForm,
    BugAttachmentForm,
)

from .services import (
    generate_bug_code,
    get_allowed_status_transitions,
    can_change_bug_status,
)
from .models import (
    Bug,
    BugComment,
    BugStatusHistory,
    BugAttachment,
)
from .attachment_services import (
    process_uploaded_file,
    sanitize_filename,
    generate_storage_name,
)

from apps.notifications.models import Notification
from apps.notifications.services import (
    create_notification,
    notify_bug_status_change,
    notify_bug_comment,
)

@login_required
@role_required(Permission.VIEW_BUG)
def bug_list(request):

    user = request.user

    # -----------------------------------------------------
    # Base queryset based on RBAC
    # -----------------------------------------------------

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

    elif user.role in {
        "DEVELOPER",
        "TESTER",
    }:

        bugs = base_queryset.filter(
            project__members__user=user,
            project__members__is_active=True,
        ).distinct()

    else:

        bugs = Bug.objects.none()


    # -----------------------------------------------------
    # Search
    # -----------------------------------------------------

    search_query = request.GET.get(
        "search",
        "",
    ).strip()


    if search_query:

        bugs = bugs.filter(
            Q(bug_code__icontains=search_query)
            | Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(project__name__icontains=search_query)
            | Q(project__project_key__icontains=search_query)
            | Q(reporter__username__icontains=search_query)
            | Q(reporter__first_name__icontains=search_query)
            | Q(reporter__last_name__icontains=search_query)
            | Q(assigned_to__username__icontains=search_query)
            | Q(assigned_to__first_name__icontains=search_query)
            | Q(assigned_to__last_name__icontains=search_query)
        ).distinct()


    # -----------------------------------------------------
    # Status
    # -----------------------------------------------------

    status_filter = request.GET.get(
        "status",
        "",
    ).strip()


    valid_statuses = {
        value
        for value, label in Bug.Status.choices
    }


    if status_filter in valid_statuses:

        bugs = bugs.filter(
            status=status_filter
        )

    else:

        status_filter = ""


    # -----------------------------------------------------
    # Severity
    # -----------------------------------------------------

    severity_filter = request.GET.get(
        "severity",
        "",
    ).strip()


    valid_severities = {
        value
        for value, label in Bug.Severity.choices
    }


    if severity_filter in valid_severities:

        bugs = bugs.filter(
            severity=severity_filter
        )

    else:

        severity_filter = ""


    # -----------------------------------------------------
    # Priority
    # -----------------------------------------------------

    priority_filter = request.GET.get(
        "priority",
        "",
    ).strip()


    valid_priorities = {
        value
        for value, label in Bug.Priority.choices
    }


    if priority_filter in valid_priorities:

        bugs = bugs.filter(
            priority=priority_filter
        )

    else:

        priority_filter = ""


    # -----------------------------------------------------
    # Ordering
    # -----------------------------------------------------

    bugs = bugs.order_by(
        "-created_at"
    )


    # -----------------------------------------------------
    # Pagination
    # -----------------------------------------------------

    paginator = Paginator(
        bugs,
        10,
    )

    page_number = request.GET.get(
        "page"
    )

    page_obj = paginator.get_page(
        page_number
    )


    context = {
        "bugs": page_obj.object_list,
        "page_obj": page_obj,

        "search_query": search_query,

        "status_filter": status_filter,
        "severity_filter": severity_filter,
        "priority_filter": priority_filter,

        "status_choices": Bug.Status.choices,
        "severity_choices": Bug.Severity.choices,
        "priority_choices": Bug.Priority.choices,
    }


    if request.headers.get(
        "x-requested-with"
    ) == "XMLHttpRequest":

        return render(
            request,
            "bugs/_bug_list_results.html",
            context,
        )


    return render(
        request,
        "bugs/bug_list.html",
        context,
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


    if not can_view_bug(
        request.user,
        bug,
    ):
        raise PermissionDenied


    comments = (
        bug.comments
        .select_related("user")
        .order_by("created_at")
    )
    
    attachments = bug.attachments.select_related(
        "uploaded_by"
    ).order_by("-uploaded_at")


    status_history = (
        bug.status_history
        .select_related("changed_by")
        .order_by("-changed_at")
    )


    return render(
        request,
        "bugs/bug_detail.html",
        {
            "bug": bug,

            "comments": comments,

            "status_history": status_history,

            "can_assign": can_assign_bug(
                request.user,
                bug,
            ),

            "can_change_status": can_change_bug_status(
                request.user,
                bug,
            ),

            "can_add_comment": can_add_comment(
                request.user,
                bug,
            ),

            "comment_form": BugCommentForm(),
            "attachments": attachments,
        },
    )


@login_required
@role_required(Permission.CREATE_BUG)
def bug_create(request):

    if request.method == "POST":

        form = BugCreateForm(
            request.POST,
            user=request.user,
        )

        if form.is_valid():

            with transaction.atomic():

                bug = form.save(
                    commit=False
                )

                bug.reporter = request.user

                bug.status = Bug.Status.NEW

                bug.bug_code = generate_bug_code(
                    bug.project
                )

                bug.save()


            messages.success(
                request,
                f"Bug {bug.bug_code} was created successfully.",
            )

            return redirect(
                "bugs:detail",
                bug.id,
            )

    else:

        form = BugCreateForm(
            user=request.user,
        )


    return render(
        request,
        "bugs/bug_create.html",
        {
            "form": form,
        },
    )

@login_required
@role_required(Permission.UPDATE_BUG)
def bug_update(request, bug_id):

    bug = get_object_or_404(
        Bug.objects.select_related(
            "project",
            "reporter",
            "assigned_to",
        ),
        id=bug_id,
    )


    if not can_update_bug(
        request.user,
        bug,
    ):
        raise PermissionDenied


    if request.method == "POST":

        form = BugUpdateForm(
            request.POST,
            instance=bug,
        )


        if form.is_valid():

            updated_bug = form.save()

            messages.success(
                request,
                f"Bug {updated_bug.bug_code} was updated successfully.",
            )

            return redirect(
                "bugs:detail",
                updated_bug.id,
            )


    else:

        form = BugUpdateForm(
            instance=bug,
        )


    return render(
        request,
        "bugs/bug_update.html",
        {
            "bug": bug,
            "form": form,
        },
    )
    
@login_required
@role_required(Permission.ASSIGN_BUG)
def bug_assign(request, bug_id):

    bug = get_object_or_404(
        Bug.objects.select_related(
            "project",
            "assigned_to",
        ),
        id=bug_id,
    )


    if not can_assign_bug(
        request.user,
        bug,
    ):
        raise PermissionDenied


    # Assignment is intended for bugs that are
    # new or already assigned.

    if bug.status not in {
        Bug.Status.NEW,
        Bug.Status.ASSIGNED,
    }:

        messages.warning(
            request,
            (
                f"Bug {bug.bug_code} cannot be assigned "
                f"while it is {bug.get_status_display()}."
            ),
        )

        return redirect(
            "bugs:detail",
            bug.id,
        )


    if request.method == "POST":

        form = BugAssignmentForm(
            request.POST,
            bug=bug,
        )


        if form.is_valid():

            developer = form.cleaned_data[
                "assigned_to"
            ]


            with transaction.atomic():

                locked_bug = (
                    Bug.objects
                    .select_for_update()
                    .select_related("project")
                    .get(id=bug.id)
                )


                if locked_bug.status not in {
                    Bug.Status.NEW,
                    Bug.Status.ASSIGNED,
                }:

                    raise PermissionDenied


                previous_status = (
                    locked_bug.status
                )

                previous_assignee_id = (
                    locked_bug.assigned_to_id
                )


                locked_bug.assigned_to = developer

                if previous_status == Bug.Status.NEW:

                    locked_bug.status = (
                        Bug.Status.ASSIGNED
                    )

                locked_bug.save(
                    update_fields=[
                        "assigned_to",
                        "status",
                        "updated_at",
                    ]
                )


                # Create status history only when
                # the status actually changes.

                if previous_status != locked_bug.status:

                    BugStatusHistory.objects.create(
                        bug=locked_bug,
                        old_status=previous_status,
                        new_status=locked_bug.status,
                        changed_by=request.user,
                        comment=(
                            f"Bug assigned to "
                            f"{developer.username}."
                        ),
                    )


            # if previous_assignee_id == developer.id:

            #     messages.success(
            #         request,
            #         (
            #             f"Bug {bug.bug_code} is already assigned "
            #             f"to {developer.username}."
            #         ),
            #     )
            
            if previous_assignee_id != developer.id:
                create_notification(
                    recipient=developer,
                    title="Bug Assigned",
                    message=(
                        f"You have been assigned bug "
                        f"{locked_bug.bug_code} in project "
                        f"{locked_bug.project.name}."
                    ),
                    notification_type=Notification.NotificationType.BUG_ASSIGNED,
                    bug=locked_bug,
                    project=locked_bug.project,
                )

            else:

                messages.success(
                    request,
                    (
                        f"Bug {bug.bug_code} was assigned "
                        f"to {developer.username}."
                    ),
                )


            return redirect(
                "bugs:detail",
                bug.id,
            )


    else:

        form = BugAssignmentForm(
            bug=bug,
        )


    return render(
        request,
        "bugs/bug_assign.html",
        {
            "bug": bug,
            "form": form,
        },
    )
    
@login_required
@role_required(Permission.CHANGE_BUG_STATUS)
def bug_status_change(request, bug_id):

    bug = get_object_or_404(
        Bug.objects.select_related(
            "project",
            "reporter",
            "assigned_to",
        ),
        id=bug_id,
    )


    allowed_statuses = (
        get_allowed_status_transitions(
            request.user,
            bug,
        )
    )


    if not allowed_statuses:

        messages.info(
            request,
            "There are no valid status transitions available for this bug.",
        )

        return redirect(
            "bugs:detail",
            bug.id,
        )


    if request.method == "POST":

        form = BugStatusChangeForm(
            request.POST,
            bug=bug,
            user=request.user,
        )


        if form.is_valid():

            requested_status = form.cleaned_data[
                "new_status"
            ]

            comment = form.cleaned_data[
                "comment"
            ]


            with transaction.atomic():

                locked_bug = (
                    Bug.objects
                    .select_for_update()
                    .select_related(
                        "project",
                    )
                    .get(
                        id=bug.id
                    )
                )


                allowed_statuses = (
                    get_allowed_status_transitions(
                        request.user,
                        locked_bug,
                    )
                )


                if requested_status not in allowed_statuses:

                    raise PermissionDenied


                old_status = locked_bug.status


                # -------------------------------------------------
                # Update lifecycle timestamps
                # -------------------------------------------------

                now = timezone.now()


                if requested_status == Bug.Status.RESOLVED:

                    locked_bug.resolved_at = now

                elif requested_status == Bug.Status.REOPENED:

                    locked_bug.resolved_at = None


                if requested_status == Bug.Status.CLOSED:

                    locked_bug.closed_at = now

                else:

                    locked_bug.closed_at = None


                locked_bug.status = requested_status

                locked_bug.save()


                # -------------------------------------------------
                # Status History
                # -------------------------------------------------

                BugStatusHistory.objects.create(
                    bug=locked_bug,
                    old_status=old_status,
                    new_status=requested_status,
                    changed_by=request.user,
                    comment=comment,
                )
                
                notify_bug_status_change(
                    bug=locked_bug,
                    old_status=old_status,
                    new_status=requested_status,
                    changed_by=request.user,
                )


            messages.success(
                request,
                (
                    f"Bug {bug.bug_code} status changed from "
                    f"{dict(Bug.Status.choices)[old_status]} to "
                    f"{dict(Bug.Status.choices)[requested_status]}."
                ),
            )


            return redirect(
                "bugs:detail",
                bug.id,
            )


    else:

        form = BugStatusChangeForm(
            bug=bug,
            user=request.user,
        )


    return render(
        request,
        "bugs/bug_status_change.html",
        {
            "bug": bug,
            "form": form,
        },
    )
    
    
@login_required
@role_required(Permission.ADD_COMMENT)
def bug_comment_create(request, bug_id):

    if request.method != "POST":
        raise PermissionDenied


    bug = get_object_or_404(
        Bug.objects.select_related(
            "project",
        ),
        id=bug_id,
    )


    if not can_add_comment(
        request.user,
        bug,
    ):
        raise PermissionDenied


    form = BugCommentForm(
        request.POST,
    )


    if not form.is_valid():

        if request.headers.get(
            "x-requested-with"
        ) == "XMLHttpRequest":

            return JsonResponse(
                {
                    "success": False,
                    "errors": form.errors,
                },
                status=400,
            )

        return redirect(
            "bugs:detail",
            bug.id,
        )


    comment = BugComment.objects.create(
        bug=bug,
        user=request.user,
        message=form.cleaned_data["message"],
    )
    
    notify_bug_comment(
        bug=bug,
        commenter=request.user,
    )


    if request.headers.get(
        "x-requested-with"
    ) == "XMLHttpRequest":

        html = render_to_string(
            "bugs/_bug_comment.html",
            {
                "comment": comment,
            },
            request=request,
        )

        return JsonResponse(
            {
                "success": True,
                "html": html,
            }
        )


    return redirect(
        "bugs:detail",
        bug.id,
    )
    
def _get_authorized_attachment(user, attachment_id):
    """
    Return the attachment only when the user is authorized
    to view the related bug.
    """

    attachment = get_object_or_404(
        BugAttachment.objects.select_related(
            "bug__project",
            "uploaded_by",
        ),
        id=attachment_id,
    )

    if not can_view_bug(user, attachment.bug):
        raise PermissionDenied

    return attachment

@login_required
def bug_attachment_view(request, attachment_id):
    attachment = _get_authorized_attachment(
        request.user,
        attachment_id,
    )

    if not attachment.file:
        raise PermissionDenied

    file_handle = attachment.file.open("rb")

    content_type, _ = mimetypes.guess_type(
        attachment.file_name
    )

    response = FileResponse(
        file_handle,
        as_attachment=False,
        filename=attachment.file_name,
        content_type=content_type or "application/octet-stream",
    )

    return response

@login_required
def bug_attachment_download(request, attachment_id):
    attachment = _get_authorized_attachment(
        request.user,
        attachment_id,
    )

    if not attachment.file:
        raise PermissionDenied

    file_handle = attachment.file.open("rb")

    content_type, _ = mimetypes.guess_type(
        attachment.file_name
    )

    response = FileResponse(
        file_handle,
        as_attachment=True,
        filename=attachment.file_name,
        content_type=content_type or "application/octet-stream",
    )

    return response

@login_required
@role_required(Permission.DELETE_ATTACHMENT)
def bug_attachment_delete(request, attachment_id):

    if request.method != "POST":
        raise PermissionDenied

    attachment = get_object_or_404(
        BugAttachment.objects.select_related(
            "bug__project",
            "uploaded_by",
        ),
        id=attachment_id,
    )

    if not can_view_bug(request.user, attachment.bug):
        raise PermissionDenied

    if not can_delete_attachment(request.user, attachment):
        raise PermissionDenied

    bug_id = attachment.bug_id
    file_name = attachment.file_name

    with transaction.atomic():
        attachment.file.delete(save=False)
        attachment.delete()

    messages.success(
        request,
        f"Attachment '{file_name}' was deleted successfully.",
    )

    return redirect("bugs:detail", bug_id)
    
@login_required
def bug_attachment_upload(request, bug_id):
    bug = get_object_or_404(
        Bug.objects.select_related("project"),
        id=bug_id,
    )

    if not can_view_bug(request.user, bug):
        raise PermissionDenied

    if request.method != "POST":
        raise PermissionDenied

    form = BugAttachmentForm(request.POST, request.FILES)

    if not form.is_valid():
        for error in form.errors.get("file", []):
            messages.error(request, error)

        return redirect("bugs:detail", bug.id)

    uploaded_file = form.cleaned_data["file"]

    try:
        processed_file, processed_name = process_uploaded_file(
            uploaded_file
        )
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("bugs:detail", bug.id)

    display_name = sanitize_filename(
        uploaded_file.name
    )

    storage_name = generate_storage_name(
        processed_name
    )

    attachment = BugAttachment(
        bug=bug,
        uploaded_by=request.user,
        file_name=display_name,
    )

    attachment.file.save(
        storage_name,
        processed_file,
        save=False,
    )

    attachment.file_size = attachment.file.size
    attachment.save()


    messages.success(
        request,
        f"Attachment '{attachment.file_name}' uploaded successfully.",
    )

    return redirect("bugs:detail", bug.id)