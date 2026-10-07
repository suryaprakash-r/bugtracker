from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User, Profile


class AdminUserCreateForm(UserCreationForm):
    """
    Form used by administrators to create a new BugTracker user.
    """

    phone = forms.CharField(
        required=False,
        max_length=20,
    )

    designation = forms.CharField(
        required=False,
        max_length=100,
    )

    department = forms.CharField(
        required=False,
        max_length=100,
    )

    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
            }
        ),
    )

    class Meta:
        model = User

        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "password1",
            "password2",
            "phone",
            "designation",
            "department",
            "bio",
        )

    def save(self, commit=True):
        user = super().save(commit=False)

        if commit:
            user.is_active = True
            user.save()

            Profile.objects.create(
                user=user,
                phone=self.cleaned_data.get("phone", ""),
                designation=self.cleaned_data.get(
                    "designation",
                    "",
                ),
                department=self.cleaned_data.get(
                    "department",
                    "",
                ),
                bio=self.cleaned_data.get(
                    "bio",
                    "",
                ),
            )

        return user


class AdminUserUpdateForm(forms.ModelForm):
    """
    Form used by administrators to update an existing user
    and their profile information.
    """

    phone = forms.CharField(
        required=False,
        max_length=20,
    )

    designation = forms.CharField(
        required=False,
        max_length=100,
    )

    department = forms.CharField(
        required=False,
        max_length=100,
    )

    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
            }
        ),
    )

    class Meta:
        model = User

        fields = (
            "first_name",
            "last_name",
            "email",
            "role",
            "phone",
            "designation",
            "department",
            "bio",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        profile = getattr(
            self.instance,
            "profile",
            None,
        )

        if profile:
            self.fields["phone"].initial = profile.phone
            self.fields["designation"].initial = profile.designation
            self.fields["department"].initial = profile.department
            self.fields["bio"].initial = profile.bio

    def save(self, commit=True):
        user = super().save(commit=commit)

        profile, _ = Profile.objects.get_or_create(
            user=user,
        )

        profile.phone = self.cleaned_data.get(
            "phone",
            "",
        )

        profile.designation = self.cleaned_data.get(
            "designation",
            "",
        )

        profile.department = self.cleaned_data.get(
            "department",
            "",
        )

        profile.bio = self.cleaned_data.get(
            "bio",
            "",
        )

        profile.save()

        return user