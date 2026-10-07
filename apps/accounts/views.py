from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.deletion import ProtectedError

from .models import User, Profile
from .forms import (
    AdminUserCreateForm,
    AdminUserUpdateForm,
)
from .permissions import Permission, role_required

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            if not user.is_active:
                messages.error(
                    request,
                    "Your account is inactive. Please contact the administrator.",
                )
                return render(request, "accounts/login.html")

            login(request, user)

            next_url = request.POST.get("next") or request.GET.get("next")

            if next_url:
                return redirect(next_url)

            return redirect("dashboard:index")

        messages.error(
            request,
            "Invalid username or password.",
        )

    return render(request, "accounts/login.html")


@login_required
def logout_view(request):
    logout(request)

    messages.success(
        request,
        "You have been logged out successfully.",
    )

    return redirect("accounts:login")

@login_required
@role_required(Permission.MANAGE_USERS)
def users_view(request):
    users = (
        User.objects
        .select_related("profile")
        .order_by("-date_joined")
    )

    search_query = request.GET.get("q", "").strip()
    role_filter = request.GET.get("role", "").strip()
    status_filter = request.GET.get("status", "").strip()

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
        )

    if role_filter in {
        User.Role.ADMIN,
        User.Role.PROJECT_MANAGER,
        User.Role.DEVELOPER,
        User.Role.TESTER,
    }:
        users = users.filter(role=role_filter)

    if status_filter == "active":
        users = users.filter(is_active=True)

    elif status_filter == "inactive":
        users = users.filter(is_active=False)

    paginator = Paginator(users, 10)

    page_number = request.GET.get("page")
    user_page = paginator.get_page(page_number)

    return render(
        request,
        "users/index.html",
        {
            "user_page": user_page,
            "search_query": search_query,
            "role_filter": role_filter,
            "status_filter": status_filter,
            "total_users": User.objects.count(),
            "active_users": User.objects.filter(is_active=True).count(),
            "inactive_users": User.objects.filter(is_active=False).count(),
        },
    )
    
@login_required
@role_required(Permission.MANAGE_USERS)
def user_create(request):

    if request.method == "POST":

        form = AdminUserCreateForm(
            request.POST,
        )

        if form.is_valid():

            user = form.save()

            messages.success(
                request,
                f'User "{user.username}" was created successfully.',
            )

            return redirect(
                "accounts:users",
            )

    else:

        form = AdminUserCreateForm()

    return render(
        request,
        "users/create.html",
        {
            "form": form,
        },
    )

@login_required
@role_required(Permission.MANAGE_USERS)
def user_edit(request, user_id):

    user = get_object_or_404(
        User.objects.select_related("profile"),
        id=user_id,
    )

    if request.method == "POST":

        form = AdminUserUpdateForm(
            request.POST,
            instance=user,
        )

        if form.is_valid():

            updated_user = form.save()

            messages.success(
                request,
                f'User "{updated_user.username}" was updated successfully.',
            )

            return redirect(
                "accounts:users",
            )

    else:

        form = AdminUserUpdateForm(
            instance=user,
        )

    return render(
        request,
        "users/edit.html",
        {
            "form": form,
            "user_account": user,
        },
    )

@login_required
@role_required(Permission.MANAGE_USERS)
def user_toggle_status(request, user_id):

    if request.method != "POST":
        raise PermissionDenied

    user = get_object_or_404(
        User,
        id=user_id,
    )

    if user.id == request.user.id:
        messages.error(
            request,
            "You cannot deactivate your own account.",
        )
        return redirect("accounts:users")

    user.is_active = not user.is_active

    user.save(
        update_fields=["is_active"],
    )

    if user.is_active:
        messages.success(
            request,
            f'User "{user.username}" was activated successfully.',
        )
    else:
        messages.success(
            request,
            f'User "{user.username}" was deactivated successfully.',
        )

    return redirect("accounts:users")

@login_required
@role_required(Permission.MANAGE_USERS)
def user_delete(request, user_id):
    if request.method != "POST":
        raise PermissionDenied

    user = get_object_or_404(User, id=user_id)

    if user.id == request.user.id:
        messages.error(request, "You cannot delete your own account.")
        return redirect("accounts:users")

    username = user.username

    try:
        user.delete()
    except ProtectedError:
        messages.error(
            request,
            f'User "{username}" cannot be deleted because they are still linked '
            "to protected project or bug records. Deactivate the account instead "
            "or remove/reassign those records first."
        )
    else:
        messages.success(
            request,
            f'User "{username}" was deleted successfully.'
        )

    return redirect("accounts:users")

@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(
        user=request.user,
    )

    return render(
        request,
        "accounts/profile.html",
        {
            "profile": profile,
        },
    )
    

@login_required
def profile_edit(request):
    profile, created = Profile.objects.get_or_create(
        user=request.user,
    )

    if request.method == "POST":

        profile.phone = request.POST.get(
            "phone",
            "",
        ).strip()

        profile.bio = request.POST.get(
            "bio",
            "",
        ).strip()

        if request.user.role == "ADMIN":
            profile.designation = request.POST.get(
                "designation",
                "",
            ).strip()

            profile.department = request.POST.get(
                "department",
                "",
            ).strip()

        if request.FILES.get("profile_image"):
            profile.profile_image = request.FILES[
                "profile_image"
            ]

        profile.save()

        messages.success(
            request,
            "Profile updated successfully.",
        )

        return redirect("accounts:profile")

    return render(
        request,
        "accounts/profile_edit.html",
        {
            "profile": profile,
            "is_admin": request.user.role == "ADMIN",
        },
    )

@login_required
def password_change(request):

    if request.method == "POST":

        form = PasswordChangeForm(
            request.user,
            request.POST,
        )

        if form.is_valid():

            user = form.save()

            update_session_auth_hash(
                request,
                user,
            )

            messages.success(
                request,
                "Your password was changed successfully.",
            )

            return redirect(
                "accounts:profile",
            )

    else:

        form = PasswordChangeForm(
            request.user,
        )

    return render(
        request,
        "accounts/password_change.html",
        {
            "form": form,
        },
    )
    
