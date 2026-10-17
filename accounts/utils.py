"""ابزارهای اپ accounts — همهٔ پیاده‌سازی‌ها منبع واحد دارند: core.utils.

این ماژول فقط aliasهای سازگار با کد موجود اپ accounts ارائه می‌کند
تا importها و migrationهای سریال‌شده نشکنند. منطق جدیدی اینجا ننویسید.
"""

from __future__ import annotations

from typing import Any

from core.utils import (
    generate_otp_code,
    get_client_ip,
    mask_phone as _mask_phone,
    mask_email as _mask_email,
    normalize_digits,
    normalize_phone_number,
    phone_to_international,
    to_persian_digits,
)

__all__ = [
    "generate_otp_code",
    "get_client_ip",
    "normalize_digits",
    "normalize_phone",
    "normalize_phone_number",
    "normalize_national_code",
    "normalize_postal_code",
    "normalize_text",
    "normalize_email",
    "normalize_login_identifier",
    "is_valid_mobile",
    "mask_phone",
    "mask_email",
    "phone_to_international",
    "to_persian_digits",
]


# ---------------------------------------------------------------- شماره موبایل


def normalize_phone(value: Any) -> str:
    """نام سازگار با کد اپ accounts برای normalize_phone_number در core.

    خروجی: 09XXXXXXXXX یا رشتهٔ خالی در صورت نامعتبر بودن.
    """
    return normalize_phone_number(value)


normalize_phone_number  # صریحاً re-export می‌شود


def is_valid_mobile(value: Any) -> bool:
    """بررسی معتبر بودن شماره موبایل پس از نرمال‌سازی."""
    return bool(normalize_phone(value))


# ---------------------------------------------------------------- متن و شناسه‌ها


def normalize_national_code(value: Any) -> str:
    """کد ملی: فقط ارقام لاتین."""
    return normalize_digits(value).strip()


def normalize_postal_code(value: Any) -> str:
    """کد پستی: فقط ارقام لاتین."""
    return normalize_digits(value).strip()


def normalize_text(value: Any) -> str:
    """حذف فاصله‌های اضافی و ابتدا/انتهای متن."""
    return " ".join(str(value or "").split())


def normalize_email(value: Any) -> str | None:
    """ایمیل نرمال‌شده؛ خالی به None (سازگار با EmailField null=True)."""
    email = str(value or "").strip().lower()
    return email or None


def normalize_login_identifier(value: Any) -> str:
    """شناسهٔ ورود: اگر @ داشت ایمیل، وگرنه شمارهٔ موبایل."""
    raw = str(value or "").strip()

    if not raw:
        return ""

    if "@" in raw:
        return normalize_email(raw) or ""

    return normalize_phone(raw)


# ---------------------------------------------------------------- نمایش امن


def mask_phone(value: Any) -> str:
    """نمایش امن موبایل: 0912***4567."""
    return _mask_phone(value)


def mask_email(value: Any) -> str:
    """نمایش امن ایمیل: a***@example.com."""
    return _mask_email(value)
