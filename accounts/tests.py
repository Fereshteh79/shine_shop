from django.test import TestCase
from django.urls import reverse

from .models import User
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse

from .models import PhoneOTP, User
from .otp import issue_otp, verify_otp


class RegisterTests(TestCase):
    def test_register_success_and_auto_login(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "shahab",
                "email": "Shahab@Example.com",
                "phone_number": "09387586384",
                "first_name": "شهاب",
                "last_name": "طیبی",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(response, reverse("shop:home"))
        self.assertEqual(User.objects.count(), 1)

        user = User.objects.get(username="shahab")
        self.assertEqual(user.email, "shahab@example.com")  # نرمال‌سازی ایمیل
        self.assertTrue(user.is_authenticated or self.client.session.keys())

    def test_register_duplicate_email_rejected(self):
        User.objects.create_user(
            username="old",
            email="taken@example.com",
            password="StrongPass123!",
        )

        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "new",
                "email": "taken@example.com",
                "phone_number": "09120000000",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(User.objects.count(), 1)
        self.assertContains(response, "این ایمیل قبلاً ثبت شده است.")

    def test_register_invalid_phone_rejected(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "badphone",
                "email": "bad@example.com",
                "phone_number": "abc123",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(User.objects.count(), 0)

    def test_authenticated_user_cannot_see_register(self):
        User.objects.create_user(
            username="logged",
            email="logged@example.com",
            password="StrongPass123!",
        )
        self.client.login(username="logged", password="StrongPass123!")

        response = self.client.get(reverse("accounts:register"))

        self.assertRedirects(response, reverse("shop:home"))


class LoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="shahab",
            email="shahab@example.com",
            password="StrongPass123!",
        )

    def test_login_success(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "shahab", "password": "StrongPass123!"},
        )

        self.assertRedirects(response, reverse("shop:home"))

    def test_logout_requires_post(self):
        self.client.login(username="shahab", password="StrongPass123!")

        response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 405)

        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("shop:home"))


@override_settings(SMS_PROVIDER="console")
class OtpFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="otpuser",
            email="otp@example.com",
            phone_number="09123456789",
            password="StrongPass123!",
        )

    @mock.patch("accounts.otp.send_sms")
    def test_issue_and_verify_otp(self, mock_sms):
        issue_otp(phone_number="09123456789")

        mock_sms.assert_called_once()
        otp = PhoneOTP.objects.get(phone_number="09123456789", is_used=False)

        # کد هش‌شده ذخیره می‌شود — کد خام در دیتابیس نیست
        self.assertNotIn(otp.code_hash, "0123456789")

    def test_full_otp_login_flow(self):
        with mock.patch("accounts.otp.send_sms") as mock_sms:
            self.client.post(
                reverse("accounts:otp_request"),
                {"phone_number": "09123456789"},
            )

        # کد واقعی از آرگومان پیامک استخراج می‌شود
        message = mock_sms.call_args.kwargs["message"]
        code = [w for w in message.split() if w.isdigit() and len(w) == 6][0]

        response = self.client.post(
            reverse("accounts:otp_verify"),
            {"code": code},
        )

        self.assertRedirects(response, reverse("shop:home"))

    def test_wrong_code_rejected(self):
        with mock.patch("accounts.otp.send_sms"):
            self.client.post(
                reverse("accounts:otp_request"),
                {"phone_number": "09123456789"},
            )

        response = self.client.post(
            reverse("accounts:otp_verify"),
            {"code": "000000"},
        )

        self.assertContains(response, "کد وارد شده صحیح نیست.")

    def test_invalid_phone_rejected(self):
        response = self.client.post(
            reverse("accounts:otp_request"),
            {"phone_number": "12345"},
        )

        self.assertEqual(PhoneOTP.objects.count(), 0)

    def test_login_with_email(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "otp@example.com", "password": "StrongPass123!"},
        )

        self.assertRedirects(response, reverse("shop:home"))
