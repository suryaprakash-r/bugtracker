from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.bugs.models import Bug, BugComment, BugStatusHistory
from apps.projects.models import Project


User = get_user_model()


class BugModelTests(TestCase):
    """Tests for BugTracker bug management models."""

    def setUp(self):
        self.manager = User.objects.create_user(
            username="bug-project-manager",
            password="Test-Only-Password-123!",
            role="PROJECT_MANAGER",
        )

        self.reporter = User.objects.create_user(
            username="bug-tester",
            password="Test-Only-Password-123!",
            role="TESTER",
        )

        self.developer = User.objects.create_user(
            username="bug-developer",
            password="Test-Only-Password-123!",
            role="DEVELOPER",
        )

        self.project = Project.objects.create(
            name="Bug Management Test Project",
            project_key="BUGTEST",
            manager=self.manager,
        )

        self.bug = Bug.objects.create(
            project=self.project,
            bug_code="BUGTEST-001",
            title="Login page fails",
            description="The login page fails with valid credentials.",
            reporter=self.reporter,
        )

    def test_bug_has_expected_default_values(self):
        self.assertEqual(self.bug.status, Bug.Status.NEW)
        self.assertEqual(self.bug.severity, Bug.Severity.MEDIUM)
        self.assertEqual(self.bug.priority, Bug.Priority.MEDIUM)
        self.assertEqual(
            self.bug.environment,
            Bug.Environment.DEVELOPMENT,
        )
        self.assertIsNone(self.bug.assigned_to)

    def test_bug_string_representation(self):
        self.assertEqual(
            str(self.bug),
            "BUGTEST-001 - Login page fails",
        )

    def test_bug_code_must_be_unique(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Bug.objects.create(
                    project=self.project,
                    bug_code="BUGTEST-001",
                    title="Duplicate bug",
                    description="Testing duplicate bug codes.",
                    reporter=self.reporter,
                )

    def test_bug_can_be_assigned_to_a_developer(self):
        self.bug.assigned_to = self.developer
        self.bug.save(update_fields=["assigned_to", "updated_at"])

        self.bug.refresh_from_db()

        self.assertEqual(self.bug.assigned_to, self.developer)

    def test_comment_is_linked_to_bug_and_user(self):
        comment = BugComment.objects.create(
            bug=self.bug,
            user=self.developer,
            message="Investigating the login failure.",
        )

        self.assertEqual(comment.bug, self.bug)
        self.assertEqual(comment.user, self.developer)
        self.assertEqual(self.bug.comments.count(), 1)
        self.assertEqual(
            self.bug.comments.first().message,
            "Investigating the login failure.",
        )

    def test_status_history_can_be_recorded_for_a_bug(self):
        history = BugStatusHistory.objects.create(
            bug=self.bug,
            old_status=Bug.Status.NEW,
            new_status=Bug.Status.IN_PROGRESS,
            changed_by=self.developer,
            comment="Started investigating the issue.",
        )

        self.assertEqual(history.bug, self.bug)
        self.assertEqual(history.old_status, Bug.Status.NEW)
        self.assertEqual(
            history.new_status,
            Bug.Status.IN_PROGRESS,
        )
        self.assertEqual(history.changed_by, self.developer)
        self.assertEqual(self.bug.status_history.count(), 1)