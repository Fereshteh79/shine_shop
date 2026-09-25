# accounts/tests.py

import re
from datetime import timedelta
from unittest import mock

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import PhoneOTP, User
from .otp import OTPError, issue_otp, verify_otp


# ─── ثبت‌نام ────────────────────────────────────────────

class RegisterTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.register_url = reverse("accounts:register")
        cls.home_url = reverse("shop:home")

    def test_register_success(self):
        """ثبت‌نام موفق — redirect به home، یک کاربر ساخته شود،
        ایمیل نرمال‌شده ذخیره گردد و کاربر لاگین شود."""

        data = {
            "username": "shahab",
            "email": "Shahab@Example.com",
            "phone_number": "09387586384",
            "first_name": "شهاب",
            "last_name": "طیبی",
            "password1": "TestPass123",
            "password2": "TestPass123",
        }

        response = self.client.post(self.register_url, data)

        # ریدایرکت به خانه
        self.assertRedirects(response, self.home_url)

        # دقیقاً یک کاربر ساخته شده
        self.assertEqual(User.objects.count(), 1)

        # ایمیل نرمال‌شده (lowercase)
        user = User.objects.first()
        self.assertEqual(user.email, "shahab@example.com")

        # کاربر لاگین شده باشد
        self.assertIn("_auth_user_id", self.client.session)

    def test_duplicate_email_rejected(self):
        """ایمیل تکراری رد شود و تعداد کاربران ثابت بماند."""

        User.objects.create_user(
            username="existing",
            email="shahab@example.com",
            password="TestPass123",
        )

        data = {
            "username": "shahab",
            "email": "Shahab@Example.com",
            "phone_number": "09387586384",
            "first_name": "شهاب",
            "last_name": "طیبی",
            "password1": "TestPass123",
            "password2": "TestPass123",
        }

        response = self.client.post(self.register_url, data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "این ایمیل قبلاً ثبت شده است.")
        self.assertEqual(User.objects.count(), 1)

    def test_invalid_phone_rejected(self):
        """شمارهٔ نامعتبر رد شود و کاربری ساخته نشود."""

        data = {
            "username": "shahab",
            "email": "shahab@example.com",
            "phone_number": "abc123",
            "first_name": "شهاب",
            "last_name": "طیبی",
            "password1": "TestPass123",
            "password2": "TestPass123",
        }

        response = self.client.post(self.register_url, data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "شماره موبایل")
        self.assertEqual(User.objects.count(), 0)

    def test_authenticated_user_redirected(self):
        """کاربر لاگین‌شده نتواند صفحهٔ ثبت‌نام را ببیند."""

        User.objects.create_user(
            username="shahab",
            email="shahab@example.com",
            password="TestPass123",
        )
        self.client.login(username="shahab", password="TestPass123")

        response = self.client.get(self.register_url)
        self.assertRedirects(response, self.home_url)


# ─── ورود با رمز عبور ───────────────────────────────────

class LoginTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.login_url = reverse("accounts:login")
        cls.home_url = reverse("shop:home")
        cls.logout_url = reverse("accounts:logout")

        cls.user = User.objects.create_user(
            username="shahab",
            email="shahab@example.com",
            password="TestPass123",
            first_name="شهاب",
            last_name="طیبی",
        )

    def test_login_success(self):
        """ورود موفق با username و redirect به home."""

        response = self.client.post(
            self.login_url,
            {"username": "shahab", "password": "TestPass123"},
        )
        self.assertRedirects(response, self.home_url)
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_with_email(self):
        """ورود موفق با ایمیل."""

        response = self.client.post(
            self.login_url,
            {"username": "shahab@example.com", "password": "TestPass123"},
        )
        self.assertRedirects(response, self.home_url)

    def test_login_wrong_password(self):
        """ورود ناموفق با رمز اشتباه."""

        response = self.client.post(
            self.login_url,
            {"username": "shahab", "password": "WrongPass"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_requires_post(self):
        """خروج فقط با POST امکان‌پذیر باشد."""

        self.client.login(username="shahab", password="TestPass123")

        # GET نباید logout کند
        response = self.client.get(self.logout_url)
        # بسته به تنظیمات ممکن است redirect یا 405 باشد
        self.assertNotEqual(response.status_code, 200)

    def test_logout_success(self):
        """خروج موفق با POST."""
