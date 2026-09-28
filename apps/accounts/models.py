from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        PROJECT_MANAGER = "PROJECT_MANAGER", "Project Manager"
        DEVELOPER = "DEVELOPER", "Developer"
        TESTER = "TESTER", "Tester"

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.TESTER,
    )

    def __str__(self):
        return self.username
    
    
class Profile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    profile_image = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True,
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
    )

    designation = models.CharField(
        max_length=100,
        blank=True,
    )

    department = models.CharField(
        max_length=100,
        blank=True,
    )

    bio = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"