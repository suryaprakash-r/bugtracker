from django.contrib import admin
from .models import (
    Bug,
    BugComment,
    BugAttachment,
    BugStatusHistory,
)


@admin.register(Bug)
class BugAdmin(admin.ModelAdmin):
    list_display = (
        "bug_code",
        "title",
        "project",
        "severity",
        "priority",
        "status",
        "assigned_to",
        "reporter",
        "created_at",
    )

    list_filter = (
        "status",
        "severity",
        "priority",
        "environment",
        "created_at",
    )

    search_fields = (
        "bug_code",
        "title",
        "description",
        "project__name",
        "assigned_to__username",
        "reporter__username",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "resolved_at",
        "closed_at",
    )

    ordering = ("-created_at",)


@admin.register(BugComment)
class BugCommentAdmin(admin.ModelAdmin):
    list_display = (
        "bug",
        "user",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "bug__bug_code",
        "bug__title",
        "user__username",
        "message",
    )

    ordering = ("created_at",)


@admin.register(BugAttachment)
class BugAttachmentAdmin(admin.ModelAdmin):
    list_display = (
        "bug",
        "file_name",
        "uploaded_by",
        "file_size",
        "uploaded_at",
    )

    search_fields = (
        "bug__bug_code",
        "bug__title",
        "file_name",
        "uploaded_by__username",
    )

    ordering = ("-uploaded_at",)


@admin.register(BugStatusHistory)
class BugStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "bug",
        "old_status",
        "new_status",
        "changed_by",
        "changed_at",
    )

    list_filter = (
        "old_status",
        "new_status",
        "changed_at",
    )

    search_fields = (
        "bug__bug_code",
        "bug__title",
        "changed_by__username",
        "comment",
    )

    ordering = ("-changed_at",)