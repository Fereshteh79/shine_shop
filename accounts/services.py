"""لایه منطق کسب‌وکار اپ accounts."""

from __future__ import annotations

import logging
from datetime import timedelta

from django.contrib.auth.password_validation import (
    validate_password,
)
from django.db import transaction
from django.utils import timezone

from accounts import otp as otp_tools
from accounts.models import PhoneOTP, Profile, User
from accounts.selectors import (
    count_recent_otps,
    get_user_by_phone,
    last_otp_created_at,
)
from accounts.sms import send_sms
from accounts.utils import (
    is_valid_mobile,
    normalize_digits,
    normalize_phone,
)

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# ثابت‌های دامنه
# --------------------------------------------------------------------------- #

OTP_PURPOSE_LOGIN = "login"
OTP_PURPOSE_PHONE_VERIFICATION = PhoneOTP.Purpose.REGISTER
OTP_PURPOSE_PASSWORD_RESET = PhoneOTP.Purpose.RESET_PASSWORD


# --------------------------------------------------------------------------- #
# خطاهای دامنه
# --------------------------------------------------------------------------- #

class OTPError(Exception):
    """خطای پایه فرایند OTP."""

    default_message = (
        "خطایی در فرایند کد یکبارمصرف رخ داد."
    )

    def __init__(
            self,
            message: str | None = None,
    ):
        self.message = (
                message or self.default_message
        )
        super().__init__(self.message)


class OTPThrottled(OTPError):
    default_message = (
        "درخواست‌های شما بیش از حد مجاز است. "
        "کمی بعد دوباره تلاش کنید."
    )


class OTPNotFound(OTPError):
    default_message = (
        "کدی برای این شماره یافت نشد. "
        "دوباره درخواست کد کنید."
    )


class OTPExpired(OTPError):
    default_message = (
        "کد منقضی شده است. "
        "کد جدید درخواست کنید."
    )


class OTPLocked(OTPError):
    default_message = (
        "تعداد تلاش‌های ناموفق زیاد است. "
        "کد جدید درخواست کنید."
    )


class OTPInvalid(OTPError):
    default_message = "کد وارد شده صحیح نیست."

    def __init__(
            self,
            attempts_left: int | None = None,
    ):
        message = self.default_message

        if attempts_left is not None:
            message = (
                f"{message} "
                f"({attempts_left} تلاش باقی مانده)"
            )

        super().__init__(message)

        self.attempts_left = attempts_left


class OTPAlreadyUsed(OTPError):
    default_message = (
        "این کد قبلاً استفاده شده است."
    )


class SMSSendFailed(OTPError):
    default_message = (
        "ارسال پیامک ناموفق بود. "
        "لطفاً کمی بعد دوباره تلاش کنید."
    )


# --------------------------------------------------------------------------- #
# User
# --------------------------------------------------------------------------- #

def create_user(
        *,
        phone_number: str,
        password: str | None = None,
        first_name: str = "",
        last_name: str = "",
        email: str | None = None,
        is_phone_verified: bool = False,
) -> User:
    """ساخت User جدید."""

    phone_number = normalize_phone(
        phone_number
    )

    if password:
        validate_password(
            password
        )

    user = User.objects.create_user(
        phone_number=phone_number,
        password=password,
        first_name=first_name,
        last_name=last_name,
        email=email,
        is_phone_verified=is_phone_verified,
    )

    return user


def get_or_create_phone_user(
        phone_number: str,
) -> User:
    """
    دریافت User موجود یا ایجاد User جدید
    پس از احراز موفق شماره موبایل.
    """

    phone_number = normalize_phone(
        phone_number
    )

    user = get_user_by_phone(
        phone_number
    )

    if user is not None:
        return mark_phone_verified(user)

    try:
        user = create_user(
            phone_number=phone_number,
            password=None,
            is_phone_verified=True,
        )
    except Exception:
        # در شرایط race condition ممکن است درخواست دیگری
        # همزمان User را ایجاد کرده باشد.
        user = get_user_by_phone(
            phone_number
        )

        if user is None:
            raise

        return mark_phone_verified(user)

    return user


def mark_phone_verified(
        user: User,
) -> User:
    """تأیید شماره موبایل کاربر."""

    if not user.is_phone_verified:
        user.is_phone_verified = True

        user.save(
            update_fields=[
                "is_phone_verified",
                "updated_at",
            ]
        )

    return user


def change_password(
        user: User,
        raw_password: str,
) -> User:
    """تغییر رمز عبور."""

    validate_password(
        raw_password,
        user,
    )

    user.set_password(
        raw_password
    )

    user.save(
        update_fields=[
            "password",
            "updated_at",
        ]
    )

    return user


@transaction.atomic
def update_profile(
        user: User,
        *,
        user_data: dict | None = None,
        profile_data: dict | None = None,
        avatar=None,
) -> Profile:
    """به‌روزرسانی اطلاعات User و Profile."""

    user_data = user_data or {}
    profile_data = dict(
        profile_data or {}
    )

    user_fields = [
        field
        for field in (
            "first_name",
            "last_name",
            "email",
        )
        if field in user_data
    ]

    for field in user_fields:
        setattr(
            user,
            field,
            user_data[field],
        )

    if user_fields:
        user.save(
            update_fields=[
                *user_fields,
                "updated_at",
            ]
        )

    profile, _ = Profile.objects.get_or_create(
        user=user
    )

    old_avatar = profile.avatar

    if avatar is not None:
        profile_data["avatar"] = avatar

    for field, value in profile_data.items():
        setattr(
            profile,
            field,
            value,
        )

    profile.save()

    if (
            avatar is not None
            and old_avatar
            and old_avatar.name != profile.avatar.name
    ):
        old_avatar.delete(
            save=False
        )

    return profile


# --------------------------------------------------------------------------- #
# OTP
# --------------------------------------------------------------------------- #

def normalize_otp_code(
        code: str,
) -> str:
    """نرمال‌سازی کد OTP."""

    return normalize_digits(
        code
    ).strip()


def _enforce_rate_limits(
        phone_number: str,
        ip_address: str | None,
) -> None:
    """اعمال محدودیت تعداد درخواست OTP."""

    now = timezone.now()

    cooldown = (
        otp_tools.otp_resend_cooldown()
    )

    last_created = last_otp_created_at(
        phone_number
    )

    if last_created:
        elapsed = (
                now - last_created
        ).total_seconds()

        if elapsed < cooldown:
            remaining = max(
                int(cooldown - elapsed),
                1,
            )

            raise OTPThrottled(
                f"برای ارسال دوباره "
                f"{remaining} ثانیه صبر کنید."
            )

    hourly_phone = count_recent_otps(
        since=now - timedelta(hours=1),
        phone_number=phone_number,
    )

    if (
            hourly_phone
            >= otp_tools.otp_max_sends_per_phone_per_hour()
    ):
        raise OTPThrottled(
            "تعداد درخواست‌های این شماره "
            "در یک ساعت گذشته زیاد بوده است."
        )

    if ip_address:
        hourly_ip = count_recent_otps(
            since=now - timedelta(hours=1),
            ip_address=ip_address,
        )

        if (
                hourly_ip
                >= otp_tools.otp_max_sends_per_ip_per_hour()
        ):
            raise OTPThrottled(
                "از این شبکه درخواست‌های زیادی "
                "ثبت شده است."
            )


def invalidate_pending_otps(
        phone_number: str,
        purpose: str,
) -> int:
    """باطل کردن OTPهای قبلی."""

    phone_number = normalize_phone(
        phone_number
    )

    return (
        PhoneOTP.objects
        .filter(
            phone_number=phone_number,
            purpose=purpose,
            is_used=False,
        )
        .update(is_used=True)
    )


def request_otp(
        *,
        phone_number: str,
        purpose: str,
        ip_address: str | None = None,
) -> PhoneOTP:
    """ایجاد و ارسال OTP."""

    phone_number = normalize_phone(
        phone_number
    )

    if not is_valid_mobile(
            phone_number
    ):
        raise OTPError(
            "شماره موبایل معتبر نیست."
        )

    _enforce_rate_limits(
        phone_number,
        ip_address,
    )

    invalidate_pending_otps(
        phone_number,
        purpose,
    )

    code = otp_tools.generate_otp()

    otp_record = PhoneOTP.objects.create(
        phone_number=phone_number,
        purpose=purpose,
        code_hash=otp_tools.hash_otp(code),
        expires_at=(
                timezone.now()
                + otp_tools.otp_ttl()
        ),
        ip_address=ip_address,
    )

    try:
        sent = send_sms(
            phone_number,
            otp_tools.build_otp_message(code),
        )
    except Exception:
        logger.exception(
            "ارسال OTP با خطا مواجه شد."
        )
        otp_record.delete()
        raise SMSSendFailed()

    if not sent:
        otp_record.delete()
        raise SMSSendFailed()

    logger.info(
        "OTP ارسال شد. purpose=%s phone=%s",
        purpose,
        phone_number,
    )

    return otp_record


@transaction.atomic
def verify_otp(
        *,
        phone_number: str,
        code: str,
        purpose: str,
) -> PhoneOTP:
    """بررسی و مصرف OTP."""

    phone_number = normalize_phone(
        phone_number
    )

    code = normalize_otp_code(
        code
    )

    otp_record = (
        PhoneOTP.objects
        .select_for_update()
        .filter(
            phone_number=phone_number,
            purpose=purpose,
            is_used=False,
        )
        .order_by("-created_at")
        .first()
    )

    if otp_record is None:
        raise OTPNotFound()

    if otp_record.is_locked:
        raise OTPLocked()

    if otp_record.is_expired:
        raise OTPExpired()

    if not otp_tools.check_otp(
            code,
            otp_record.code_hash,
    ):
        otp_record.attempts += 1

        otp_record.save(
            update_fields=["attempts"]
        )

        if otp_record.is_locked:
            raise OTPLocked()

        raise OTPInvalid(
            attempts_left=(
                otp_record.attempts_left
            )
        )

    return otp_record.mark_used(
        verified=True
    )


def purge_expired_otps(
        days: int = 1,
) -> int:
    """پاک‌سازی OTPهای قدیمی."""

    if days < 0:
        raise ValueError(
            "days نمی‌تواند منفی باشد."
        )

    threshold = (
            timezone.now()
            - timedelta(days=days)
    )

    deleted, _ = (
        PhoneOTP.objects
        .filter(
            expires_at__lt=threshold
        )
        .delete()
    )

    return deleted
