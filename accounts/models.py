import re

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


def validate_iranian_mobile(value: str) -> None:
    """اعتبارسنجی شماره موبایل ایران — فرمت 09xxxxxxxxx."""
    if not re.fullmatch(r"09\d{9}", value):
        raise ValidationError(
            "شماره موبایل باید با ۰۹ شروع شده و ۱۱ رقم باشد."
        )


class User(AbstractUser):
    email = models.EmailField(
        unique=True,
        verbose_name="ایمیل",
    )

    phone_number = models.CharField(
        max_length=11,
        unique=True,
        null=True,
        blank=True,
        validators=[validate_iranian_mobile],
        verbose_name="شماره موبایل",
    )

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"
        ordering = ("-date_joined",)
        indexes = [
            models.Index(fields=("email",)),
            models.Index(fields=("phone_number",)),
        ]

    def __str__(self):
        return self.display_name

    @property
    def display_name(self) -> str:
        return self.get_full_name() or self.username

    def clean(self):
        super().clean()

        if self.phone_number:
            self.phone_number = self.phone_number.strip()

        if self.email:
            self.email = self.email.lower().strip()


class PhoneOTP(models.Model):
    """کد یکبارمصرف پیامکی برای ورود با شماره موبایل — کد به‌صورت هش ذخیره می‌شود."""

    phone_number = models.CharField(
        max_length=11,
        db_index=True,
        verbose_name="شماره موبایل",
    )
    code_hash = models.CharField(
        max_length=64,
        verbose_name="هش کد",
    )
    attempts = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="تعداد تلاش‌ها",
    )
    is_used = models.BooleanField(
        default=False,
        verbose_name="استفاده شده",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد",
    )
    expires_at = models.DateTimeField(
        verbose_name="تاریخ انقضا",
    )

    class Meta:
        verbose_name = "کد یکبارمصرف"
        verbose_name_plural = "کدهای یکبارمصرف"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("phone_number", "is_used")),
        ]

    def __str__(self):
        return f"{self.phone_number} - {self.created_at:%Y-%m-%d %H:%M}"

    @property
    def is_expired(self) -> bool:
        from django.utils import timezone
        return timezone.now() > self.expires_at
