from datetime import date

import csv

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from apps.accounts.permissions import Permission, role_required

from .exporters import build_pdf_report

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
def report_export(request, export_format):
    """
    Export reports using the same RBAC and date filters
    as the main Reports page.

    Actual CSV/PDF generation will be added in later steps.
    """

    start_date = _parse_report_date(
        request.GET.get("start_date")
    )

    end_date = _parse_report_date(
        request.GET.get("end_date")
    )

    allowed_formats = {"csv", "pdf"}

    export_format = export_format.lower()

    if export_format not in allowed_formats:
        return HttpResponse(
            "Unsupported export format.",
            status=400,
        )

    context = _build_report_context(
        request.user,
        start_date=start_date,
        end_date=end_date,
    )

    if export_format == "csv":
        response = HttpResponse(
            content_type="text/csv"
        )

        response["Content-Disposition"] = (
            'attachment; filename="bugtracker_report.csv"'
        )

        writer = csv.writer(response)

        writer.writerow([
            "Bug Code",
            "Project",
            "Title",
            "Status",
            "Priority",
            "Severity",
            "Environment",
            "Reporter",
            "Assigned To",
            "Created Date",
            "Updated Date",
        ])

        bugs = get_visible_report_bugs(
            request.user,
            start_date=start_date,
            end_date=end_date,
        )

        for bug in bugs:
            writer.writerow([
                bug.bug_code,
                bug.project.project_key,
                bug.title,
                bug.get_status_display(),
                bug.get_priority_display(),
                bug.get_severity_display(),
                bug.get_environment_display(),
                bug.reporter.username if bug.reporter else "",
                bug.assigned_to.username if bug.assigned_to else "",
                bug.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                bug.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            ])

        return response
    
    if export_format == "pdf":
            pdf_buffer = build_pdf_report(context)
    
            response = HttpResponse(
                pdf_buffer.getvalue(),
                content_type="application/pdf",
            )
    
            response["Content-Disposition"] = (
                'attachment; filename="bugtracker_report.pdf"'
            )
    
            return response

    return HttpResponse(
        f"Export format '{export_format}' is registered "
        f"for {context['report_bug_count']} bugs."
    )

def _build_report_context(user, start_date=None, end_date=None):
    """
    Build the shared reporting context used by the Reports page
    and report export endpoints.

    The same RBAC and date-filtered bug queryset is used across
    all report sections.
    """

    projects = get_visible_report_projects(user)

    bugs = get_visible_report_bugs(
        user,
        start_date=start_date,
        end_date=end_date,
    )

    bug_summary = get_bug_summary_report(bugs)

    project_report = get_project_report(
        user,
        bugs=bugs,
    )

    developer_workload = get_developer_workload_report(
        user,
        bugs=bugs,
    )

    tester_qa_report = get_tester_qa_report(
        user,
        bugs=bugs,
    )

    return {
        "report_project_count": projects.count(),
        "report_bug_count": bugs.count(),
        "report_bugs": bugs,
        "bug_summary": bug_summary,
        "project_report": project_report,
        "developer_workload": developer_workload,
        "tester_qa_report": tester_qa_report,
        "start_date": start_date,
        "end_date": end_date,
    }
    
    
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

    context = _build_report_context(
        request.user,
        start_date=start_date,
        end_date=end_date,
    )
    
    project_paginator = Paginator(
        context["project_report"],
        5,
    )

    project_page = project_paginator.get_page(
        request.GET.get("project_page")
    )

    context["project_report"] = project_page
    context["project_page"] = project_page
    
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string(
            "reports/_project_report.html",
            context,
            request=request,
        )

        return HttpResponse(html)

    return render(
        request,
        "reports/index.html",
        context,
    )