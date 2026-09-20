"""
مدیریت کد یکبارمصرف پیامکی (OTP).

- کد ۶ رقمی تولید و به‌صورت هش‌شده ذخیره می‌شود (نه متن ساده)
- محدودیت زمانی، محدودیت تلاش و فاصله حداقلی بین ارسال‌ها
"""

import hashlib
import secrets

from django.conf import settings
from django.utils import timezone

from .models import PhoneOTP
from .sms import send_sms

CODE_LENGTH = 6


class OTPError(Exception):
    """خطای عمومی OTP با پیام قابل نمایش به کاربر."""


def _hash_code(code: str) -> str:
    """هش کد با salt مخفی پروژه — کد هرگز به‌صورت متن ذخیره نمی‌شود."""
    salted = f"{code}:{settings.SECRET_KEY}"
    return hashlib.sha256(salted.encode()).hexdigest()


def _generate_code() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(CODE_LENGTH))


def issue_otp(*, phone_number: str) -> int:
    """
    تولید و ارسال کد برای شماره داده‌شده.

    برمی‌گرداند: ثانیه‌های باقی‌مانده اعتبار کد.
    خطاها: OTPError با پیام فارسی.
    """
    now = timezone.now()

    # فاصله حداقلی بین دو ارسال — ضد اسپم
    last = PhoneOTP.objects.filter(
        phone_number=phone_number,
        created_at__gte=now - timezone.timedelta(
            seconds=settings.OTP_COOLDOWN_SECONDS,
        ),
    ).exists()

    if last:
        raise OTPError(
            "کد قبلی هنوز معتبر است؛ لطفاً کمی صبر کنید و دوباره تلاش کنید."
        )

    # باطل کردن کدهای قبلی استفاده‌نشده این شماره
    PhoneOTP.objects.filter(
        phone_number=phone_number,
        is_used=False,
    ).update(is_used=True)

    code = _generate_code()

    otp = PhoneOTP.objects.create(
        phone_number=phone_number,
        code_hash=_hash_code(code),
        expires_at=now + timezone.timedelta(seconds=settings.OTP_TTL_SECONDS),
    )

    message = (
        f"کد ورود شما به Shine: {code}\n"
        f"این کد را با کسی به اشتراک نگذارید."
    )

    send_sms(phone_number=phone_number, message=message)

    return settings.OTP_TTL_SECONDS


def verify_otp(*, phone_number: str, code: str):
    """
    بررسی کد و بازگرداندن شماره در صورت موفقیت.

    خطاها: OTPError با پیام فارسی.
    """
    normalized = (code or "").strip().replace("۰", "0").replace("۱", "1") \
        .replace("۲", "2").replace("۳", "3").replace("۴", "4") \
        .replace("۵", "5").replace("۶", "6").replace("۷", "7") \
        .replace("۸", "8").replace("۹", "9")

    otp = (
        PhoneOTP.objects
        .filter(phone_number=phone_number, is_used=False)
        .order_by("-created_at")
        .first()
    )

    if otp is None:
        raise OTPError("کد فعالی یافت نشد؛ لطفاً کد جدید درخواست کنید.")

    if otp.is_expired:
        raise OTPError("کد منقضی شده است؛ لطفاً کد جدید درخواست کنید.")

    if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
        otp.is_used = True
        otp.save(update_fields=["is_used"])
        raise OTPError("تعداد تلاش‌های ناموفق بیش از حد مجاز است؛ کد جدید بگیرید.")

    otp.attempts += 1
    otp.save(update_fields=["attempts"])

    if not secrets.compare_digest(otp.code_hash, _hash_code(normalized)):
        raise OTPError("کد وارد شده صحیح نیست.")

    otp.is_used = True
    otp.save(update_fields=["is_used"])

    return phone_number
