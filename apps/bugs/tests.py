from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from django.urls import reverse
from apps.accounts.permissions import (
    can_assign_bug,
    can_update_bug,
    can_view_bug,
)
from apps.bugs.forms import BugStatusChangeForm
from apps.bugs.services import get_allowed_status_transitions
from apps.projects.models import Project, ProjectMember

from apps.bugs.models import Bug, BugComment, BugStatusHistory

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

class BugAuthorizationAndWorkflowTests(TestCase):
    """Tests for bug access permissions and status transitions."""

    def setUp(self):
        self.manager = User.objects.create_user(
            username="rbac-manager",
            password="Test-Only-Password-123!",
            role="PROJECT_MANAGER",
        )

        self.other_manager = User.objects.create_user(
            username="rbac-other-manager",
            password="Test-Only-Password-123!",
            role="PROJECT_MANAGER",
        )

        self.admin = User.objects.create_user(
            username="rbac-admin",
            password="Test-Only-Password-123!",
            role="ADMIN",
        )

        self.tester = User.objects.create_user(
            username="rbac-tester",
            password="Test-Only-Password-123!",
            role="TESTER",
        )

        self.developer = User.objects.create_user(
            username="rbac-developer",
            password="Test-Only-Password-123!",
            role="DEVELOPER",
        )

        self.other_developer = User.objects.create_user(
            username="rbac-other-developer",
            password="Test-Only-Password-123!",
            role="DEVELOPER",
        )

        self.outsider = User.objects.create_user(
            username="rbac-outsider",
            password="Test-Only-Password-123!",
            role="TESTER",
        )

        self.project = Project.objects.create(
            name="RBAC Test Project",
            project_key="RBAC",
            manager=self.manager,
        )

        self.tester_membership = ProjectMember.objects.create(
            project=self.project,
            user=self.tester,
        )

        ProjectMember.objects.create(
            project=self.project,
            user=self.developer,
        )

        ProjectMember.objects.create(
            project=self.project,
            user=self.other_developer,
        )

        self.bug = Bug.objects.create(
            project=self.project,
            bug_code="RBAC-001",
            title="Login authentication failure",
            description="Login fails under specific conditions.",
            reporter=self.tester,
        )

    def test_bug_is_visible_to_manager_and_active_members(self):
        self.assertTrue(can_view_bug(self.manager, self.bug))
        self.assertTrue(can_view_bug(self.developer, self.bug))
        self.assertTrue(can_view_bug(self.tester, self.bug))
        self.assertFalse(
            can_view_bug(self.other_manager, self.bug)
        )
        self.assertFalse(can_view_bug(self.outsider, self.bug))

    def test_inactive_project_member_cannot_view_bug(self):
        self.tester_membership.is_active = False
        self.tester_membership.save(update_fields=["is_active"])

        self.assertFalse(can_view_bug(self.tester, self.bug))

    def test_only_assigned_developer_can_update_bug(self):
        self.bug.assigned_to = self.developer
        self.bug.save(update_fields=["assigned_to", "updated_at"])

        self.assertTrue(can_update_bug(self.developer, self.bug))
        self.assertFalse(
            can_update_bug(self.other_developer, self.bug)
        )
        self.assertFalse(can_update_bug(self.tester, self.bug))

    def test_assignment_requires_project_manager_or_admin(self):
        self.assertTrue(can_assign_bug(self.manager, self.bug))
        self.assertTrue(can_assign_bug(self.admin, self.bug))
        self.assertFalse(
            can_assign_bug(self.other_manager, self.bug)
        )
        self.assertFalse(can_assign_bug(self.developer, self.bug))
        self.assertFalse(can_assign_bug(self.tester, self.bug))

    def test_bug_detail_denies_user_outside_project(self):
        self.client.force_login(self.outsider)

        response = self.client.get(
            reverse("bugs:detail", args=[self.bug.pk])
        )

        self.assertEqual(response.status_code, 403)

    def test_tester_cannot_access_assignment_endpoint(self):
        self.client.force_login(self.tester)

        response = self.client.get(
            reverse("bugs:assign", args=[self.bug.pk])
        )

        self.assertEqual(response.status_code, 403)

    def test_unassigned_developer_cannot_update_bug(self):
        self.client.force_login(self.developer)

        response = self.client.get(
            reverse("bugs:update", args=[self.bug.pk])
        )

        self.assertEqual(response.status_code, 403)

    def test_assigned_developer_can_progress_assigned_bug(self):
        self.bug.status = Bug.Status.ASSIGNED
        self.bug.assigned_to = self.developer
        self.bug.save(
            update_fields=["status", "assigned_to", "updated_at"]
        )

        allowed = get_allowed_status_transitions(
            self.developer,
            self.bug,
        )

        self.assertEqual(
            allowed,
            [Bug.Status.IN_PROGRESS],
        )

    def test_tester_can_test_resolved_bug_only_while_active(self):
        self.bug.status = Bug.Status.RESOLVED
        self.bug.save(update_fields=["status", "updated_at"])

        allowed = get_allowed_status_transitions(
            self.tester,
            self.bug,
        )

        self.assertIn(Bug.Status.TESTING, allowed)

        self.tester_membership.is_active = False
        self.tester_membership.save(update_fields=["is_active"])

        allowed = get_allowed_status_transitions(
            self.tester,
            self.bug,
        )

        self.assertEqual(allowed, [])

    def test_form_rejects_invalid_status_transition(self):
        self.bug.status = Bug.Status.IN_PROGRESS
        self.bug.assigned_to = self.developer
        self.bug.save(
            update_fields=["status", "assigned_to", "updated_at"]
        )

        form = BugStatusChangeForm(
            data={
                "new_status": Bug.Status.CLOSED,
                "comment": "",
            },
            bug=self.bug,
            user=self.developer,
        )

        self.assertFalse(form.is_valid())

    def test_reopening_bug_requires_a_reason(self):
        self.bug.status = Bug.Status.TESTING
        self.bug.save(update_fields=["status", "updated_at"])

        form = BugStatusChangeForm(
            data={
                "new_status": Bug.Status.REOPENED,
                "comment": "",
            },
            bug=self.bug,
            user=self.tester,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("comment", form.errors)

        valid_form = BugStatusChangeForm(
            data={
                "new_status": Bug.Status.REOPENED,
                "comment": "The same issue is reproducible again.",
            },
            bug=self.bug,
            user=self.tester,
        )

        self.assertTrue(
            valid_form.is_valid(),
            valid_form.errors,
        )
