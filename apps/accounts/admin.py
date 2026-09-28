from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin    
from .models import User, Profile


@admin.register(User)
class UserAdmin(BaseUserAdmin):

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "is_staff",
    )

    list_filter = (
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "BugTracker Role",
            {
                "fields": (
                    "role",
                ),
            },
        ),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "BugTracker Role",
            {
                "fields": (
                    "role",
                ),
            },
        ),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "designation",
        "department",
        "phone",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "designation",
        "department",
    )

    list_filter = (
        "department",
        "designation",
    )