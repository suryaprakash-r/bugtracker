from datetime import date

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.accounts.permissions import Permission, role_required

from .services import (
    get_visible_report_projects,
    get_visible_report_bugs,
    get_bug_summary_report,
    get_project_report,
    get_developer_workload_report,
    get_tester_qa_report,
)


def _parse_report_date(value):
    """
    Parse a YYYY-MM-DD report filter value.

    Return a date object when valid, otherwise return None.
    """

    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
    
    
@login_required
@role_required(Permission.VIEW_REPORTS)
def report_index(request):
    """
    Main Reports landing page.

    Access is restricted to users with VIEW_REPORTS permission.
    """
    
    start_date = _parse_report_date(
        request.GET.get("start_date")
    )

    end_date = _parse_report_date(
        request.GET.get("end_date")
    )

    projects = get_visible_report_projects(request.user)
    
    bugs = get_visible_report_bugs(
        request.user,
        start_date=start_date,
        end_date=end_date,
    )

    bug_summary = get_bug_summary_report(bugs)
    
    project_report = get_project_report(
        request.user,
        bugs=bugs,
    )

    developer_workload = get_developer_workload_report(
        request.user,
        bugs=bugs,
    )

    tester_qa_report = get_tester_qa_report(
        request.user,
        bugs=bugs,
    )

    return render(
        request,
        "reports/index.html",
        {
            "report_project_count": projects.count(),
            "report_bug_count": bugs.count(),
            "bug_summary": bug_summary,
            
            "project_report": project_report,
            "developer_workload": developer_workload,
            "tester_qa_report": tester_qa_report,
            
            "start_date": start_date,
            "end_date": end_date,
        },
    )