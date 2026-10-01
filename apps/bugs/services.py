from django.db import transaction

from apps.accounts.models import User
from .models import Bug


def generate_bug_code(project):
    """
    Generate the next sequential bug code for a project.

    Examples:
        BT-001
        BT-002
        LMS-001
    """

    prefix = project.project_key.upper()

    existing_codes = (
        Bug.objects
        .filter(
            project=project,
            bug_code__startswith=f"{prefix}-",
        )
        .values_list(
            "bug_code",
            flat=True,
        )
    )

    highest_number = 0

    for code in existing_codes:

        try:

            number = int(
                code.rsplit("-", 1)[1]
            )

            highest_number = max(
                highest_number,
                number,
            )

        except (ValueError, IndexError):

            continue


    return f"{prefix}-{highest_number + 1:03d}"



STATUS_TRANSITIONS = {
    Bug.Status.NEW: {
        Bug.Status.ASSIGNED,
    },

    Bug.Status.ASSIGNED: {
        Bug.Status.IN_PROGRESS,
    },

    Bug.Status.IN_PROGRESS: {
        Bug.Status.RESOLVED,
    },

    Bug.Status.RESOLVED: {
        Bug.Status.TESTING,
    },

    Bug.Status.TESTING: {
        Bug.Status.CLOSED,
        Bug.Status.REOPENED,
    },

    Bug.Status.REOPENED: {
        Bug.Status.IN_PROGRESS,
    },

    Bug.Status.CLOSED: set(),
}


def get_allowed_status_transitions(user, bug):
    """
    Return the status transitions the current user
    is allowed to perform for this bug.

    NEW -> ASSIGNED is deliberately excluded here
    because assignment is handled by bug_assign().
    """

    if not user or not user.is_authenticated:
        return []


    next_statuses = set(
        STATUS_TRANSITIONS.get(
            bug.status,
            set(),
        )
    )


    # Assignment workflow handles NEW -> ASSIGNED.
    if bug.status == Bug.Status.NEW:
        next_statuses.discard(
            Bug.Status.ASSIGNED
        )
        return []


    # -----------------------------------------------------
    # Admin
    # -----------------------------------------------------

    if user.is_superuser or user.role == User.Role.ADMIN:
        return sorted(
            next_statuses
        )


    # -----------------------------------------------------
    # Project Manager
    # -----------------------------------------------------

    if user.role == User.Role.PROJECT_MANAGER:

        if bug.project.manager_id == user.id:
            return sorted(
                next_statuses
            )

        return []


    # -----------------------------------------------------
    # Developer
    # -----------------------------------------------------

    if user.role == User.Role.DEVELOPER:

        if bug.assigned_to_id != user.id:
            return []

        if bug.status in {
            Bug.Status.ASSIGNED,
            Bug.Status.IN_PROGRESS,
            Bug.Status.REOPENED,
        }:
            return sorted(
                next_statuses
            )

        return []


    # -----------------------------------------------------
    # Tester
    # -----------------------------------------------------

    if user.role == User.Role.TESTER:

        is_active_member = (
            bug.project.members.filter(
                user=user,
                is_active=True,
            ).exists()
        )

        if not is_active_member:
            return []

        if bug.status in {
            Bug.Status.RESOLVED,
            Bug.Status.TESTING,
        }:
            return sorted(
                next_statuses
            )

        return []


    return []


def can_change_bug_status(user, bug):
    """
    Return True when the user has at least one valid
    status transition available.
    """

    return bool(
        get_allowed_status_transitions(
            user,
            bug,
        )
    )