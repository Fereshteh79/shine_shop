"""لایهٔ ارسال پیامک با پشتیبانی از چند سرویس‌دهنده (Strategy Pattern)."""
from __future__ import annotations

import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from accounts.utils import mask_phone

logger = logging.getLogger(__name__)

DEFAULT_BACKEND = "accounts.sms.ConsoleSMSBackend"


class BaseSMSBackend:
    """قرارداد مشترک همهٔ سرویس‌دهنده‌های پیامک."""

    def send(self, phone_number: str, message: str) -> bool:  # pragma: no cover
        raise NotImplementedError


class ConsoleSMSBackend(BaseSMSBackend):
    """مناسب توسعه: پیامک فقط در لاگ ثبت می‌شود و هزینه ندارد."""

    def send(self, phone_number: str, message: str) -> bool:
        logger.info("[SMS:console] to=%s message=%s", mask_phone(phone_number), message)
        return True


class KavenegarSMSBackend(BaseSMSBackend):
    """ارسال پیامک از طریق وب‌سرویس کاوه‌نگار."""

    api_url = "https://api.kavenegar.com/v1/{api_key}/sms/send.json"

    def __init__(
            self,
            api_key: str | None = None,
            sender: str | None = None,
            timeout: int = 10,
    ):
        self.api_key = api_key or getattr(settings, "KAVENEGAR_API_KEY", "")
        self.sender = sender or getattr(settings, "KAVENEGAR_SENDER", "")
        self.timeout = timeout
        if not self.api_key:
            raise ImproperlyConfigured("KAVENEGAR_API_KEY تنظیم نشده است.")

    def send(self, phone_number: str, message: str) -> bool:
        import requests  # فقط همین سرویس‌دهنده به requests نیاز دارد

        try:
            response = requests.post(
                self.api_url.format(api_key=self.api_key),
                data={"receptor": phone_number, "sender": self.sender, "message": message},
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            logger.exception("ارسال پیامک به %s ناموفق بود.", mask_phone(phone_number))
            return False

        status = payload.get("return", {}).get("status")
        if status != 200:
            logger.error("کاوه‌نگار خطا داد: %s", payload)
            return False
        return True


def get_sms_backend() -> BaseSMSBackend:
    """سرویس‌دهندهٔ فعال را از settings می‌سازد."""
    return import_string(getattr(settings, "SMS_BACKEND", DEFAULT_BACKEND))()


def send_sms(phone_number: str, message: str) -> bool:
    """نقطهٔ ورود واحد ارسال پیامک؛ هیچ‌وقت exception پرت نمی‌کند."""
    try:
        return get_sms_backend().send(phone_number, message)
    except Exception:
        logger.exception("ارسال پیامک شکست خورد (phone=%s).", mask_phone(phone_number))
        return False
