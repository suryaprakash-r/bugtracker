from django import template

from apps.accounts.permissions import (
    can_manage_project,
    can_update_bug,
    can_view_bug,
    user_has_permission,
)

register = template.Library()


@register.filter(name="has_permission")
def has_permission_filter(user, permission):
    return user_has_permission(user, permission)


@register.filter(name="can_update_bug")
def can_update_bug_filter(user, bug):
    return can_update_bug(user, bug)


@register.filter(name="can_view_bug")
def can_view_bug_filter(user, bug):
    return can_view_bug(user, bug)


@register.filter(name="can_manage_project")
def can_manage_project_filter(user, project):
    return can_manage_project(user, project)

@register.filter
def can_delete_attachment(user, attachment):
    from apps.accounts.permissions import can_delete_attachment as check_permission
    return check_permission(user, attachment)