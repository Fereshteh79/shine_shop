"""
دروازه ارسال پیامک — قابل تعویض بین سرویس‌دهنده‌ها از طریق تنظیمات.

SMS_PROVIDER=console   → چاپ در لاگ (محیط توسعه)
SMS_PROVIDER=kavenegar → ارسال واقعی با کاوه‌نگار (نیازمند KAVENEGAR_API_KEY)
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

KAVENEGAR_API_URL = "https://api.kavenegar.com/v1/{key}/sms/send.json"


class SMSDeliveryError(Exception):
    """خطای ارسال پیامک."""


def _send_via_console(*, phone_number: str, message: str) -> None:
    logger.info("SMS به %s: %s", phone_number, message)


def _send_via_kavenegar(*, phone_number: str, message: str) -> None:
    api_key = settings.KAVENEGAR_API_KEY

    if not api_key:
        raise SMSDeliveryError("کلید API کاوه‌نگار تنظیم نشده است.")

    try:
        response = requests.get(
            KAVENEGAR_API_URL.format(key=api_key),
            params={"receptor": phone_number, "message": message},
            timeout=settings.PAYMENT_GATEWAY_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("خطای ارسال پیامک کاوه‌نگار: %s", exc)
        raise SMSDeliveryError("ارسال پیامک ناموفق بود؛ بعداً تلاش کنید.") from exc


PROVIDERS = {
    "console": _send_via_console,
    "kavenegar": _send_via_kavenegar,
}


def send_sms(*, phone_number: str, message: str) -> None:
    provider = PROVIDERS.get(settings.SMS_PROVIDER)

    if provider is None:
        raise SMSDeliveryError(
            f"سرویس‌دهنده پیامک نامعتبر است: {settings.SMS_PROVIDER}"
        )

    provider(phone_number=phone_number, message=message)
