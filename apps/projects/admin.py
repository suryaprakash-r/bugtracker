from django.contrib import admin
from .models import Project, ProjectMember


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "project_key",
        "manager",
        "status",
        "start_date",
        "end_date",
        "created_at",
    )

    list_filter = (
        "status",
        "start_date",
        "end_date",
    )

    search_fields = (
        "name",
        "project_key",
        "description",
        "manager__username",
    )

    ordering = ("-created_at",)


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "user",
        "is_active",
        "joined_at",
    )

    list_filter = (
        "is_active",
        "joined_at",
    )

    search_fields = (
        "project__name",
        "project__project_key",
        "user__username",
        "user__email",
    )