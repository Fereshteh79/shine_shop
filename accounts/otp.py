"""ابزارها و policyهای OTP بدون دسترسی مستقیم به دیتابیس.

منبع واحد تنظیمات: shine_shop/settings.py
    OTP_CODE_LENGTH | OTP_CODE_TTL | OTP_RESEND_INTERVAL | OTP_MAX_VERIFY_ATTEMPTS
"""

from __future__ import annotations

import secrets
import string
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password

DEFAULT_OTP_SMS_TEMPLATE = (
    "کد ورود شما به شاین: {code}\n"
    "این کد را در اختیار دیگران نگذارید."
)


def otp_length() -> int:
    """طول کد OTP (بین ۴ تا ۱۰ رقم)."""
    value = int(getattr(settings, "OTP_CODE_LENGTH", 6))

    if not 4 <= value <= 10:
        raise ValueError("OTP_CODE_LENGTH باید بین ۴ و ۱۰ باشد.")

    return value


def otp_ttl() -> timedelta:
    """مدت اعتبار OTP."""
    seconds = int(getattr(settings, "OTP_CODE_TTL", 120))

    if seconds <= 0:
        raise ValueError("OTP_CODE_TTL باید بزرگ‌تر از صفر باشد.")

    return timedelta(seconds=seconds)


def otp_max_attempts() -> int:
    """حداکثر تعداد تلاش ناموفق برای هر کد."""
    value = int(getattr(settings, "OTP_MAX_VERIFY_ATTEMPTS", 5))

    if value <= 0:
        raise ValueError("OTP_MAX_VERIFY_ATTEMPTS باید بزرگ‌تر از صفر باشد.")

    return value


def otp_resend_cooldown() -> int:
    """فاصلهٔ مجاز (ثانیه) بین دو درخواست OTP."""
    value = int(getattr(settings, "OTP_RESEND_INTERVAL", 90))

    if value < 0:
        raise ValueError("OTP_RESEND_INTERVAL نمی‌تواند منفی باشد.")

    return value


def otp_max_sends_per_phone_per_hour() -> int:
    """حداکثر درخواست OTP برای هر شماره در یک ساعت."""
    value = int(getattr(settings, "OTP_MAX_SENDS_PER_PHONE_PER_HOUR", 5))

    if value <= 0:
        raise ValueError("OTP_MAX_SENDS_PER_PHONE_PER_HOUR باید بزرگ‌تر از صفر باشد.")

    return value


def otp_max_sends_per_ip_per_hour() -> int:
    """حداکثر درخواست OTP از هر IP در یک ساعت."""
    value = int(getattr(settings, "OTP_MAX_SENDS_PER_IP_PER_HOUR", 20))

    if value <= 0:
        raise ValueError("OTP_MAX_SENDS_PER_IP_PER_HOUR باید بزرگ‌تر از صفر باشد.")

    return value


def generate_otp() -> str:
    """تولید کد تصادفی امن."""
    return "".join(secrets.choice(string.digits) for _ in range(otp_length()))


def hash_otp(code: str) -> str:
    """ذخیره امن OTP به‌صورت hash (کد هرگز خام ذخیره نمی‌شود)."""
    return make_password(code)


def check_otp(code: str, code_hash: str) -> bool:
    """بررسی OTP در برابر hash."""
    return check_password(code, code_hash)


def build_otp_message(code: str) -> str:
    """ساخت متن پیامک OTP."""
    template = getattr(settings, "OTP_SMS_TEMPLATE", DEFAULT_OTP_SMS_TEMPLATE)

    return template.format(code=code)
