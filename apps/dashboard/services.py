from datetime import timedelta

from django.utils import timezone
from django.db.models.functions import TruncDate
from django.db.models import Count, Q

from apps.bugs.models import Bug
from apps.notifications.models import ActivityLog
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


def get_bug_trend(bugs, days=14):
    """
    Return daily bug creation and resolution counts
    for the requested number of days.
    """

    today = timezone.localdate()
    start_date = today - timedelta(days=days - 1)

    date_range = [
        start_date + timedelta(days=index)
        for index in range(days)
    ]

    created_data = (
        bugs.filter(
            created_at__date__range=(start_date, today)
        )
        .annotate(
            trend_date=TruncDate("created_at")
        )
        .values("trend_date")
        .annotate(total=Count("id"))
        .order_by("trend_date")
    )

    resolved_data = (
        bugs.filter(
            resolved_at__isnull=False,
            resolved_at__date__range=(start_date, today)
        )
        .annotate(
            trend_date=TruncDate("resolved_at")
        )
        .values("trend_date")
        .annotate(total=Count("id"))
        .order_by("trend_date")
    )

    created_counts = {
        item["trend_date"]: item["total"]
        for item in created_data
    }

    resolved_counts = {
        item["trend_date"]: item["total"]
        for item in resolved_data
    }

    return [
        {
            "date": trend_date.strftime("%d %b"),
            "created": created_counts.get(trend_date, 0),
            "resolved": resolved_counts.get(trend_date, 0),
        }
        for trend_date in date_range
    ]

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

def get_visible_activity_logs(user, limit=10):
    """
    Return recent activity visible to the current user.

    Project-linked activity is limited to the user's visible
    projects.

    Activity without a project is visible only to:
    - the activity actor
    - Admin / superuser
    """

    visible_projects = get_visible_projects(user)

    if user.is_superuser or user.role == "ADMIN":
        activity_logs = ActivityLog.objects.all()

    else:
        activity_logs = ActivityLog.objects.filter(
            Q(project__in=visible_projects)
            | Q(project__isnull=True, user=user)
        )

    return (
        activity_logs
        .select_related(
            "user",
            "project",
        )
        .order_by("-created_at")[:limit]
    )

def get_dashboard_data(user):
    """
    Build all data required by the dashboard.

    Visibility is determined through the reusable
    project and bug querysets.
    """

    projects = get_visible_projects(user)
    bugs = get_visible_bugs(user)
    bug_trend = get_bug_trend(bugs)
    
    role_metrics = get_role_metrics(
        user,
        projects,
        bugs,
    )

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
    
    recent_activity = get_visible_activity_logs(
        user,
        limit=10,
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
        "recent_activity": recent_activity,
        
        "bug_trend": bug_trend,
        "role_metrics": role_metrics,
    }
    
def get_role_metrics(user, visible_projects, visible_bugs):
    """
    Return dashboard KPI metrics tailored to the user's role.
    """

    open_statuses = {
        "NEW",
        "ASSIGNED",
        "IN_PROGRESS",
        "REOPENED",
    }

    resolved_statuses = {
        "RESOLVED",
        "TESTING",
        "CLOSED",
    }

    role = getattr(user, "role", None)

    total_projects = visible_projects.count()
    active_projects = visible_projects.filter(
        status="ACTIVE"
    ).count()

    total_bugs = visible_bugs.count()

    open_bugs = visible_bugs.filter(
        status__in=open_statuses
    ).count()

    unassigned_bugs = visible_bugs.filter(
        assigned_to__isnull=True
    ).count()

    critical_bugs = visible_bugs.filter(
        severity="CRITICAL"
    ).count()

    resolved_bugs = visible_bugs.filter(
        status__in=resolved_statuses
    ).count()

    closed_bugs = visible_bugs.filter(
        status="CLOSED"
    ).count()


    # -----------------------------------------------------
    # Common metrics
    # -----------------------------------------------------

    common = {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "total_bugs": total_bugs,
        "open_bugs": open_bugs,
        "unassigned_bugs": unassigned_bugs,
        "critical_bugs": critical_bugs,
        "resolved_bugs": resolved_bugs,
        "closed_bugs": closed_bugs,
    }


    # -----------------------------------------------------
    # Admin / Project Manager
    # -----------------------------------------------------

    if (
        user.is_superuser
        or role in {"ADMIN", "PROJECT_MANAGER"}
    ):
        return {
            "role": role or "ADMIN",
            "role_label": (
                "Administrator"
                if role == "ADMIN" or user.is_superuser
                else "Project Manager"
            ),
            "metrics": common,
        }


    # -----------------------------------------------------
    # Developer
    # -----------------------------------------------------

    if role == "DEVELOPER":

        assigned_bugs = visible_bugs.filter(
            assigned_to=user
        )

        assigned_open_bugs = assigned_bugs.filter(
            status__in=open_statuses
        ).count()

        assigned_resolved_bugs = assigned_bugs.filter(
            status__in=resolved_statuses
        ).count()

        assigned_in_progress = assigned_bugs.filter(
            status="IN_PROGRESS"
        ).count()

        assigned_testing = assigned_bugs.filter(
            status="TESTING"
        ).count()

        assigned_reopened = assigned_bugs.filter(
            status="REOPENED"
        ).count()

        assigned_closed = assigned_bugs.filter(
            status="CLOSED"
        ).count()

        return {
            "role": role,
            "role_label": "Developer",
            "metrics": {
                "total_projects": total_projects,
                "active_projects": active_projects,
                "total_bugs": assigned_bugs.count(),
                "open_bugs": assigned_open_bugs,
                "unassigned_bugs": unassigned_bugs,
                "critical_bugs": assigned_bugs.filter(
                    severity="CRITICAL"
                ).count(),
                "resolved_bugs": assigned_resolved_bugs,
                "closed_bugs": assigned_closed,
                "in_progress_bugs": assigned_in_progress,
                "testing_bugs": assigned_testing,
                "reopened_bugs": assigned_reopened,
            },
        }


    # -----------------------------------------------------
    # Tester
    # -----------------------------------------------------

    if role == "TESTER":

        testing_bugs = visible_bugs.filter(
            status="TESTING"
        ).count()

        reopened_bugs = visible_bugs.filter(
            status="REOPENED"
        ).count()

        new_bugs = visible_bugs.filter(
            status="NEW"
        ).count()

        return {
            "role": role,
            "role_label": "Tester",
            "metrics": {
                "total_projects": total_projects,
                "active_projects": active_projects,
                "total_bugs": total_bugs,
                "open_bugs": open_bugs,
                "unassigned_bugs": unassigned_bugs,
                "critical_bugs": critical_bugs,
                "resolved_bugs": resolved_bugs,
                "closed_bugs": closed_bugs,
                "testing_bugs": testing_bugs,
                "reopened_bugs": reopened_bugs,
                "new_bugs": new_bugs,
            },
        }


    # -----------------------------------------------------
    # Fallback
    # -----------------------------------------------------

    return {
        "role": role or "UNKNOWN",
        "role_label": "User",
        "metrics": common,
    }