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


def get_bug_distribution(bugs, field_name, choices):
    """
    Return grouped bug counts and percentages for a model field.

    Example:
        get_bug_distribution(
            bugs,
            "status",
            Bug.Status.choices,
        )
    """

    total_bugs = bugs.count()

    grouped_counts = {
        item[field_name]: item["total"]
        for item in (
            bugs.values(field_name)
            .annotate(total=Count("id"))
        )
    }

    distribution = []

    for value, label in choices:

        count = grouped_counts.get(value, 0)

        if count > 0:

            percentage = (
                (count / total_bugs) * 100
                if total_bugs
                else 0
            )

            distribution.append({
                "value": value,
                "label": label,
                "total": count,
                "percentage": round(percentage, 1),
            })

    return distribution

def get_developer_workload(bugs):
    """
    Return workload statistics grouped by developer.

    Only bugs currently assigned to a developer are included.
    """

    workload = (
        bugs
        .filter(
            assigned_to__isnull=False,
            assigned_to__role="DEVELOPER",
        )
        .values(
            "assigned_to",
            "assigned_to__username",
            "assigned_to__first_name",
            "assigned_to__last_name",
        )
        .annotate(
            total=Count("id"),

            open=Count(
                "id",
                filter=Q(
                    status__in=OPEN_STATUSES
                ),
            ),

            resolved=Count(
                "id",
                filter=Q(
                    status__in=RESOLVED_STATUSES
                ),
            ),

            critical=Count(
                "id",
                filter=Q(
                    severity="CRITICAL"
                ),
            ),
        )
        .order_by("-open", "-total")
    )

    results = []

    for item in workload:

        first_name = (
            item["assigned_to__first_name"] or ""
        ).strip()

        last_name = (
            item["assigned_to__last_name"] or ""
        ).strip()

        full_name = " ".join(
            part
            for part in [first_name, last_name]
            if part
        )

        display_name = (
            full_name
            or item["assigned_to__username"]
        )

        results.append({
            "user_id": item["assigned_to"],
            "username": item["assigned_to__username"],
            "name": display_name,
            "total": item["total"],
            "open": item["open"],
            "resolved": item["resolved"],
            "critical": item["critical"],
        })

    return results

def get_testing_workload(bugs):
    """
    Return testing-related workload statistics.

    Because the current Bug model does not assign a tester
    directly, these values represent the testing queue across
    the user's visible bugs.
    """

    ready_for_testing = bugs.filter(
        status=Bug.Status.RESOLVED
    ).count()

    testing_in_progress = bugs.filter(
        status=Bug.Status.TESTING
    ).count()

    reopened_bugs = bugs.filter(
        status=Bug.Status.REOPENED
    ).count()

    return {
        "ready_for_testing": ready_for_testing,
        "testing_in_progress": testing_in_progress,
        "reopened_bugs": reopened_bugs,
    }

def get_dashboard_data(user):
    """
    Build all data required by the dashboard.

    Visibility is determined through the reusable
    project and bug querysets.
    """

    projects = get_visible_projects(user)
    bugs = get_visible_bugs(user)

    # ---------------------------------------------------------
    # Project KPIs
    # ---------------------------------------------------------

    total_projects = projects.count()

    active_projects = projects.filter(
        status=Project.Status.ACTIVE
    ).count()

    # ---------------------------------------------------------
    # Bug KPIs
    # ---------------------------------------------------------

    total_bugs = bugs.count()

    open_bugs = bugs.filter(
        status__in=OPEN_STATUSES
    ).count()

    unassigned_bugs = bugs.filter(
        assigned_to__isnull=True
    ).count()

    critical_bugs = bugs.filter(
        severity=Bug.Severity.CRITICAL
    ).count()

    resolved_bugs = bugs.filter(
        status__in=RESOLVED_STATUSES
    ).count()

    closed_bugs = bugs.filter(
        status=Bug.Status.CLOSED
    ).count()

    # ---------------------------------------------------------
    # Bug analytics
    # ---------------------------------------------------------

    status_counts = get_bug_distribution(
        bugs,
        "status",
        Bug.Status.choices,
    )

    priority_counts = get_bug_distribution(
        bugs,
        "priority",
        Bug.Priority.choices,
    )
    
    severity_counts = get_bug_distribution(
        bugs,
        "severity",
        Bug.Severity.choices,
    )
    
    developer_workload = get_developer_workload(
        bugs
    )

    testing_workload = get_testing_workload(
        bugs
    )

    # ---------------------------------------------------------
    # Recent bugs
    # ---------------------------------------------------------

    recent_bugs = (
        bugs
        .select_related(
            "project",
            "reporter",
            "assigned_to",
        )
        .order_by("-created_at")[:10]
    )

    # ---------------------------------------------------------
    # Dashboard payload
    # ---------------------------------------------------------

    return {
        "total_projects": total_projects,
        "active_projects": active_projects,

        "total_bugs": total_bugs,
        "open_bugs": open_bugs,
        "unassigned_bugs": unassigned_bugs,
        "critical_bugs": critical_bugs,
        "resolved_bugs": resolved_bugs,
        "closed_bugs": closed_bugs,

        "status_counts": status_counts,
        "priority_counts": priority_counts,
        "severity_counts": severity_counts,
        
        "developer_workload": developer_workload,
        "testing_workload": testing_workload,
        
        "recent_bugs": recent_bugs,
    }