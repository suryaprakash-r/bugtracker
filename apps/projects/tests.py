
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.projects.models import Project, ProjectMember


User = get_user_model()


class ProjectModelTests(TestCase):
    """Tests for BugTracker project data and defaults."""

    def setUp(self):
        self.manager = User.objects.create_user(
            username="project-manager",
            password="Test-Only-Password-123!",
            role="PROJECT_MANAGER",
        )

        self.project = Project.objects.create(
            name="BugTracker DevOps",
            project_key="BTDEV",
            manager=self.manager,
        )

    def test_project_defaults_to_planning(self):
        self.assertEqual(
            self.project.status,
            Project.Status.PLANNING,
        )

    def test_project_string_representation(self):
        self.assertEqual(
            str(self.project),
            "BTDEV - BugTracker DevOps",
        )

    def test_project_key_must_be_unique(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Project.objects.create(
                    name="Duplicate Project",
                    project_key="BTDEV",
                    manager=self.manager,
                )

    def test_project_member_is_active_by_default(self):
        developer = User.objects.create_user(
            username="project-developer",
            password="Test-Only-Password-123!",
            role="DEVELOPER",
        )

        membership = ProjectMember.objects.create(
            project=self.project,
            user=developer,
        )

        self.assertTrue(membership.is_active)
        self.assertEqual(membership.project, self.project)
        self.assertEqual(membership.user, developer)
        self.assertEqual(
            str(membership),
            "project-developer - BTDEV",
        )

    def test_user_cannot_be_added_to_same_project_twice(self):
        developer = User.objects.create_user(
            username="duplicate-developer",
            password="Test-Only-Password-123!",
            role="DEVELOPER",
        )

        ProjectMember.objects.create(
            project=self.project,
            user=developer,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProjectMember.objects.create(
                    project=self.project,
                    user=developer,
                )
