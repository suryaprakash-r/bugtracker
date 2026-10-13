
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class AccountAuthenticationTests(TestCase):
    """Tests for the BugTracker account authentication flow."""

    def setUp(self):
        self.password = "Test-Only-Password-123!"
        self.user = User.objects.create_user(
            username="ci-developer",
            email="ci-developer@example.com",
            password=self.password,
            role="DEVELOPER",
        )

    def test_user_password_is_stored_as_a_hash(self):
        """The stored password must not be plain text."""
        self.assertNotEqual(self.user.password, self.password)
        self.assertTrue(self.user.check_password(self.password))

    def test_login_page_loads_successfully(self):
        """The login page should return HTTP 200."""
        response = self.client.get(reverse("accounts:login"))

        self.assertEqual(response.status_code, 200)

    def test_valid_credentials_log_user_in(self):
        """Valid credentials should authenticate the user."""
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": self.user.username,
                "password": self.password,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            str(self.client.session.get("_auth_user_id")),
            str(self.user.pk),
        )

    def test_invalid_password_does_not_log_user_in(self):
        """An incorrect password must not authenticate the user."""
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": self.user.username,
                "password": "Incorrect-Password-123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
