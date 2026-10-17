"""ابزارهای مشترک پروژه — نسخهٔ واحد. هیچجای دیگری نرمالسازی ننویس."""
from __future__ import annotations

import secrets
from typing import Any, Iterable

from django.conf import settings
from django.http import HttpRequest
from django.utils.http import url_has_allowed_host_and_scheme

# ---------------------------------------------------------------- ارقام
_LATIN_DIGITS = "0123456789"
_PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
_ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"

_TO_LATIN = str.maketrans(
    {
        **{ord(p): d for p, d in zip(_PERSIAN_DIGITS, _LATIN_DIGITS)},
        **{ord(a): d for a, d in zip(_ARABIC_DIGITS, _LATIN_DIGITS)},
    }
)
_TO_PERSIAN = str.maketrans({ord(l): p for l, p in zip(_LATIN_DIGITS, _PERSIAN_DIGITS)})


def normalize_digits(value: Any) -> str:
    """همهٔ ارقام فارسی/عربی را به لاتین تبدیل میکند. برای ورودی و ذخیرهسازی."""
    if value is None:
        return ""
    return str(value).translate(_TO_LATIN)


def to_persian_digits(value: Any) -> str:
    """ارقام لاتین را برای *نمایش* فارسی میکند."""
    if value is None:
        return ""
    return str(value).translate(_TO_PERSIAN)


# ---------------------------------------------------------------- حروف فارسی
_PERSIAN_CHAR_MAP = str.maketrans(
    {
        "ي": "ی",
        "ى": "ی",
        "ك": "ک",
        "ة": "ه",
        "\u200c": " ",  # نیمفاصله → فاصله (فقط برای مقایسه/جستوجو)
    }
)


def normalize_persian_chars(value: Any) -> str:
    """ي/ك عربی را به ی/ک فارسی تبدیل میکند. برای جستوجو و یکسانسازی."""
    if value is None:
        return ""
    return str(value).translate(_PERSIAN_CHAR_MAP)


def slugify_fa(value: str) -> str:
    """اسلاگ ساده و امن از متن فارسی/انگلیسی."""
    from django.utils.text import slugify

    text = normalize_persian_chars(normalize_digits(value)).strip()
    return slugify(text, allow_unicode=True)


# ---------------------------------------------------------------- شماره تلفن
IRAN_COUNTRY_CODE = "98"
MOBILE_NATIONAL_LENGTH = 11  # مثال: 09123456789


def normalize_phone_number(value: Any, *, country_code: str = IRAN_COUNTRY_CODE) -> str:
    """شمارهٔ موبایل را به قالب ملی یکدست `09XXXXXXXXX` تبدیل میکند.

    ورودیهای پذیرفتهشده: 09123456789 | 9123456789 | +989123456789
                           00989123456789 | 989123456789 | ۰۹۱۲۳۴۵۶۷۸۹
    اگر ورودی قابل نرمالسازی نباشد، رشتهٔ خالی برمیگرداند؛
    اعتبارسنجی نهایی با `core.validators.validate_iranian_mobile` است.
    """
    digits = normalize_digits(value).strip()
    if not digits:
        return ""

    # نویسههای مجاز تلفنی را نگه دار
    digits = "".join(ch for ch in digits if ch.isdigit() or ch == "+")
    digits = digits.lstrip("+")

    # حذف پیششمارهٔ بینالمللی
    for prefix in (f"00{country_code}", country_code):
        if digits.startswith(prefix) and len(digits) > len(prefix) + 9:
            digits = digits[len(prefix):]
            break

    if digits.startswith("0"):
        digits = digits[1:]

    # اکنون باید 10 رقم با شروع 9 باشد
    if len(digits) != MOBILE_NATIONAL_LENGTH - 1 or not digits.startswith("9"):
        return ""

    return "0" + digits


def is_valid_iranian_mobile(value: Any) -> bool:
    return bool(normalize_phone_number(value))


def phone_to_international(phone: Any, *, country_code: str = IRAN_COUNTRY_CODE) -> str:
    """`09123456789` → `+989123456789` (برای API پیامک)."""
    national = normalize_phone_number(phone, country_code=country_code)
    if not national:
        return ""
    return f"+{country_code}{national[1:]}"


def mask_phone(phone: Any) -> str:
    """نمایش امن: 0912***6789"""
    national = normalize_phone_number(phone)
    if not national:
        return "***"
    return f"{national[:4]}***{national[-4:]}"


def mask_email(email: str) -> str:
    if not email or "@" not in email:
        return "***"
    local, _, domain = email.partition("@")
    visible = local[:2]
    return f"{visible}{'*' * max(len(local) - 2, 1)}@{domain}"


# ---------------------------------------------------------------- IP کلاینت
def get_client_ip(request: HttpRequest, *, trusted_proxies: int | None = None) -> str:
    """IP واقعی کلاینت با احتساب پروکسیهای مورد اعتماد.

    `TRUSTED_PROXY_COUNT` را در settings تعیین کن (پشت nginx معمولاً 1).
    """
    if trusted_proxies is None:
        trusted_proxies = int(getattr(settings, "TRUSTED_PROXY_COUNT", 0))

    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if trusted_proxies > 0 and xff:
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        if len(parts) >= trusted_proxies:
            return parts[-trusted_proxies]

    return request.META.get("REMOTE_ADDR", "") or ""


# ---------------------------------------------------------------- امنیت / ریدایرکت
def is_safe_next_url(request: HttpRequest, url: str | None) -> bool:
    """جلوگیری از Open Redirect."""
    if not url:
        return False
    return url_has_allowed_host_and_scheme(
        url=url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    )


def get_safe_next_url(request: HttpRequest, default: str = "/") -> str:
    candidate = request.POST.get("next") or request.GET.get("next")
    return candidate if is_safe_next_url(request, candidate) else default


# ---------------------------------------------------------------- OTP
def generate_otp_code(length: int | None = None) -> str:
    """کد عددی امن (رمزنگاریشده)."""
    if length is None:
        length = int(getattr(settings, "OTP_LENGTH", 6))
    length = max(4, min(int(length), 10))
    return "".join(secrets.choice(_LATIN_DIGITS) for _ in range(length))


def otp_expiry_seconds() -> int:
    return int(getattr(settings, "OTP_TTL_SECONDS", 120))


# ---------------------------------------------------------------- کمکی
def errors_to_dict(exc: Exception) -> dict[str, Any]:
    """تبدیل خطای دامنهای به دیکشنری قابل برگشت به فرانت."""
    to_dict = getattr(exc, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    return {"code": "internal_error", "message": str(exc), "context": {}}


def error_status_code(exc: Exception) -> int:
    return int(getattr(exc, "http_status", 500))


def chunked(iterable: Iterable, size: int):
    """پیمایش تکهتکه (برای عملیات دستهای)."""
    size = max(int(size), 1)
    bucket: list[Any] = []
    for item in iterable:
        bucket.append(item)
        if len(bucket) >= size:
            yield bucket
            bucket = []
    if bucket:
        yield bucket
