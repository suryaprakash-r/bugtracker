from django import forms

from apps.accounts.models import User
from apps.projects.models import Project

from .models import Bug


class BugCreateForm(forms.ModelForm):

    class Meta:
        model = Bug

        fields = [
            "project",
            "title",
            "description",
            "severity",
            "priority",
            "environment",
            "browser",
            "operating_system",
            "steps_to_reproduce",
            "expected_result",
            "actual_result",
        ]

        widgets = {
            "project": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter bug title",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Describe the bug...",
                    "rows": 5,
                }
            ),

            "severity": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "priority": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "environment": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "browser": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: Chrome 140",
                }
            ),

            "operating_system": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: Windows 11",
                }
            ),

            "steps_to_reproduce": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Step 1...\nStep 2...\nStep 3...",
                    "rows": 5,
                }
            ),

            "expected_result": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "What should happen?",
                    "rows": 4,
                }
            ),

            "actual_result": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "What actually happened?",
                    "rows": 4,
                }
            ),
        }


    def __init__(self, *args, user=None, **kwargs):

        super().__init__(*args, **kwargs)

        self.current_user = user

        if not user:
            self.fields["project"].queryset = Project.objects.none()
            return


        # -------------------------------------------------
        # Project visibility
        # -------------------------------------------------

        if user.is_superuser or user.role == User.Role.ADMIN:

            projects = Project.objects.all()

        elif user.role == User.Role.TESTER:

            projects = Project.objects.filter(
                members__user=user,
                members__is_active=True,
            ).distinct()

        else:

            projects = Project.objects.none()


        self.fields["project"].queryset = (
            projects
            .select_related("manager")
            .order_by("name")
        )


    def clean_project(self):

        project = self.cleaned_data["project"]

        user = self.current_user

        if user.is_superuser or user.role == User.Role.ADMIN:
            return project


        if user.role == User.Role.TESTER:

            is_member = project.members.filter(
                user=user,
                is_active=True,
            ).exists()

            if not is_member:

                raise forms.ValidationError(
                    "You can only create bugs for projects "
                    "where you are an active member."
                )

            return project


        raise forms.ValidationError(
            "You do not have permission to create bugs for this project."
        )


    def clean_title(self):

        title = self.cleaned_data["title"].strip()

        if len(title) < 5:

            raise forms.ValidationError(
                "Bug title must contain at least 5 characters."
            )

        return title