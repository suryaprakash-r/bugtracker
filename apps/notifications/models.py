from django.conf import settings
from django.db import models


class Notification(models.Model):

    class NotificationType(models.TextChoices):
        BUG_ASSIGNED = "BUG_ASSIGNED", "Bug Assigned"
        STATUS_CHANGED = "STATUS_CHANGED", "Status Changed"
        COMMENT_ADDED = "COMMENT_ADDED", "Comment Added"
        PROJECT_ADDED = "PROJECT_ADDED", "Added to Project"
        GENERAL = "GENERAL", "General"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    title = models.CharField(
        max_length=255,
    )

    message = models.TextField()

    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL,
    )

    bug = models.ForeignKey(
        "bugs.Bug",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )

    is_read = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient.username} - {self.title}"
    
class ActivityLog(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="activity_logs",
    )

    action = models.CharField(
        max_length=100,
    )

    description = models.TextField()

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} - {self.created_at}"