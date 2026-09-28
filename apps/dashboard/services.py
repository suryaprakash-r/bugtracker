from django.db.models import Count, Q

from apps.bugs.models import Bug
from apps.projects.models import Project


OPEN_STATUSES = [
    Bug.Status.NEW,
    Bug.Status.ASSIGNED,
    Bug.Status.IN_PROGRESS,
    Bug.Status.REOPENED,
]

RESOLVED_STATUSES = [
    Bug.Status.RESOLVED,
    Bug.Status.TESTING,
    Bug.Status.CLOSED,
]


def get_visible_projects(user):
    """
    Return only projects the current user is allowed to see.
    """

    if user.is_superuser or user.role == "ADMIN":
        return Project.objects.all()

    if user.role == "PROJECT_MANAGER":
        return Project.objects.filter(
            manager=user
        )

    return Project.objects.filter(
        members__user=user,
        members__is_active=True,
    ).distinct()


def get_visible_bugs(user):
    """
    Return only bugs belonging to projects the current user
    is allowed to see.
    """

    if user.is_superuser or user.role == "ADMIN":
        return Bug.objects.all()

    if user.role == "PROJECT_MANAGER":
        return Bug.objects.filter(
            project__manager=user
        )

    return Bug.objects.filter(
        project__members__user=user,
        project__members__is_active=True,
    ).distinct()


def get_dashboard_data(user):

    projects = get_visible_projects(user)
    bugs = get_visible_bugs(user)

    total_projects = projects.count()

    total_bugs = bugs.count()

    open_bugs = bugs.filter(
        status__in=OPEN_STATUSES
    ).count()

    resolved_bugs = bugs.filter(
        status__in=RESOLVED_STATUSES
    ).count()

    status_counts = []

    for status_value, status_label in Bug.Status.choices:

        count = bugs.filter(
            status=status_value
        ).count()

        if count > 0:
            status_counts.append({
                "value": status_value,
                "label": status_label,
                "total": count,
            })


    priority_counts = []

    for priority_value, priority_label in Bug.Priority.choices:

        count = bugs.filter(
            priority=priority_value
        ).count()

        if count > 0:
            priority_counts.append({
                "value": priority_value,
                "label": priority_label,
                "total": count,
            })


    recent_bugs = bugs.select_related(
        "project",
        "reporter",
        "assigned_to",
    ).order_by(
        "-created_at"
    )[:10]


    return {
        "total_projects": total_projects,
        "total_bugs": total_bugs,
        "open_bugs": open_bugs,
        "resolved_bugs": resolved_bugs,
        "status_counts": status_counts,
        "priority_counts": priority_counts,
        "recent_bugs": recent_bugs,
    }