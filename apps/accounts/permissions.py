from functools import wraps

from django.core.exceptions import PermissionDenied

from .models import User

class Permission:
    """
    Application-level permissions used by BugTracker RBAC.
    """

    MANAGE_USERS = "manage_users"

    CREATE_PROJECT = "create_project"
    MANAGE_PROJECT = "manage_project"
    MANAGE_PROJECT_MEMBERS = "manage_project_members"

    CREATE_BUG = "create_bug"
    VIEW_BUG = "view_bug"
    ASSIGN_BUG = "assign_bug"
    UPDATE_BUG = "update_bug"
    CHANGE_BUG_STATUS = "change_bug_status"
    REOPEN_BUG = "reopen_bug"

    ADD_COMMENT = "add_comment"
    ADD_ATTACHMENT = "add_attachment"

    VIEW_REPORTS = "view_reports"
    VIEW_ACTIVITY_LOG = "view_activity_log"
    
    VIEW_PROJECT = "view_project"

ROLE_PERMISSIONS = {
    "ADMIN": {
        Permission.MANAGE_USERS,
        Permission.CREATE_PROJECT,
        Permission.MANAGE_PROJECT,
        Permission.MANAGE_PROJECT_MEMBERS,
        Permission.CREATE_BUG,
        Permission.VIEW_BUG,
        Permission.ASSIGN_BUG,
        Permission.UPDATE_BUG,
        Permission.CHANGE_BUG_STATUS,
        Permission.REOPEN_BUG,
        Permission.ADD_COMMENT,
        Permission.ADD_ATTACHMENT,
        Permission.VIEW_REPORTS,
        Permission.VIEW_ACTIVITY_LOG,
        Permission.VIEW_PROJECT,
    },

    "PROJECT_MANAGER": {
        Permission.CREATE_PROJECT,
        Permission.MANAGE_PROJECT,
        Permission.MANAGE_PROJECT_MEMBERS,
        Permission.VIEW_BUG,
        Permission.ASSIGN_BUG,
        Permission.CHANGE_BUG_STATUS,
        Permission.ADD_COMMENT,
        Permission.ADD_ATTACHMENT,
        Permission.VIEW_REPORTS,
        Permission.VIEW_PROJECT,
    },

    "DEVELOPER": {
        Permission.VIEW_BUG,
        Permission.UPDATE_BUG,
        Permission.CHANGE_BUG_STATUS,
        Permission.ADD_COMMENT,
        Permission.ADD_ATTACHMENT,
        Permission.VIEW_PROJECT,
    },

    "TESTER": {
        Permission.CREATE_BUG,
        Permission.VIEW_BUG,
        Permission.CHANGE_BUG_STATUS,
        Permission.REOPEN_BUG,
        Permission.ADD_COMMENT,
        Permission.ADD_ATTACHMENT,
        Permission.VIEW_PROJECT,
    },
}


def user_has_permission(user, permission):
    
    """
    Return True when the authenticated user has the requested
    application permission through their role.
    """

    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return permission in ROLE_PERMISSIONS.get(user.role, set())


def role_has_permission(role, permission):
    """
    Check whether a role has a specific permission.
    """

    return permission in ROLE_PERMISSIONS.get(role, set())


def role_required(permission):
    """
    Decorator for views that require a specific application permission.
    """

    def decorator(view_func):

        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):

            if not request.user.is_authenticated:
                raise PermissionDenied

            if not user_has_permission(
                request.user,
                permission,
            ):
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator


def roles_required(*roles):
    """
    Decorator for views that require one of the specified roles.
    """

    def decorator(view_func):

        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):

            if not request.user.is_authenticated:
                raise PermissionDenied

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            if request.user.role not in roles:
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator


def can_manage_project(user, project):
    """
    Check whether the user can manage the given project.
    """

    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if user.role == User.Role.ADMIN:
        return True

    if user.role == "PROJECT_MANAGER":
        return project.manager_id == user.id

    return False


def can_view_project(user, project):
    """
    Check whether the user can view the given project.
    """

    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if user.role == User.Role.ADMIN:
        return True

    if project.manager_id == user.id:
        return True

    return project.members.filter(
        user=user,
        is_active=True,
    ).exists()


def can_update_bug(user, bug):
    """
    Check whether the user can update the given bug.
    """

    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if user.role == User.Role.ADMIN:
        return True

    if user.role == "DEVELOPER":
        return bug.assigned_to_id == user.id

    return False


def can_view_bug(user, bug):
    """
    Check whether the user can view the given bug.
    """

    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if user.role == User.Role.ADMIN:
        return True

    if user.role == "PROJECT_MANAGER":
        return bug.project.manager_id == user.id

    if user.role in {
        "DEVELOPER",
        "TESTER",
    }:
        return bug.project.members.filter(
            user=user,
            is_active=True,
        ).exists()

    return False


def can_create_bug(user, project):
    """
    Check whether the user can create a bug for the project.
    """

    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if user.role == User.Role.ADMIN:
        return True

    if user.role == "TESTER":
        return project.members.filter(
            user=user,
            is_active=True,
        ).exists()

    return False