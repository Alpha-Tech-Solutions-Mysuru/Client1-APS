from django.test import TestCase
from django.urls import reverse

from .models import User
from .models import UserRole


class LoginViewTests(TestCase):

    def test_admin_login_accepts_admin_user(self):

        User.objects.create_user(
            username="admin1",
            password="pass1234",
            role=UserRole.ADMIN,
            mobile_number="9111111111",
        )

        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "admin1",
                "password": "pass1234",
            },
        )

        self.assertRedirects(response, reverse("ups:dashboard"))

    def test_admin_login_accepts_superadmin_user(self):

        User.objects.create_superuser(
            username="super1",
            password="pass1234",
            email="super1@example.com",
        )

        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "super1",
                "password": "pass1234",
            },
        )

        self.assertRedirects(response, reverse("ups:dashboard"))
