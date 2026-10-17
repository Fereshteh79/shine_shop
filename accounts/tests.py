# accounts/tests.py
"""
تست‌های اپ accounts — پروژه Shine Gallery

اجرا:
    python manage.py test accounts -v 2
"""

import re
from datetime import timedelta
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import PhoneOTP, Profile

User = get_user_model()

# ═══════════════════════════════════════════════════════════════
#  پیکربندی تست‌ها
#  اگر نامی در پروژه‌ات متفاوت است، فقط همین بخش را عوض کن.
# ═══════════════════════════════════════════════════════════════

# نام فیلد «شماره موبایل» در OtpRequestForm
OTP_PHONE_FIELD = "phone_number"

# نام فیلد «کد» در OtpVerifyForm
OTP_CODE_FIELD = "code"

# مسیر تابع ارسال پیامک — برای mock کردن.
#   from .sms import send_otp_sms        → "accounts.views.send_otp_sms"
#   from . import sms; sms.send_otp(...) → "accounts.sms.send_otp"
OTP_SENDER_PATH = "accounts.views.send_otp_sms"

PASSWORD = "Shine@12345"
NEW_PASSWORD = "Shine@67890"
PHONE = "09387586384"
PHONE_ALT = "09381112233"
PHONE_FA = "۰۹۳۸۷۵۸۶۳۸۴"


# ═══════════════════════════════════════════════════════════════
#  ابزارهای کمکی
# ═══════════════════════════════════════════════════════════════

def make_user(**overrides):
    data = {
        "email": "shahab@example.com",
        "phone_number": PHONE,
        "password": PASSWORD,
    }
    data.update(overrides)
    return User.objects.create_user(**data)



def extract_otp_code(sender_mock):
    """کد عددی را از آرگومان‌های تابع ارسال پیامک بیرون می‌کشد."""
    if not sender_mock.call_args:
        return None
    values = list(sender_mock.call_args.args) + list(sender_mock.call_args.kwargs.values())
    for value in values:
        if isinstance(value, str) and re.fullmatch(r"\d{4,8}", value.strip()):
            return value.strip()
    return None


# ═══════════════════════════════════════════════════════════════
#  ۱) مدل User
# ═══════════════════════════════════════════════════════════════

class UserModelTests(TestCase):

    def test_clean_lowercases_email(self):
        """clean() ایمیل را کوچک و trim می‌کند."""
        user = User(username="a", email="  Shahab@Example.COM  ")
        user.clean()
        self.assertEqual(user.email, "shahab@example.com")

    def test_clean_converts_persian_digits_in_phone(self):
        """clean() اعداد فارسی شماره موبایل را به لاتین تبدیل می‌کند."""
        user = User(username="a", phone_number="۰۹۳۸۷۵۸۶۳۸۴")
        user.clean()
        self.assertEqual(user.phone_number, "09387586384")

    def test_phone_number_is_optional(self):
        """کاربر بدون شماره موبایل قابل ساخت است."""
        user = User.objects.create_user(
            username="nophone", email="n@example.com", password=PASSWORD
        )
        self.assertIsNone(user.phone_number)

    def test_email_cannot_be_duplicated(self):
        """ایمیل تکراری در سطح دیتابیس رد می‌شود."""
        make_user()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user(
                    username="other", email="shahab@example.com", password=PASSWORD
                )

    def test_email_is_nullable(self):
        """ایمیل باید NULL‌پذیر باشد (لازمهٔ ثبت‌نام OTP بدون ایمیل)."""
        field = User._meta.get_field("email")
        self.assertTrue(field.null, "فیلد email باید null=True باشد")
        self.assertTrue(field.blank, "فیلد email باید blank=True باشد")

    def test_two_users_without_email_can_coexist(self):
        """
        رگرسیون باگ مهم:
        اگر کاربر OTP با create_user(email=None) ساخته شود، جنگو
        رشتهٔ خالی («») ذخیره می‌کند و کاربر دوم IntegrityError می‌گیرد.
        راه درست، ساختن مستقیم User(...) با email=None است.
        """
        u1 = User(username="otp1", phone_number="09380000001", email=None)
        u1.set_unusable_password()
        u1.save()

        u2 = User(username="otp2", phone_number="09380000002", email=None)
        u2.set_unusable_password()
        u2.save()

        self.assertIsNone(u1.email)
        self.assertIsNone(u2.email)
        self.assertEqual(User.objects.filter(email__isnull=True).count(), 2)


# ═══════════════════════════════════════════════════════════════
#  ۲) مدل Profile
# ═══════════════════════════════════════════════════════════════

class ProfileModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = make_user(first_name="شهاب", last_name="طیبی")

    def test_profile_is_created_by_signal(self):
        """سیگنال post_save باید خودکار Profile بسازد."""
        self.assertTrue(Profile.objects.filter(user=self.user).exists())
        self.assertEqual(self.user.profile.pk, Profile.objects.get(user=self.user).pk)

    def test_profile_str(self):
        self.assertIn(self.user.username, str(self.user.profile))

    def test_full_name_contains_user_names(self):
        full_name = self.user.profile.full_name
        self.assertIn("شهاب", full_name)
        self.assertIn("طیبی", full_name)

    def test_has_avatar_is_false_without_avatar(self):
        self.assertFalse(self.user.profile.has_avatar)


# ═══════════════════════════════════════════════════════════════
#  ۳) ثبت‌نام
# ═══════════════════════════════════════════════════════════════

class RegisterTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("accounts:register")
        cls.home_url = reverse("shop:home")

    def valid_data(self, **overrides):
        data = {
            "username": "shahab",
            "email": "Shahab@Example.com",
            "phone_number": PHONE,
            "first_name": "شهاب",
            "last_name": "طیبی",
            "password1": PASSWORD,
            "password2": PASSWORD,
        }
        data.update(overrides)
        return data

    # ── مسیر خوش‌بینانه ──────────────────────────────────────

    def test_register_success(self):
        """ثبت‌نام موفق: redirect به خانه + ساخته‌شدن کاربر + لاگین شدن."""
        response = self.client.post(self.url, self.valid_data())

        self.assertRedirects(response, self.home_url)
        self.assertEqual(User.objects.count(), 1)
        self.assertIn("_auth_user_id", self.client.session)

    def test_register_lowercases_email(self):
        """ایمیل با حروف بزرگ، lowercase ذخیره شود."""
        self.client.post(self.url, self.valid_data(email="Shahab@Example.com"))
        self.assertEqual(User.objects.get().email, "shahab@example.com")

    def test_register_normalizes_persian_phone_digits(self):
        """شماره با اعداد فارسی، به شکل لاتین ذخیره شود."""
        self.client.post(self.url, self.valid_data(phone_number=PHONE_FA))
        self.assertEqual(User.objects.get().phone_number, PHONE)

    def test_register_creates_profile(self):
        """بعد از ثبت‌نام، Profile کاربر باید ساخته شده باشد."""
        self.client.post(self.url, self.valid_data())
        self.assertTrue(Profile.objects.filter(user=User.objects.get()).exists())

    # ── مسیرهای خطا ──────────────────────────────────────────

    def test_duplicate_email_rejected(self):
        """ایمیل تکراری: فرم خطا بدهد و کاربر دومی ساخته نشود."""
        make_user(username="existing", email="shahab@example.com")

        response = self.client.post(self.url, self.valid_data())

        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_duplicate_phone_rejected(self):
        """شماره تکراری: فرم خطا بدهد و کاربر دومی ساخته نشود."""
        make_user(username="existing")

        response = self.client.post(self.url, self.valid_data())

        self.assertEqual(response.status_code, 200)
        self.assertIn("phone_number", response.context["form"].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_duplicate_username_rejected(self):
        make_user(username="shahab", email="other@example.com", phone_number=PHONE_ALT)

        response = self.client.post(self.url, self.valid_data())

        self.assertEqual(response.status_code, 200)
        self.assertIn("username", response.context["form"].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_invalid_phone_rejected(self):
        """شماره نامعتبر (حروف) رد شود."""
        response = self.client.post(self.url, self.valid_data(phone_number="abc123"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("phone_number", response.context["form"].errors)
        self.assertEqual(User.objects.count(), 0)

    def test_short_phone_rejected(self):
        response = self.client.post(self.url, self.valid_data(phone_number="0912"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("phone_number", response.context["form"].errors)
        self.assertEqual(User.objects.count(), 0)

    def test_password_mismatch_rejected(self):
        response = self.client.post(
            self.url, self.valid_data(password2="TotallyDifferent@999")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 0)

    def test_authenticated_user_is_redirected(self):
        """کاربر لاگین‌شده نباید صفحهٔ ثبت‌نام را ببیند."""
        make_user()
        self.client.login(username="shahab", password=PASSWORD)

        response = self.client.get(self.url)

        self.assertRedirects(response, self.home_url)


# ═══════════════════════════════════════════════════════════════
#  ۴) ورود با رمز عبور
# ═══════════════════════════════════════════════════════════════

class LoginTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("accounts:login")
        cls.home_url = reverse("shop:home")
        cls.user = make_user()

    def test_login_with_username(self):
        response = self.client.post(
            self.url, {"username": "shahab", "password": PASSWORD}
        )
        self.assertRedirects(response, self.home_url)
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_with_email(self):
        response = self.client.post(
            self.url, {"username": "shahab@example.com", "password": PASSWORD}
        )
        self.assertRedirects(response, self.home_url)
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_with_email_is_case_insensitive(self):
        response = self.client.post(
            self.url, {"username": "Shahab@Example.COM", "password": PASSWORD}
        )
        self.assertRedirects(response, self.home_url)

    def test_login_with_phone(self):
        response = self.client.post(
            self.url, {"username": PHONE, "password": PASSWORD}
        )
        self.assertRedirects(response, self.home_url)

    def test_login_with_persian_phone_digits(self):
        """ورود با اعداد فارسی — نیاز به نرمال‌سازی در backends.py دارد."""
        response = self.client.post(
            self.url, {"username": PHONE_FA, "password": PASSWORD}
        )
        self.assertRedirects(response, self.home_url)

    def test_login_wrong_password(self):
        response = self.client.post(
            self.url, {"username": "shahab", "password": "WrongPass@999"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_unknown_user(self):
        response = self.client.post(
            self.url, {"username": "ghost", "password": PASSWORD}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_inactive_user_cannot_login(self):
        """کاربر بن‌شده (is_active=False) نباید وارد شود."""
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        response = self.client.post(
            self.url, {"username": "shahab", "password": PASSWORD}
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)


# ═══════════════════════════════════════════════════════════════
#  ۵) خروج
# ═══════════════════════════════════════════════════════════════

class LogoutTests(TestCase):

    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)
        self.url = reverse("accounts:logout")

    def test_get_does_not_logout(self):
        """GET نباید کاربر را خارج کند (CSRF safety)."""
        response = self.client.get(self.url)

        self.assertIn("_auth_user_id", self.client.session)
        self.assertNotEqual(response.status_code, 200)

    def test_post_logs_out(self):
        """POST موفق: session پاک شود."""
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)


# ═══════════════════════════════════════════════════════════════
#  ۶) پروفایل
# ═══════════════════════════════════════════════════════════════

class ProfileViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("accounts:profile")
        cls.login_url = reverse("accounts:login")
        cls.user = make_user()

    # ── دسترسی ───────────────────────────────────────────────

    def test_requires_login(self):
        """کاربر مهمان به login ریدایرکت شود."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(self.login_url, response["Location"])

    def test_get_renders_template(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile.html")

    def test_context_has_both_forms(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertIn("profile_form", response.context)
        self.assertIn("password_form", response.context)
        self.assertIn("profile", response.context)

    # ── ویرایش اطلاعات ───────────────────────────────────────

    def test_update_profile_success(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {
                "update_profile": "",
                "phone_number": PHONE_ALT,
                "address": "تهران، خیابان ولیعصر",
                "city": "تهران",
                "country": "ایران",
                "birth_date": "1996-06-01",  # اگر ویجت شمسی داری، عوض کن
                "bio": "علاقه‌مند به عکاسی",
                "website": "https://example.com",
            },
        )

        self.assertRedirects(response, self.url)

        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()

        self.assertEqual(self.user.phone_number, PHONE_ALT)
        self.assertEqual(self.user.profile.city, "تهران")
        self.assertEqual(self.user.profile.address, "تهران، خیابان ولیعصر")

    def test_update_profile_normalizes_persian_phone(self):
        self.client.force_login(self.user)

        self.client.post(
            self.url,
            {"update_profile": "", "phone_number": PHONE_FA},
        )

        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, PHONE)

    def test_update_profile_rejects_duplicate_phone(self):
        """شمارهٔ متعلق به کاربر دیگر نباید قابل ذخیره باشد."""
        other = make_user(
            username="other", email="other@example.com", phone_number=PHONE_ALT
        )
        self.client.force_login(self.user)

        response = self.client.post(
            self.url, {"update_profile": "", "phone_number": PHONE_ALT}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("phone_number", response.context["profile_form"].errors)

        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, PHONE)

    def test_update_profile_does_not_change_password(self):
        """فرم پروفایل نباید به رمز عبور دست بزند."""
        self.client.force_login(self.user)

        self.client.post(self.url, {"update_profile": "", "city": "شیراز"})

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(PASSWORD))

    # ── تغییر رمز عبور ───────────────────────────────────────

    def test_change_password_success_keeps_session(self):
        """تغییر رمز موفق + کاربر باید لاگین بماند (update_session_auth_hash)."""
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {
                "change_password": "",
                "old_password": PASSWORD,
                "new_password1": NEW_PASSWORD,
                "new_password2": NEW_PASSWORD,
            },
        )

        self.assertRedirects(response, self.url)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))
        self.assertIn("_auth_user_id", self.client.session)

    def test_change_password_wrong_old_password(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {
                "change_password": "",
                "old_password": "WrongOld@999",
                "new_password1": NEW_PASSWORD,
                "new_password2": NEW_PASSWORD,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
