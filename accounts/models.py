"""مدل‌های اپ accounts: User سفارشی، Profile و PhoneOTP."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models, transaction
from django.utils import timezone

from .utils import (
    mask_email,
    mask_phone,
    normalize_email,
    normalize_national_code,
    normalize_phone,
    normalize_postal_code,
    normalize_text,
)
from .validators import (
    validate_avatar_extension,
    validate_avatar_size,
    validate_iranian_mobile,
    validate_iranian_national_code,
    validate_not_future_date,
)


class UserManager(BaseUserManager):
    """مدیر سفارشی کاربران با احراز هویت بر پایه شماره موبایل."""

    use_in_migrations = True

    def _create_user(
            self,
            phone_number: str,
            password: str | None,
            **extra_fields: Any,
    ) -> User:
        """ساخت کاربر با داده‌های نرمال‌شده. ساخت Profile در signals انجام می‌شود."""

        normalized_phone = normalize_phone(phone_number)

        if not normalized_phone:
            raise ValueError("شماره موبایل الزامی است.")

        extra_fields["email"] = normalize_email(extra_fields.get("email"))
        extra_fields["first_name"] = normalize_text(extra_fields.get("first_name"))
        extra_fields["last_name"] = normalize_text(extra_fields.get("last_name"))

        with transaction.atomic():
            user = self.model(
                phone_number=normalized_phone,
                **extra_fields,
            )

            if password:
                user.set_password(password)
            else:
                user.set_unusable_password()

            user.save(using=self._db)

        return user

    def create_user(
            self,
            phone_number: str,
            password: str | None = None,
            **extra_fields: Any,
    ) -> User:
        """ساخت کاربر عادی."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not False:
            raise ValueError("کاربر عادی نباید is_staff=True داشته باشد.")

        if extra_fields.get("is_superuser") is not False:
            raise ValueError("کاربر عادی نباید is_superuser=True داشته باشد.")

        return self._create_user(
            phone_number=phone_number,
            password=password,
            **extra_fields,
        )

    def create_superuser(
            self,
            phone_number: str,
            password: str,
            **extra_fields: Any,
    ) -> User:
        """ساخت سوپریوزر با دسترسی کامل."""
        if not password:
            raise ValueError("رمز عبور سوپریوزر الزامی است.")

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_phone_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("سوپریوزر باید is_staff=True باشد.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("سوپریوزر باید is_superuser=True باشد.")

        if extra_fields.get("is_active") is not True:
            raise ValueError("سوپریوزر باید is_active=True باشد.")

        if extra_fields.get("is_phone_verified") is not True:
            raise ValueError("سوپریوزر باید موبایل تأییدشده داشته باشد.")

        return self._create_user(
            phone_number=phone_number,
            password=password,
            **extra_fields,
        )

    def get_by_natural_key(self, username: str) -> User:
        """بازیابی کاربر بر اساس شماره موبایل نرمال‌شده."""
        return self.get(phone_number=normalize_phone(username))


class User(AbstractBaseUser, PermissionsMixin):
    """کاربر اصلی سیستم."""

    phone_number = models.CharField(
        "شماره موبایل",
        max_length=11,
        unique=True,
        validators=[validate_iranian_mobile],
        help_text="مثال: 09121234567",
    )

    email = models.EmailField(
        "ایمیل",
        unique=True,
        null=True,
        blank=True,
    )

    first_name = models.CharField("نام", max_length=60, blank=True)
    last_name = models.CharField("نام خانوادگی", max_length=60, blank=True)

    is_active = models.BooleanField("فعال", default=True)
    is_staff = models.BooleanField("دسترسی به پنل مدیریت", default=False)
    is_phone_verified = models.BooleanField("موبایل تأییدشده", default=False)

    date_joined = models.DateTimeField("تاریخ عضویت", default=timezone.now)
    updated_at = models.DateTimeField("آخرین بروزرسانی", auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"
        ordering = ("-date_joined", "-id")

    def __str__(self) -> str:
        return self.get_full_name() or self.masked_phone

    @property
    def display_name(self) -> str:
        return self.get_full_name() or self.masked_phone

    def get_full_name(self) -> str:
        return normalize_text(f"{self.first_name} {self.last_name}")

    def get_short_name(self) -> str:
        return self.first_name or self.masked_phone

    @property
    def masked_phone(self) -> str:
        return mask_phone(self.phone_number)

    @property
    def masked_email(self) -> str:
        return mask_email(self.email) or "—"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """نرمال‌سازی داده‌ها قبل از ذخیره. جایگزین full_clean() نیست."""
        self.phone_number = normalize_phone(self.phone_number)
        self.email = normalize_email(self.email)
        self.first_name = normalize_text(self.first_name)
        self.last_name = normalize_text(self.last_name)

        super().save(*args, **kwargs)


def avatar_upload_to(instance: Profile, filename: str) -> str:
    """مسیر یکتا برای آواتار کاربر."""
    suffix = Path(filename).suffix.lower()
    return f"accounts/avatars/{instance.user_id}/{uuid.uuid4().hex}{suffix}"


class Profile(models.Model):
    """اطلاعات تکمیلی پروفایل کاربر."""

    class Gender(models.TextChoices):
        UNKNOWN = "", "نامشخص"
        MALE = "male", "مرد"
        FEMALE = "female", "زن"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="کاربر",
    )

    national_code = models.CharField(
        "کد ملی",
        max_length=10,
        blank=True,
        validators=[validate_iranian_national_code],
    )

    birth_date = models.DateField(
        "تاریخ تولد",
        null=True,
        blank=True,
        validators=[validate_not_future_date],
    )

    gender = models.CharField(
        "جنسیت",
        max_length=6,
        choices=Gender.choices,
        default=Gender.UNKNOWN,
    )

    province = models.CharField("استان", max_length=50, blank=True)
    city = models.CharField("شهر", max_length=50, blank=True)
    postal_code = models.CharField("کد پستی", max_length=10, blank=True)
    address = models.TextField("نشانی", max_length=500, blank=True)

    avatar = models.ImageField(
        "تصویر پروفایل",
        upload_to=avatar_upload_to,
        null=True,
        blank=True,
        validators=[validate_avatar_size, validate_avatar_extension],
    )

    created_at = models.DateTimeField("زمان ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین بروزرسانی", auto_now=True)

    _COMPLETION_FIELDS = (
        "national_code",
        "birth_date",
        "gender",
        "province",
        "city",
        "postal_code",
        "address",
    )

    class Meta:
        verbose_name = "پروفایل"
        verbose_name_plural = "پروفایل‌ها"

    def __str__(self) -> str:
        return f"پروفایل {self.user}"

    @property
    def full_name(self) -> str:
        return self.user.get_full_name()

    @property
    def has_avatar(self) -> bool:
        return bool(self.avatar)

    def save(self, *args: Any, **kwargs: Any) -> None:
        """نرمال‌سازی داده‌ها قبل از ذخیره."""
        self.national_code = normalize_national_code(self.national_code)
        self.postal_code = normalize_postal_code(self.postal_code)
        self.province = normalize_text(self.province)
        self.city = normalize_text(self.city)
        self.address = normalize_text(self.address)

        super().save(*args, **kwargs)

    @property
    def completion_percent(self) -> int:
        """درصد تکمیل اطلاعات اصلی پروفایل."""
        total = len(self._COMPLETION_FIELDS)

        if total == 0:
            return 100

        filled = sum(
            1 for field in self._COMPLETION_FIELDS
            if getattr(self, field) not in ("", None)
        )

        return round(filled * 100 / total)


class PhoneOTP(models.Model):
    """
    کد یکبارمصرف موبایل.

    کد واقعی هرگز در دیتابیس ذخیره نمی‌شود؛ فقط hash آن نگهداری می‌شود.
    """

    class Purpose(models.TextChoices):
        LOGIN = "login", "ورود"
        REGISTER = "register", "ثبت‌نام"
        RESET_PASSWORD = "reset", "بازیابی رمز عبور"

    phone_number = models.CharField(
        "شماره موبایل",
        max_length=11,
        db_index=True,
    )

    purpose = models.CharField(
        "هدف",
        max_length=20,
        choices=Purpose.choices,
        default=Purpose.LOGIN,
    )

    code_hash = models.CharField("هش کد", max_length=255)

    attempts = models.PositiveSmallIntegerField("تعداد تلاش ناموفق", default=0)
    is_used = models.BooleanField("استفاده‌شده", default=False)
    expires_at = models.DateTimeField("زمان انقضا")
    verified_at = models.DateTimeField("زمان تأیید", null=True, blank=True)
    ip_address = models.GenericIPAddressField("آی‌پی درخواست", null=True, blank=True)
    created_at = models.DateTimeField("زمان ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "کد یکبارمصرف"
        verbose_name_plural = "کدهای یکبارمصرف"
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=["phone_number", "purpose", "created_at"], name="otp_lookup_idx"),
            models.Index(fields=["expires_at"], name="otp_expiry_idx"),
            models.Index(fields=["is_used", "expires_at"], name="otp_active_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.get_purpose_display()} — {mask_phone(self.phone_number)}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """نرمال‌سازی شماره موبایل قبل از ذخیره."""
        self.phone_number = normalize_phone(self.phone_number)
        super().save(*args, **kwargs)

    @property
    def max_attempts(self) -> int:
        """حداکثر تعداد تلاش مجاز (منبع واحد: OTP_MAX_VERIFY_ATTEMPTS)."""
        value = getattr(settings, "OTP_MAX_VERIFY_ATTEMPTS", 5)

        try:
            return max(int(value), 1)
        except (TypeError, ValueError):
            return 5

    @property
    def attempts_left(self) -> int:
        return max(self.max_attempts - self.attempts, 0)

    @property
    def is_expired(self) -> bool:
        return self.expires_at <= timezone.now()

    @property
    def is_locked(self) -> bool:
        return self.attempts >= self.max_attempts

    @property
    def is_valid(self) -> bool:
        return not (self.is_used or self.is_expired or self.is_locked)

    def mark_used(self, *, verified: bool = False, save: bool = True) -> PhoneOTP:
        """علامت‌گذاری OTP به‌عنوان استفاده‌شده."""
        self.is_used = True
        update_fields = ["is_used"]

        if verified:
            self.verified_at = timezone.now()
            update_fields.append("verified_at")

        if save:
            self.save(update_fields=update_fields)

        return self
