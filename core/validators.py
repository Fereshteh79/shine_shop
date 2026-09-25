"""
اعتبارسنج‌های سفارشی پروژهٔ Shine Shop.

شامل:
- نرمال‌سازی ارقام فارسی و عربی
- شماره موبایل ایران
- کد ملی ایران
- کد پستی ایران
- شماره شبا (IBAN)
- شماره کارت بانکی
- اعتبارسنجی فایل‌های تصویری
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

# ============================================================================
# ابزارهای عمومی
# ============================================================================

_DIGIT_TRANS = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
    "01234567890123456789",
)

_DIGIT_RE = re.compile(r"\D+")


def normalize_digits(value: Any) -> str:
    """
    تبدیل ارقام فارسی و عربی به لاتین و حذف فاصلهٔ ابتدا/انتها.

    مثال:
        "۰۹۱۲۳۴۵۶۷۸۹" -> "09123456789"
    """
    if value is None:
        return ""

    return str(value).strip().translate(_DIGIT_TRANS)


def _digits_only(value: Any) -> str:
    """تمام کاراکترهای غیرعددی را حذف می‌کند."""
    return _DIGIT_RE.sub("", normalize_digits(value))


# ============================================================================
# موبایل ایران
# ============================================================================

MOBILE_RE = re.compile(r"^09\d{9}$")

_MOBILE_SEPARATORS_TRANS = str.maketrans(
    {
        " ": "",
        "\u00a0": "",
        "\u200c": "",
        "-": "",
        "(": "",
        ")": "",
        ".": "",
    }
)


def normalize_iranian_mobile(value: Any) -> str:
    """
    یکدست‌سازی شماره موبایل ایران به فرمت:

        09xxxxxxxxx

    نمونه‌های قابل پشتیبانی:
        09123456789
        +989123456789
        00989123456789
        989123456789
        0912 345 6789
        0912-345-6789
    """
    if value is None:
        return ""

    digits = normalize_digits(value)
    digits = digits.translate(_MOBILE_SEPARATORS_TRANS)

    if digits.startswith("+98"):
        digits = "0" + digits[3:]

    elif digits.startswith("0098"):
        digits = "0" + digits[4:]

    elif digits.startswith("98") and len(digits) == 12:
        digits = "0" + digits[2:]

    return digits


def is_iranian_mobile(value: Any) -> bool:
    """بررسی معتبر بودن شماره موبایل ایران."""
    return bool(MOBILE_RE.fullmatch(normalize_iranian_mobile(value)))


def validate_iranian_mobile(value: Any) -> str:
    """
    اعتبارسنجی شماره موبایل ایران.

    در صورت معتبر بودن، شمارهٔ نرمال‌شده را برمی‌گرداند.
    """
    normalized = normalize_iranian_mobile(value)

    if not normalized:
        raise ValidationError("شماره موبایل الزامی است.")

    if not MOBILE_RE.fullmatch(normalized):
        raise ValidationError(
            "شماره موبایل معتبر نیست. نمونه صحیح: 09123456789"
        )

    return normalized


@deconstructible
class IranianMobileValidator:
    """Validator قابل استفاده در مدل‌های Django."""

    message = "شماره موبایل ایران معتبر نیست."
    code = "invalid_mobile"

    def __call__(self, value: Any) -> None:
        normalized = normalize_iranian_mobile(value)

        if not MOBILE_RE.fullmatch(normalized):
            raise ValidationError(
                self.message,
                code=self.code,
            )


# ============================================================================
# کد ملی ایران
# ============================================================================

_NATIONAL_ID_RE = re.compile(r"^\d{10}$")


def normalize_national_id(value: Any) -> str:
    """نرمال‌سازی کد ملی و حذف فاصله/خط تیره."""
    return _digits_only(value)


def is_valid_national_id(value: Any) -> bool:
    """
    بررسی الگوریتمی کد ملی ایران.

    کد ملی باید:
    - دقیقاً ۱۰ رقم داشته باشد.
    - تمام ارقام آن یکسان نباشند.
    - رقم کنترل آن با الگوریتم استاندارد مطابقت داشته باشد.
    """
    code = normalize_national_id(value)

    if not _NATIONAL_ID_RE.fullmatch(code):
        return False

    if len(set(code)) == 1:
        return False

    digits = [int(char) for char in code]

    weighted_sum = sum(
        digits[index] * (10 - index)
        for index in range(9)
    )

    remainder = weighted_sum % 11
    check_digit = digits[9]

    if remainder < 2:
        return check_digit == remainder

    return check_digit == 11 - remainder


def validate_national_id(value: Any) -> str:
    """اعتبارسنجی کد ملی و بازگرداندن مقدار نرمال‌شده."""
    normalized = normalize_national_id(value)

    if not normalized:
        raise ValidationError("کد ملی الزامی است.")

    if not is_valid_national_id(normalized):
        raise ValidationError(
            "کد ملی واردشده معتبر نیست.",
            code="invalid_national_id",
        )

    return normalized


@deconstructible
class IranianNationalIdValidator:
    """Validator قابل استفاده در ModelField و FormField."""

    message = "کد ملی واردشده معتبر نیست."
    code = "invalid_national_id"

    def __call__(self, value: Any) -> None:
        if not is_valid_national_id(value):
            raise ValidationError(
                self.message,
                code=self.code,
            )


# ============================================================================
# کد پستی ایران
# ============================================================================

_POSTAL_CODE_RE = re.compile(r"^\d{10}$")


def normalize_postal_code(value: Any) -> str:
    """نرمال‌سازی کد پستی."""
    return _digits_only(value)


def is_valid_postal_code(value: Any) -> bool:
    """
    بررسی ساختار کد پستی ایران.

    کد پستی ایران باید دقیقاً ۱۰ رقم باشد.
    """
    code = normalize_postal_code(value)

    if not _POSTAL_CODE_RE.fullmatch(code):
        return False

    # کد پستی نمی‌تواند با 0 یا 2 شروع شود.
    # این شرط با ساختار رایج کدهای پستی ایران سازگار است.
    if code[0] in {"0", "2"}:
        return False

    return True


def validate_postal_code(value: Any) -> str:
    """اعتبارسنجی کد پستی."""
    normalized = normalize_postal_code(value)

    if not normalized:
        raise ValidationError("کد پستی الزامی است.")

    if not is_valid_postal_code(normalized):
        raise ValidationError(
            "کد پستی باید یک کد ۱۰ رقمی معتبر باشد.",
            code="invalid_postal_code",
        )

    return normalized


@deconstructible
class IranianPostalCodeValidator:
    """Validator کد پستی ایران برای Django."""

    message = "کد پستی واردشده معتبر نیست."
    code = "invalid_postal_code"

    def __call__(self, value: Any) -> None:
        if not is_valid_postal_code(value):
            raise ValidationError(
                self.message,
                code=self.code,
            )


# ============================================================================
# شبا / IBAN ایران
# ============================================================================

_IRAN_IBAN_RE = re.compile(r"^IR\d{24}$")


def normalize_iban(value: Any) -> str:
    """
    نرمال‌سازی IBAN.

    فاصله‌ها و خط تیره حذف می‌شوند و حروف به uppercase تبدیل می‌شوند.
    """
    if value is None:
        return ""

    text = normalize_digits(value)
    text = re.sub(r"[\s\-]", "", text)

    return text.upper()


def is_valid_iranian_iban(value: Any) -> bool:
    """
    اعتبارسنجی ساختاری و الگوریتم MOD-97 برای شبا ایران.
    """
    iban = normalize_iban(value)

    if not _IRAN_IBAN_RE.fullmatch(iban):
        return False

    # انتقال چهار کاراکتر اول به انتهای رشته.
    rearranged = iban[4:] + iban[:4]

    numeric = []

    for char in rearranged:
        if char.isdigit():
            numeric.append(char)
        elif "A" <= char <= "Z":
            numeric.append(str(ord(char) - ord("A") + 10))
        else:
            return False

    try:
        return int("".join(numeric)) % 97 == 1
    except ValueError:
        return False


def validate_iranian_iban(value: Any) -> str:
    """اعتبارسنجی شبا و بازگرداندن مقدار استاندارد."""
    normalized = normalize_iban(value)

    if not normalized:
        raise ValidationError("شماره شبا الزامی است.")

    if not is_valid_iranian_iban(normalized):
        raise ValidationError(
            "شماره شبا (IBAN) واردشده معتبر نیست.",
            code="invalid_iban",
        )

    return normalized


@deconstructible
class IranianIBANValidator:
    """Validator شبا ایران برای Django."""

    message = "شماره شبا واردشده معتبر نیست."
    code = "invalid_iban"

    def __call__(self, value: Any) -> None:
        if not is_valid_iranian_iban(value):
            raise ValidationError(
                self.message,
                code=self.code,
            )


# ============================================================================
# شماره کارت بانکی ایران
# ============================================================================

_CARD_RE = re.compile(r"^\d{16}$")


def normalize_card_number(value: Any) -> str:
    """نرمال‌سازی شماره کارت بانکی."""
    return _digits_only(value)


def is_valid_card_number(value: Any) -> bool:
    """
    اعتبارسنجی شماره کارت با الگوریتم Luhn.

    شماره کارت ایران معمولاً ۱۶ رقمی است.
    """
    card = normalize_card_number(value)

    if not _CARD_RE.fullmatch(card):
        return False

    # جلوگیری از پذیرش شماره‌هایی مانند 1111111111111111
    if len(set(card)) == 1:
        return False

    digits = [int(char) for char in card]

    checksum = 0

    for index, digit in enumerate(digits):
        if index % 2 == 0:
            value = digit * 2
            checksum += value - 9 if value > 9 else value
        else:
            checksum += digit

    return checksum % 10 == 0


def validate_card_number(value: Any) -> str:
    """اعتبارسنجی شماره کارت."""
    normalized = normalize_card_number(value)

    if not normalized:
        raise ValidationError("شماره کارت الزامی است.")

    if not is_valid_card_number(normalized):
        raise ValidationError(
            "شماره کارت بانکی معتبر نیست.",
            code="invalid_card_number",
        )

    return normalized


@deconstructible
class IranianCardNumberValidator:
    """Validator شماره کارت برای Django."""

    message = "شماره کارت بانکی معتبر نیست."
    code = "invalid_card_number"

    def __call__(self, value: Any) -> None:
        if not is_valid_card_number(value):
            raise ValidationError(
                self.message,
                code=self.code,
            )


# ============================================================================
# فایل تصویر
# ============================================================================

DEFAULT_IMAGE_EXTENSIONS = frozenset(
    {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }
)

DEFAULT_IMAGE_CONTENT_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
    }
)


@deconstructible
class ImageFileValidator:
    """
    اعتبارسنج فایل تصویر.

    توجه:
    بررسی MIME type به‌تنهایی امنیت کامل ایجاد نمی‌کند؛
    در محل آپلود حساس بهتر است محتوای واقعی فایل نیز بررسی شود.
    """

    def __init__(
            self,
            *,
            max_size_mb: int = 5,
            allowed_extensions: tuple[str, ...] | None = None,
            allowed_content_types: tuple[str, ...] | None = None,
    ) -> None:
        if max_size_mb <= 0:
            raise ValueError("max_size_mb باید بزرگ‌تر از صفر باشد.")

        self.max_size = max_size_mb * 1024 * 1024

        self.allowed_extensions = frozenset(
            extension.lower()
            if extension.startswith(".")
            else f".{extension.lower()}"
            for extension in (
                    allowed_extensions
                    or tuple(DEFAULT_IMAGE_EXTENSIONS)
            )
        )

        self.allowed_content_types = frozenset(
            allowed_content_types
            or tuple(DEFAULT_IMAGE_CONTENT_TYPES)
        )

    def __call__(self, value: Any) -> None:
        if not value:
            return

        # بررسی حجم فایل
        size = getattr(value, "size", None)

        if size is not None and size > self.max_size:
            max_mb = self.max_size // (1024 * 1024)

            raise ValidationError(
                f"حجم تصویر نمی‌تواند بیشتر از {max_mb} مگابایت باشد.",
                code="image_too_large",
            )

        # بررسی پسوند
        name = getattr(value, "name", "") or ""
        extension = Path(name).suffix.lower()

        if extension not in self.allowed_extensions:
            extensions = ", ".join(
                sorted(self.allowed_extensions)
            )

            raise ValidationError(
                f"فرمت تصویر مجاز نیست. فرمت‌های مجاز: {extensions}",
                code="invalid_image_extension",
            )

        # بررسی MIME type در صورت در دسترس بودن
        content_type = getattr(value, "content_type", None)

        if (
                content_type
                and content_type.lower() not in self.allowed_content_types
        ):
            raise ValidationError(
                "نوع فایل تصویر معتبر نیست.",
                code="invalid_image_content_type",
            )


# ============================================================================
# Validator عمومی تصویر
# ============================================================================

validate_image = ImageFileValidator()

# ============================================================================
# توابع کمکی عمومی برای استفاده در کد پروژه
# ==========
