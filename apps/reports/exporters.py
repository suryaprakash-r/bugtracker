from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def build_pdf_report(context):
    """
    Build a PDF report from the shared report context.
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title="BugTracker Report",
        author="BugTracker",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        leading=24,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=14,
    )

    section_style = ParagraphStyle(
        "ReportSection",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceBefore=8,
        spaceAfter=8,
    )

    normal_style = ParagraphStyle(
        "ReportNormal",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
    )

    story = []

    # ---------------------------------------------------------
    # Header
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "BugTracker Report",
            title_style,
        )
    )

    if context.get("start_date") and context.get("end_date"):
        period = (
            f"Report period: "
            f"{context['start_date'].strftime('%d %b %Y')} "
            f"to "
            f"{context['end_date'].strftime('%d %b %Y')}"
        )
    elif context.get("start_date"):
        period = (
            f"Report period: "
            f"{context['start_date'].strftime('%d %b %Y')} onward"
        )
    elif context.get("end_date"):
        period = (
            f"Report period: "
            f"Up to {context['end_date'].strftime('%d %b %Y')}"
        )
    else:
        period = "Report period: All visible bugs"

    story.append(
        Paragraph(
            period,
            subtitle_style,
        )
    )

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    summary = context["bug_summary"]

    story.append(
        Paragraph(
            "Bug Summary",
            section_style,
        )
    )

    summary_data = [
        ["Metric", "Value"],
        ["Total Bugs", summary["total_bugs"]],
        ["Open Bugs", summary["open_bugs"]],
        ["Unassigned Bugs", summary["unassigned_bugs"]],
        ["Critical Bugs", summary["critical_bugs"]],
        ["Resolved Bugs", summary["resolved_bugs"]],
        ["Testing Bugs", summary["testing_bugs"]],
        ["Reopened Bugs", summary["reopened_bugs"]],
        ["Closed Bugs", summary["closed_bugs"]],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[50 * mm, 25 * mm],
    )

    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                    colors.white,
                    colors.HexColor("#F8FAFC"),
                ]),
                ("ALIGN", (1, 1), (1, -1), "CENTER"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    story.append(summary_table)
    story.append(Spacer(1, 8))

    # ---------------------------------------------------------
    # Bug Details
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Bug Details",
            section_style,
        )
    )

    bugs = context["report_bugs"]

    bug_data = [[
        "Bug Code",
        "Project",
        "Title",
        "Status",
        "Priority",
        "Severity",
        "Environment",
        "Reporter",
        "Assigned To",
        "Created",
    ]]

    for bug in bugs:
        bug_data.append([
            bug.bug_code,
            bug.project.project_key,
            Paragraph(
                str(bug.title),
                normal_style,
            ),
            bug.get_status_display(),
            bug.get_priority_display(),
            bug.get_severity_display(),
            bug.get_environment_display(),
            bug.reporter.username if bug.reporter else "-",
            bug.assigned_to.username if bug.assigned_to else "-",
            bug.created_at.strftime("%d-%m-%Y"),
        ])

    bug_table = Table(
        bug_data,
        repeatRows=1,
        colWidths=[
            24 * mm,
            18 * mm,
            60 * mm,
            25 * mm,
            21 * mm,
            21 * mm,
            28 * mm,
            25 * mm,
            28 * mm,
            25 * mm,
        ],
    )

    bug_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                    colors.white,
                    colors.HexColor("#F8FAFC"),
                ]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    story.append(bug_table)

    document.build(story)

    buffer.seek(0)

    return buffer