"""
Reporting service layer for BugTracker.

This module will contain reusable reporting queries,
visibility rules, filtering, and report aggregation logic.
"""


def get_visible_report_projects(user):
    """
    Return the projects visible to the authenticated user
    for reporting purposes.

    Reporting visibility will follow the existing BugTracker RBAC.
    """
    pass


def get_visible_report_bugs(user):
    """
    Return the bugs visible to the authenticated user
    for reporting purposes.

    Reporting visibility will follow the existing BugTracker RBAC.
    """
    pass