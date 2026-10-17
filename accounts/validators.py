"""اعتبارسنج‌های اپ accounts.

خطای پرت‌شده همیشه django.core.exceptions.ValidationError است تا
هم در فرم‌ها و هم در full_clean() مدل‌ها کار کند.

نرمال‌سازی اینجا انجام نمی‌شود؛ منبع واحد آن core.utils است.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError

from core.constants import AVATAR_ALLOWED_CONTENT_TYPES, AVATAR_MAX_SIZE
from core.utils import normalize_digits, normalize_phone_number


# ---------------------------------------------------------------- شماره موبایل


def validate_iranian_mobile(value: str) -> None:
    """اعتبارسنجی شمارهٔ موبایل ایران در قالب 09XXXXXXXXX."""
    if not value:
        raise ValidationError("شمارهٔ تلفن همراه الزامی است.")

    normalized = normalize_phone_number(value)

    if not normalized:
        raise ValidationError("شمارهٔ تلفن همراه معتبر نیست. نمونهٔ درست: 09123456789")

    if not normalized.startswith("09"):
        raise ValidationError("شمارهٔ تلفن همراه باید با 09 شروع شود.")


# ---------------------------------------------------------------- کد ملی (با رقم کنترل)


def validate_iranian_national_code(value: str) -> None:
    """اعتبارسنجی کد ملی ایران با الگوریتم رقم کنترل."""
    code = normalize_digits(value)

    if not code:
        return  # فیلد اختیاری است؛ الزام در فرم بررسی می‌شود

    if not code.isdigit() or len(code) != 10:
        raise ValidationError("کد ملی باید ۱۰ رقم باشد.")

    if code == code[0] * 10:
        raise ValidationError("کد ملی واردشده معتبر نیست.")

    check = int(code[9])
    total = sum(int(code[i]) * (10 - i) for i in range(9))
    remainder = total % 11

    is_valid = (remainder < 2 and check == remainder) or (
            remainder >= 2 and check == 11 - remainder
    )

    if not is_valid:
        raise ValidationError("کد ملی واردشده معتبر نیست.")


# ---------------------------------------------------------------- تاریخ


def validate_not_future_date(value) -> None:
    """تاریخ نباید در آینده باشد (مثلاً تاریخ تولد)."""
    from django.utils import timezone

    if value and value > timezone.localdate():
        raise ValidationError("تاریخ نمی‌تواند در آینده باشد.")


# ---------------------------------------------------------------- آواتار


def validate_avatar_size(file) -> None:
    """حجم فایل آواتار (علاوه بر محدودیت خود ImageField)."""
    if not file:
        return

    size = getattr(file, "size", 0) or 0

    if size > AVATAR_MAX_SIZE:
        raise ValidationError("حجم تصویر نباید بیشتر از ۲ مگابایت باشد.")


def validate_avatar_extension(file) -> None:
    """پسوند و نوع فایل آواتار."""
    if not file:
        return

    content_type = getattr(file, "content_type", None)

    if content_type and content_type not in AVATAR_ALLOWED_CONTENT_TYPES:
        raise ValidationError("فرمت تصویر باید JPG، PNG یا WEBP باشد.")


# ---------------------------------------------------------------- کد OTP


def validate_otp_code(value: str, *, length: int = 6) -> None:
    digits = normalize_digits(value)

    if not digits:
        raise ValidationError("کد تأیید الزامی است.")
    if not digits.isdigit():
        raise ValidationError("کد تأیید فقط باید عدد باشد.")
    if len(digits) != length:
        raise ValidationError(f"کد تأیید باید {length} رقم باشد.")


# ---------------------------------------------------------------- اعداد و مبالغ


def validate_non_negative_amount(value) -> None:
    """مبلغ صفر یا مثبت با حداکثر دو رقم اعشار."""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError("مبلغ واردشده معتبر نیست.") from exc

    if amount < Decimal("0"):
        raise ValidationError("مبلغ نمی‌تواند منفی باشد.")

    exponent = amount.as_tuple().exponent
    if isinstance(exponent, int) and exponent < -2:
        raise ValidationError("مبلغ حداکثر می‌تواند دو رقم اعشار داشته باشد.")


def validate_positive_int(value, *, min_value: int = 1, max_value: int | None = None) -> None:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError("مقدار واردشده باید عدد صحیح باشد.") from exc

    if number < min_value:
        raise ValidationError(f"مقدار باید حداقل {min_value} باشد.")
    if max_value is not None and number > max_value:
        raise ValidationError(f"مقدار باید حداکثر {max_value} باشد.")
