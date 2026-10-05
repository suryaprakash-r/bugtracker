from django.contrib.auth import get_user_model
from django.db.models import Count, Q

from apps.accounts.permissions import Permission, user_has_permission
from apps.bugs.models import Bug
from apps.projects.models import Project


User = get_user_model()

def get_visible_report_projects(user):
    """
    Return the projects visible to the authenticated user
    for reporting purposes.

    Reporting visibility follows the existing BugTracker RBAC.
    """

    if not user or not user.is_authenticated:
        return Project.objects.none()

    if not user_has_permission(user, Permission.VIEW_REPORTS):
        return Project.objects.none()

    if user.is_superuser or user.role == "ADMIN":
        return Project.objects.select_related(
            "manager"
        ).order_by("-created_at")

    if user.role == "PROJECT_MANAGER":
        return Project.objects.filter(
            manager=user
        ).select_related(
            "manager"
        ).order_by("-created_at")

    return Project.objects.none()


def get_visible_report_bugs(user):
    """
    Return the bugs visible to the authenticated user
    for reporting purposes.

    Reporting visibility follows the existing BugTracker RBAC.
    """

    if not user or not user.is_authenticated:
        return Bug.objects.none()

    if not user_has_permission(user, Permission.VIEW_REPORTS):
        return Bug.objects.none()

    if user.is_superuser or user.role == "ADMIN":
        return Bug.objects.select_related(
            "project",
            "reporter",
            "assigned_to",
        ).order_by("-created_at")

    if user.role == "PROJECT_MANAGER":
        return Bug.objects.filter(
            project__manager=user
        ).select_related(
            "project",
            "reporter",
            "assigned_to",
        ).order_by("-created_at")

    return Bug.objects.none()


def _get_distribution(queryset, field_name, choices):
    """
    Build a complete distribution for a model field.

    Every configured choice is included, even when its count is zero.
    """

    counts = (
        queryset
        .order_by()
        .values(field_name)
        .annotate(total=Count("id"))
    )

    count_map = {
        item[field_name]: item["total"]
        for item in counts
    }

    total = queryset.count()

    distribution = []

    for value, label in choices:
        item_total = count_map.get(value, 0)

        percentage = (
            round((item_total / total) * 100, 1)
            if total
            else 0
        )

        distribution.append(
            {
                "value": value,
                "label": label,
                "total": item_total,
                "percentage": percentage,
            }
        )

    return distribution


def get_bug_summary_report(bugs):
    """
    Return summary analytics for a visible bug queryset.

    The queryset passed to this function must already be restricted
    according to the current user's reporting visibility.
    """

    total_bugs = bugs.count()

    status_counts = _get_distribution(
        bugs,
        "status",
        Bug.Status.choices,
    )

    priority_counts = _get_distribution(
        bugs,
        "priority",
        Bug.Priority.choices,
    )

    severity_counts = _get_distribution(
        bugs,
        "severity",
        Bug.Severity.choices,
    )

    status_map = {
        item["value"]: item["total"]
        for item in status_counts
    }

    open_bugs = sum(
        status_map.get(status, 0)
        for status in {
            Bug.Status.NEW,
            Bug.Status.ASSIGNED,
            Bug.Status.IN_PROGRESS,
            Bug.Status.REOPENED,
        }
    )

    return {
        "total_bugs": total_bugs,
        "open_bugs": open_bugs,
        "unassigned_bugs": bugs.filter(
            assigned_to__isnull=True
        ).count(),
        "critical_bugs": bugs.filter(
            severity=Bug.Severity.CRITICAL
        ).count(),
        "resolved_bugs": status_map.get(
            Bug.Status.RESOLVED,
            0,
        ),
        "testing_bugs": status_map.get(
            Bug.Status.TESTING,
            0,
        ),
        "closed_bugs": status_map.get(
            Bug.Status.CLOSED,
            0,
        ),
        "reopened_bugs": status_map.get(
            Bug.Status.REOPENED,
            0,
        ),
        "status_counts": status_counts,
        "priority_counts": priority_counts,
        "severity_counts": severity_counts,
    }
    
def get_project_report(user):
    """
    Return project-level reporting data for the user's
    report-visible projects.

    Each project includes bug counts derived from its
    associated bugs.
    """

    projects = get_visible_report_projects(user)

    return projects.annotate(
        total_bugs=Count(
            "bugs",
            distinct=True,
        ),
        open_bugs=Count(
            "bugs",
            filter=Q(
                bugs__status__in=[
                    Bug.Status.NEW,
                    Bug.Status.ASSIGNED,
                    Bug.Status.IN_PROGRESS,
                    Bug.Status.REOPENED,
                ]
            ),
            distinct=True,
        ),
        resolved_bugs=Count(
            "bugs",
            filter=Q(
                bugs__status=Bug.Status.RESOLVED,
            ),
            distinct=True,
        ),
        testing_bugs=Count(
            "bugs",
            filter=Q(
                bugs__status=Bug.Status.TESTING,
            ),
            distinct=True,
        ),
        closed_bugs=Count(
            "bugs",
            filter=Q(
                bugs__status=Bug.Status.CLOSED,
            ),
            distinct=True,
        ),
        reopened_bugs=Count(
            "bugs",
            filter=Q(
                bugs__status=Bug.Status.REOPENED,
            ),
            distinct=True,
        ),
        critical_bugs=Count(
            "bugs",
            filter=Q(
                bugs__severity=Bug.Severity.CRITICAL,
            ),
            distinct=True,
        ),
    ).order_by(
        "-total_bugs",
        "project_key",
    )
    
    
def get_developer_workload_report(user):
    """
    Return developer workload metrics for developers who are
    active members of the user's report-visible projects.

    Developers with zero assigned bugs are included so the report
    represents the full visible development team.
    """

    projects = get_visible_report_projects(user)

    if not projects.exists():
        return User.objects.none()

    return (
        User.objects.filter(
            role=User.Role.DEVELOPER,
            project_memberships__project__in=projects,
            project_memberships__is_active=True,
            is_active=True,
        )
        .distinct()
        .annotate(
            total_bugs=Count(
                "assigned_bugs",
                filter=Q(
                    assigned_bugs__project__in=projects,
                ),
                distinct=True,
            ),
            open_bugs=Count(
                "assigned_bugs",
                filter=Q(
                    assigned_bugs__project__in=projects,
                    assigned_bugs__status__in=[
                        Bug.Status.NEW,
                        Bug.Status.ASSIGNED,
                        Bug.Status.IN_PROGRESS,
                        Bug.Status.REOPENED,
                    ],
                ),
                distinct=True,
            ),
            resolved_bugs=Count(
                "assigned_bugs",
                filter=Q(
                    assigned_bugs__project__in=projects,
                    assigned_bugs__status=Bug.Status.RESOLVED,
                ),
                distinct=True,
            ),
            testing_bugs=Count(
                "assigned_bugs",
                filter=Q(
                    assigned_bugs__project__in=projects,
                    assigned_bugs__status=Bug.Status.TESTING,
                ),
                distinct=True,
            ),
            closed_bugs=Count(
                "assigned_bugs",
                filter=Q(
                    assigned_bugs__project__in=projects,
                    assigned_bugs__status=Bug.Status.CLOSED,
                ),
                distinct=True,
            ),
            reopened_bugs=Count(
                "assigned_bugs",
                filter=Q(
                    assigned_bugs__project__in=projects,
                    assigned_bugs__status=Bug.Status.REOPENED,
                ),
                distinct=True,
            ),
            critical_bugs=Count(
                "assigned_bugs",
                filter=Q(
                    assigned_bugs__project__in=projects,
                    assigned_bugs__severity=Bug.Severity.CRITICAL,
                ),
                distinct=True,
            ),
        )
        .order_by(
            "-total_bugs",
            "first_name",
            "username",
        )
    )
    
def get_tester_qa_report(user):
    """
    Return tester / QA workload metrics for testers who are
    active members of the user's report-visible projects.

    Testers with zero assigned bugs are included so the report
    represents the full visible QA team.
    """

    projects = get_visible_report_projects(user)

    if not projects.exists():
        return User.objects.none()

    return (
        User.objects.filter(
            role=User.Role.TESTER,
            project_memberships__project__in=projects,
            project_memberships__is_active=True,
            is_active=True,
        )
        .distinct()
        .annotate(
            total_bugs=Count(
                "assigned_bugs",
                filter=Q(
                    assigned_bugs__project__in=projects,
                ),
                distinct=True,
            ),
            open_bugs=Count(
                "assigned_bugs",
                filter=Q(
                    assigned_bugs__project__in=projects,
                    assigned_bugs__status__in=[
                        Bug.Status.NEW,
                        Bug.Status.ASSIGNED,
                        Bug.Status.IN_PROGRESS,
                        Bug.Status.REOPENED,
                    ],
                ),
                distinct=True,
            ),
            resolved_bugs=Count(
                "assigned_bugs",
                filter=Q(
                    assigned_bugs__project__in=projects,
                    assigned_bugs__status=Bug.Status.RESOLVED,
                ),
                distinct=True,
            ),
            testing_bugs=Count(
                "assigned_bugs",
                filter=Q(
                    assigned_bugs__project__in=projects,
                    assigned_bugs__status=Bug.Status.TESTING,
                ),
                distinct=True,
            ),
            closed_bugs=Count(
                "assigned_bugs",
                filter=Q(
                    assigned_bugs__project__in=projects,
                    assigned_bugs__status=Bug.Status.CLOSED,
                ),
                distinct=True,
            ),
            reopened_bugs=Count(
                "assigned_bugs",
                filter=Q(
                    assigned_bugs__project__in=projects,
                    assigned_bugs__status=Bug.Status.REOPENED,
                ),
                distinct=True,
            ),
            critical_bugs=Count(
                "assigned_bugs",
                filter=Q(
                    assigned_bugs__project__in=projects,
                    assigned_bugs__severity=Bug.Severity.CRITICAL,
                ),
                distinct=True,
            ),
        )
        .order_by(
            "-testing_bugs",
            "-total_bugs",
            "first_name",
            "username",
        )
    )