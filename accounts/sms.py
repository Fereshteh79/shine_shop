# accounts/sms.py
"""
لایهٔ انتزاعی ارسال پیامک.

در حال حاضر یک پیاده‌سازی ساختگی (dummy) دارد.
برای Production باید با سرویس واقعی (مثلاً کاوه‌نگار، مِلی پیامک و …) جایگزین شود.
"""

import logging

logger = logging.getLogger(__name__)


class SMSDeliveryError(Exception):
    """خطا در ارسال پیامک."""


def send_sms(*, phone_number: str, message: str) -> None:
    """
    ارسال پیامک به شمارهٔ داده‌شده.

    Raises:
        SMSDeliveryError: در صورت شکست ارسال.
    """

    # TODO: پیاده‌سازی واقعی با API سرویس پیامک
    logger.info("SMS → %s: %s", phone_number, message)

    # شبیه‌سازی خطای تصادفی برای تست (در Production حذف شود)
    # import random
    # if random.random() < 0.1:
    #     raise SMSDeliveryError("ارسال پیامک با خطا مواجه شد.")
