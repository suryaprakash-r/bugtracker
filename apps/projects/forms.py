from django import forms

from apps.accounts.models import User

from .models import Project


class ProjectForm(forms.ModelForm):

    class Meta:
        model = Project

        fields = [
            "name",
            "project_key",
            "description",
            "manager",
            "status",
            "start_date",
            "end_date",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter project name",
                }
            ),

            "project_key": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: BT",
                    "maxlength": 10,
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter project description",
                    "rows": 4,
                }
            ),

            "manager": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "start_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "end_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
        }


    def __init__(self, *args, user=None, **kwargs):

        super().__init__(*args, **kwargs)

        self.current_user = user

        self.fields["manager"].queryset = (
            User.objects.filter(
                role=User.Role.PROJECT_MANAGER,
                is_active=True,
            )
            .order_by(
                "first_name",
                "last_name",
                "username",
            )
        )


        # Project Manager can only manage themselves
        # as the manager of their projects.

        if (
            user
            and not user.is_superuser
            and user.role == User.Role.PROJECT_MANAGER
        ):

            self.fields["manager"].initial = user

            self.fields["manager"].disabled = True


    def clean_project_key(self):

        project_key = self.cleaned_data["project_key"]

        project_key = project_key.strip().upper()

        if not project_key:

            raise forms.ValidationError(
                "Project key is required."
            )

        if " " in project_key:

            raise forms.ValidationError(
                "Project key cannot contain spaces."
            )

        return project_key


    def clean(self):

        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if (
            start_date
            and end_date
            and end_date < start_date
        ):

            self.add_error(
                "end_date",
                "End date cannot be earlier than the start date.",
            )

        return cleaned_data
    
class ProjectMemberForm(forms.Form):

    user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
        label="Select Member",
    )


    def __init__(self, *args, project=None, **kwargs):

        super().__init__(*args, **kwargs)

        self.project = project

        active_member_ids = (
            project.members
            .filter(is_active=True)
            .values_list(
                "user_id",
                flat=True,
            )
        )

        self.fields["user"].queryset = (
            User.objects.filter(
                role__in=[
                    User.Role.DEVELOPER,
                    User.Role.TESTER,
                ],
                is_active=True,
            )
            .exclude(
                id__in=active_member_ids
            )
            .order_by(
                "first_name",
                "last_name",
                "username",
            )
        )


    def clean_user(self):

        user = self.cleaned_data["user"]

        existing_membership = (
            self.project.members
            .filter(user=user)
            .first()
        )

        if existing_membership:

            if existing_membership.is_active:

                raise forms.ValidationError(
                    "This user is already an active member of the project."
                )

            raise forms.ValidationError(
                "This user already has an inactive membership. "
                "Reactivate the existing membership instead."
            )

        return user