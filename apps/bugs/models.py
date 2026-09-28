from django.conf import settings
from django.db import models


class Bug(models.Model):

    class Severity(models.TextChoices):
        CRITICAL = "CRITICAL", "Critical"
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"

    class Priority(models.TextChoices):
        URGENT = "URGENT", "Urgent"
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        ASSIGNED = "ASSIGNED", "Assigned"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"
        TESTING = "TESTING", "Testing"
        CLOSED = "CLOSED", "Closed"
        REOPENED = "REOPENED", "Reopened"

    class Environment(models.TextChoices):
        DEVELOPMENT = "DEVELOPMENT", "Development"
        STAGING = "STAGING", "Staging"
        PRODUCTION = "PRODUCTION", "Production"

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="bugs",
    )

    bug_code = models.CharField(
        max_length=30,
        unique=True,
    )

    title = models.CharField(
        max_length=255,
    )

    description = models.TextField()

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reported_bugs",
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_bugs",
    )

    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.MEDIUM,
    )

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )

    environment = models.CharField(
        max_length=20,
        choices=Environment.choices,
        default=Environment.DEVELOPMENT,
    )

    browser = models.CharField(
        max_length=100,
        blank=True,
    )

    operating_system = models.CharField(
        max_length=100,
        blank=True,
    )

    steps_to_reproduce = models.TextField(
        blank=True,
    )

    expected_result = models.TextField(
        blank=True,
    )

    actual_result = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    closed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.bug_code} - {self.title}"
    
class BugComment(models.Model):

    bug = models.ForeignKey(
        Bug,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bug_comments",
    )

    message = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.user.username} on {self.bug.bug_code}"
    
class BugAttachment(models.Model):

    bug = models.ForeignKey(
        Bug,
        on_delete=models.CASCADE,
        related_name="attachments",
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bug_attachments",
    )

    file = models.FileField(
        upload_to="bugs/attachments/",
    )

    file_name = models.CharField(
        max_length=255,
        blank=True,
    )

    file_size = models.PositiveBigIntegerField(
        null=True,
        blank=True,
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return self.file_name or self.file.name
    
class BugStatusHistory(models.Model):

    bug = models.ForeignKey(
        Bug,
        on_delete=models.CASCADE,
        related_name="status_history",
    )

    old_status = models.CharField(
        max_length=20,
        choices=Bug.Status.choices,
        blank=True,
    )

    new_status = models.CharField(
        max_length=20,
        choices=Bug.Status.choices,
    )

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bug_status_changes",
    )

    comment = models.TextField(
        blank=True,
    )

    changed_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.bug.bug_code}: {self.old_status} → {self.new_status}"
    
