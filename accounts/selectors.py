"""لایه Query اپ accounts."""

from __future__ import annotations

from datetime import datetime

from django.utils import timezone

from accounts.models import PhoneOTP, Profile, User
from accounts.otp import otp_resend_cooldown
from accounts.utils import (
    normalize_email,
    normalize_login_identifier,
    normalize_phone,
)


def get_user_by_phone(
        phone_number: str,
) -> User | None:
    """یافتن کاربر بر اساس شماره موبایل."""
    phone_number = normalize_phone(phone_number)

    if not phone_number:
        return None

    return (
        User.objects
        .filter(phone_number=phone_number)
        .first()
    )


def get_user_by_email(
        email: str,
) -> User | None:
    """یافتن کاربر بر اساس ایمیل."""
    email = normalize_email(email)

    if not email:
        return None

    return (
        User.objects
        .filter(email=email)
        .first()
    )


def find_user_by_identifier(
        identifier: str,
) -> User | None:
    """یافتن کاربر با موبایل یا ایمیل."""

    normalized = normalize_login_identifier(
        identifier
    )

    if not normalized:
        return None

    if "@" in normalized:
        return get_user_by_email(normalized)

    return get_user_by_phone(normalized)


def user_exists(phone_number: str) -> bool:
    """بررسی وجود کاربر با شماره موبایل."""
    phone_number = normalize_phone(phone_number)

    return (
        User.objects
        .filter(phone_number=phone_number)
        .exists()
    )


def get_profile(user: User) -> Profile:
    """دریافت یا ایجاد پروفایل کاربر."""
    profile, _ = Profile.objects.get_or_create(
        user=user
    )

    return profile


def get_pending_otp(
        phone_number: str,
        purpose: str,
) -> PhoneOTP | None:
    """دریافت آخرین OTP فعال."""
    phone_number = normalize_phone(phone_number)

    return (
        PhoneOTP.objects
        .filter(
            phone_number=phone_number,
            purpose=purpose,
            is_used=False,
        )
        .order_by("-created_at")
        .first()
    )


def get_otp_by_id(
        otp_id: int,
) -> PhoneOTP | None:
    return (
        PhoneOTP.objects
        .filter(pk=otp_id)
        .first()
    )


def last_otp_created_at(
        phone_number: str,
) -> datetime | None:
    """زمان ایجاد آخرین OTP برای شماره."""
    phone_number = normalize_phone(phone_number)

    return (
        PhoneOTP.objects
        .filter(phone_number=phone_number)
        .order_by("-created_at")
        .values_list("created_at", flat=True)
        .first()
    )


def count_recent_otps(
        *,
        since: datetime,
        phone_number: str | None = None,
        ip_address: str | None = None,
) -> int:
    """تعداد OTPهای ایجادشده در بازه زمانی مشخص."""

    queryset = PhoneOTP.objects.filter(
        created_at__gte=since
    )

    if phone_number:
        queryset = queryset.filter(
            phone_number=normalize_phone(phone_number)
        )

    if ip_address:
        queryset = queryset.filter(
            ip_address=ip_address
        )

    return queryset.count()


def resend_cooldown_remaining(
        phone_number: str,
) -> int:
    """تعداد ثانیه باقی‌مانده تا ارسال مجدد OTP."""

    cooldown = otp_resend_cooldown()
    last_created = last_otp_created_at(
        phone_number
    )

    if not last_created:
        return 0

    elapsed = (
            timezone.now() - last_created
    ).total_seconds()

    return max(
        int(cooldown - elapsed),
        0,
    )
