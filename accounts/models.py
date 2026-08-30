from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager
from django.db import models


class UserRole(models.TextChoices):
    SUPERADMIN = "SUPERADMIN", "Super Admin"
    ADMIN = "ADMIN", "Admin"
    ENGINEER = "ENGINEER", "Engineer"


class CustomUserManager(UserManager):

    def create_superuser(self, username, email=None, password=None, **extra_fields):

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields["role"] = UserRole.SUPERADMIN

        return super().create_superuser(
            username=username,
            email=email,
            password=password,
            **extra_fields,
        )


class User(AbstractUser):

    objects = CustomUserManager()

    visible_password = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        verbose_name="Visible Password",
    )

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.ENGINEER,
        verbose_name="Role",
    )

    mobile_number = models.CharField(
        max_length=15,
        unique=True,
        verbose_name="Mobile Number",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        db_table = "users"

        ordering = ["username"]

        verbose_name = "User"

        verbose_name_plural = "Users"

    def save(self, *args, **kwargs):

        if self.is_superuser:
            self.role = UserRole.SUPERADMIN
            self.is_staff = True
        elif self.role in [UserRole.SUPERADMIN, UserRole.ADMIN]:
            self.is_staff = True
        else:
            self.is_staff = False

        super().save(*args, **kwargs)

    def __str__(self):

        return f"{self.username} ({self.get_role_display()})"
