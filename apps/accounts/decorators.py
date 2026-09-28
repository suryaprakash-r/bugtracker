from functools import wraps

from django.core.exceptions import PermissionDenied


def roles_required(*roles):
    """
    Allow access only when the authenticated user's role
    matches one of the supplied roles.
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