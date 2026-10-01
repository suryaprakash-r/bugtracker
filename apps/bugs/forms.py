from django import forms

from apps.accounts.models import User
from apps.projects.models import Project

from .services import get_allowed_status_transitions
from .models import Bug, BugAttachment


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
    
class BugAssignmentForm(forms.Form):

    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
        label="Developer",
    )


    def __init__(self, *args, bug=None, **kwargs):

        super().__init__(*args, **kwargs)

        self.bug = bug

        if not bug:
            return


        # Only active Developers who are active
        # members of this project can be selected.

        self.fields["assigned_to"].queryset = (
            User.objects.filter(
                role=User.Role.DEVELOPER,
                is_active=True,
                project_memberships__project=bug.project,
                project_memberships__is_active=True,
            )
            .distinct()
            .order_by(
                "first_name",
                "last_name",
                "username",
            )
        )


        # Show the current developer as selected
        # when the bug has already been assigned.

        if bug.assigned_to_id:

            self.fields["assigned_to"].initial = (
                bug.assigned_to_id
            )


    def clean_assigned_to(self):

        developer = self.cleaned_data["assigned_to"]

        if developer.role != User.Role.DEVELOPER:

            raise forms.ValidationError(
                "Only Developers can be assigned to bugs."
            )


        if not developer.is_active:

            raise forms.ValidationError(
                "The selected Developer is inactive."
            )


        is_project_member = (
            self.bug.project.members.filter(
                user=developer,
                is_active=True,
            ).exists()
        )


        if not is_project_member:

            raise forms.ValidationError(
                "The selected Developer must be an active "
                "member of this project."
            )


        return developer
    
class BugUpdateForm(forms.ModelForm):

    class Meta:
        model = Bug

        fields = [
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


    def clean_title(self):

        title = self.cleaned_data["title"].strip()

        if len(title) < 5:
            raise forms.ValidationError(
                "Bug title must contain at least 5 characters."
            )

        return title
    
class BugStatusChangeForm(forms.Form):

    new_status = forms.ChoiceField(
        choices=[],
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
        label="New Status",
    )

    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Add an optional comment...",
                "rows": 4,
            }
        ),
        label="Comment",
    )


    def __init__(
        self,
        *args,
        bug=None,
        user=None,
        **kwargs
    ):

        super().__init__(
            *args,
            **kwargs
        )

        self.bug = bug
        self.current_user = user


        allowed_statuses = (
            get_allowed_status_transitions(
                user,
                bug,
            )
            if bug and user
            else []
        )


        self.allowed_status_values = {
            status
            for status in allowed_statuses
        }


        self.fields["new_status"].choices = [
            (
                status,
                dict(
                    Bug.Status.choices
                )[status],
            )
            for status in allowed_statuses
        ]


    def clean_new_status(self):

        new_status = self.cleaned_data[
            "new_status"
        ]


        if new_status not in self.allowed_status_values:

            raise forms.ValidationError(
                "This status transition is not allowed."
            )


        return new_status


    def clean(self):

        cleaned_data = super().clean()

        new_status = cleaned_data.get(
            "new_status"
        )

        comment = cleaned_data.get(
            "comment",
            "",
        ).strip()


        # Reopening requires a reason.

        if (
            new_status == Bug.Status.REOPENED
            and not comment
        ):

            self.add_error(
                "comment",
                "Please provide a reason for reopening the bug.",
            )


        cleaned_data["comment"] = comment

        return cleaned_data
    
class BugCommentForm(forms.Form):

    message = forms.CharField(
        label="Comment",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Write your comment...",
                "maxlength": 2000,
            }
        ),
        max_length=2000,
    )

    def clean_message(self):
        message = self.cleaned_data["message"].strip()

        if not message:
            raise forms.ValidationError(
                "Comment cannot be empty."
            )

        return message
    
    
# File attachment form with validation for file size and allowed extensions
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10 MB

class BugAttachmentForm(forms.ModelForm):
    class Meta:
        model = BugAttachment
        fields = ["file"]

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]

        if uploaded_file.size > MAX_ATTACHMENT_SIZE:
            raise forms.ValidationError(
                "File size cannot exceed 10 MB."
            )

        allowed_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            ".txt",
            ".log",
            ".zip",
            ".rar",
            ".7z",
        }

        from pathlib import Path

        extension = Path(uploaded_file.name).suffix.lower()

        if extension not in allowed_extensions:
            raise forms.ValidationError(
                "This file type is not supported."
            )

        return uploaded_file