from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

from .models import Profile

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

            next_url = request.GET.get("next")

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

        profile.designation = request.POST.get(
            "designation",
            "",
        ).strip()

        profile.department = request.POST.get(
            "department",
            "",
        ).strip()

        profile.bio = request.POST.get(
            "bio",
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
    
