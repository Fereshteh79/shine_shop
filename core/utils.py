"""توابع کمکی عمومی پروژهٔ Shine Shop."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable, Optional

from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme

from core.validators import normalize_digits

# ---------------------------------------------------------------------------
# تبدیل و نرمال‌سازی اعداد
# ---------------------------------------------------------------------------

# جداکننده‌های گروه‌بندی اعداد:
# 1,250,000
# 1،250،000
# 1٬250٬000
# 1 250 000
_GROUPING_TRANS = str.maketrans(
    {
        ",": "",
        "،": "",
        "٬": "",
        " ": "",
        "\u00a0": "",
        "\u200c": "",
    }
)

# ممیز عربی/فارسی → ممیز استاندارد Python
_DECIMAL_TRANS = str.maketrans(
    {
        "٫": ".",
    }
)

# فاصله‌های متوالی
_WHITESPACE_RE = re.compile(r"\s+")

# اعراب و کشیده
_DIACRITICS_RE = re.compile(r"[\u0640\u064b-\u0652\u0670]")

# حروف عربی و فارسی که برای جست‌وجو باید یکسان شوند.
_PERSIAN_CHAR_TRANS = str.maketrans(
    {
        "ي": "ی",
        "ى": "ی",
        "ك": "ک",
        "ة": "ه",
        "ۀ": "ه",
        "أ": "ا",
        "إ": "ا",
        "ٱ": "ا",
        "ؤ": "و",
        "ئ": "ی",
        "ء": "",
    }
)


# ---------------------------------------------------------------------------
# اعداد و پول
# ---------------------------------------------------------------------------

def to_decimal(
        value: Any,
        *,
        default: Optional[Decimal] = None,
) -> Optional[Decimal]:
    """
    تبدیل مقدارهای مختلف به Decimal.

    از ارقام فارسی/عربی، جداکنندهٔ هزارگان و ممیز فارسی پشتیبانی می‌کند.

    مثال:
        "۱,۲۵۰,۰۰۰" -> Decimal("1250000")
        "۱۲۵۰٫۵"    -> Decimal("1250.5")
        "1 250 000" -> Decimal("1250000")
        None        -> default
    """
    if value is None:
        return default

    if isinstance(value, str) and not value.strip():
        return default

    if isinstance(value, Decimal):
        return value

    if isinstance(value, bool):
        raise TypeError("مقدار bool قابل تبدیل مستقیم به عدد نیست.")

    if isinstance(value, int):
        return Decimal(value)

    if isinstance(value, float):
        # استفاده از str برای جلوگیری از خطاهای نمایش دودویی float.
        return Decimal(str(value))

    text = normalize_digits(str(value)).strip()

    # تبدیل ممیز فارسی/عربی
    text = text.translate(_DECIMAL_TRANS)

    # حذف جداکننده‌های هزارگان و فاصله‌ها
    text = text.translate(_GROUPING_TRANS)

    if not text:
        return default

    try:
        return Decimal(text)
    except InvalidOperation:
        if default is not None:
            return default

        raise ValueError(f"عدد نامعتبر است: {value!r}") from None


def money(
        value: Any,
        *,
        default: Optional[Decimal] = None,
) -> Decimal:
    """
    تبدیل مقدار به مبلغ صحیح تومان.

    اعشار با ROUND_HALF_UP گرد می‌شود.

    مثال:
        money("1250000") -> Decimal("1250000")
        money("1250000.6") -> Decimal("1250001")
    """
    number = to_decimal(value, default=default)

    if number is None:
        raise ValueError("مقدار مبلغ نمی‌تواند خالی باشد.")

    return number.quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP,
    )


def format_price(
        value: Any,
        *,
        separator: str = ",",
) -> str:
    """
    قالب‌بندی مبلغ برای نمایش.

    مثال:
        1250000 -> "1,250,000"
        1250000 -> "1٬250٬000"  # با separator دلخواه
    """
    formatted = f"{money(value):,}"

    if separator == ",":
        return formatted

    return formatted.replace(",", separator)


def calculate_percentage(
        amount: Any,
        percentage: Any,
) -> Decimal:
    """
    محاسبهٔ درصدی از یک مبلغ.

    مثال:
        calculate_percentage(100000, 10)
        -> Decimal("10000")
    """
    amount_value = money(amount)

    rate = to_decimal(
        percentage,
        default=Decimal("0"),
    )

    if rate is None:
        rate = Decimal("0")

    result = amount_value * rate / Decimal("100")

    return money(result)


# ---------------------------------------------------------------------------
# امنیت و Redirect
# ---------------------------------------------------------------------------

def safe_redirect(
        request,
        target: Optional[str],
        fallback: str,
        *,
        allowed_hosts: Optional[Iterable[str]] = None,
):
    """
    ریدایرکت امن برای جلوگیری از Open Redirect.

    target فقط زمانی استفاده می‌شود که Django آن را برای هاست/پروتکل
    درخواست معتبر تشخیص دهد؛ در غیر این صورت fallback برگردانده می‌شود.
    """
    if not target:
        return redirect(fallback)

    if allowed_hosts is None:
        hosts = {request.get_host()}
    else:
        hosts = {
            str(host).strip()
            for host in allowed_hosts
            if host and str(host).strip()
        }

        # در صورت ارسال لیست خالی، هاست فعلی همچنان مجاز باشد.
        if not hosts:
            hosts = {request.get_host()}

    try:
        is_safe = url_has_allowed_host_and_scheme(
            target,
            allowed_hosts=hosts,
            require_https=request.is_secure(),
        )
    except (TypeError, ValueError):
        is_safe = False

    if is_safe:
        return redirect(target)

    return redirect(fallback)

# ---------------------------------------------------------------------------
# اطلاعات درخواست و شبکه
# --------------------------------------------------------------------
