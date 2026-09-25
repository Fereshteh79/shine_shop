# accounts/otp.py
"""
مدیریت کد یکبارمصرف پیامکی (OTP).

- تولید کد ۶ رقمی
- ذخیرهٔ هش‌شدهٔ کد
- محدودیت زمانی
- محدودیت تعداد تلاش
- فاصلهٔ حداقلی بین ارسال‌ها
- پشتیبانی از اعداد فارسی و انگلیسی
"""

import hashlib
import logging
import secrets

from django.conf import settings
from django.utils import timezone

from .models import PhoneOTP
from .sms import SMSDeliveryError, send_sms

logger = logging.getLogger(__name__)

CODE_LENGTH = 6
PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


class OTPError(Exception):
    """خطای عمومی OTP با پیام قابل نمایش به کاربر."""


def _hash_code(code: str) -> str:
    """هش کردن کد با استفاده از SECRET_KEY پروژه."""

    salted = f"{code}:{settings.SECRET_KEY}"
    return hashlib.sha256(salted.encode("utf-8")).hexdigest()


def _generate_code() -> str:
    """تولید کد ۶ رقمی تصادفی."""

    return "".join(
        secrets.choice("0123456789") for _ in range(CODE_LENGTH)
    )


def _normalize_code(code: str) -> str:
    """تبدیل اعداد فارسی به انگلیسی و حذف فاصله‌های اضافی."""

    return (code or "").strip().translate(PERSIAN_DIGITS)


def issue_otp(*, phone_number: str) -> int:
    """
    تولید و ارسال کد یکبارمصرف.

    Returns:
        تعداد ثانیه‌های اعتبار کد.

    Raises:
        OTPError
    """

    if not phone_number:
        raise OTPError("شماره موبایل نامعتبر است.")

    now = timezone.now()

    # بررسی فاصلهٔ حداقلی بین دو ارسال
    recent_otp_exists = PhoneOTP.objects.filter(
        phone_number=phone_number,
        created_at__gte=now - timezone.timedelta(
            seconds=settings.OTP_COOLDOWN_SECONDS
        ),
    ).exists()

    if recent_otp_exists:
        raise OTPError(
            "کد قبلی هنوز معتبر است؛ لطفاً کمی صبر کنید و دوباره تلاش کنید."
        )

    # باطل کردن کدهای قبلی استفاده‌نشده
    PhoneOTP.objects.filter(
        phone_number=phone_number,
        is_used=False,
    ).update(is_used=True)

    # تولید کد جدید
    code = _generate_code()

    # ذخیرهٔ هش‌شده
    otp = PhoneOTP.objects.create(
        phone_number=phone_number,
        code_hash=_hash_code(code),
        expires_at=now + timezone.timedelta(seconds=settings.OTP_TTL_SECONDS),
    )

    message = (
        f"کد ورود شما به Shine: {code}\n"
        "این کد را با کسی به اشتراک نگذارید."
    )

    try:
        send_sms(phone_number=phone_number, message=message)
    except SMSDeliveryError as exc:
        # ارسال ناموفق → حذف کد تا کاربر بتواند دوباره درخواست دهد
        otp.delete()
        logger.error("ارسال OTP ناموفق برای %s: %s", phone_number, exc)
        raise OTPError(
            "ارسال پیامک ناموفق بود؛ لطفاً کمی بعد دوباره تلاش کنید."
        ) from exc

    return settings.OTP_TTL_SECONDS


def verify_otp(*, phone_number: str, code: str):
    """
    بررسی کد یکبارمصرف.

    Returns:
        شماره موبایل در صورت موفقیت.

    Raises:
        OTPError
    """

    if not phone_number:
        raise OTPError("شماره موبایل نامعتبر است.")

    normalized = _normalize_code(code)

    # بررسی اولیهٔ فرمت
    if not normalized.isdigit() or len(normalized) != CODE_LENGTH:
        raise OTPError("کد وارد شده صحیح نیست.")

    # آخرین کد فعال
    otp = (
        PhoneOTP.objects.filter(
            phone_number=phone_number,
            is_used=False,
        )
        .order_by("-created_at")
        .first()
    )

    if otp is None:
        raise OTPError("کد فعالی یافت نشد؛ لطفاً کد جدید درخواست کنید.")

    # بررسی انقضا
    if otp.is_expired:
        raise OTPError("کد منقضی شده است؛ لطفاً کد جدید درخواست کنید.")

    # بررسی تعداد تلاش‌ها
    if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
        otp.is_used = True
        otp.save(update_fields=["is_used"])
        raise OTPError(
            "تعداد تلاش‌های ناموفق بیش از حد مجاز است؛ کد جدید بگیرید."
        )

    # افزایش شمارندهٔ تلاش
    otp.attempts += 1
    otp.save(update_fields=["attempts"])

    # بررسی تطابق کد
    if not secrets.compare_digest(otp.code_hash, _hash_code(normalized)):
        raise OTPError("کد وارد شده صحیح نیست.")

    # موفقیت — مصرف‌شده علامت بزن
    otp.is_used = True
    otp.save(update_fields=["is_used"])

    return phone_number
