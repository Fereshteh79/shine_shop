"""
درگاه پرداخت زرین‌پال.

این ماژول مسئول:

- ایجاد درخواست پرداخت
- دریافت Authority
- ساخت لینک پرداخت
- تأیید پرداخت
- تبدیل واحد مبلغ
- مدیریت خطاهای شبکه و پاسخ درگاه
- نرمال‌سازی پیام خطای زرین‌پال

واحد مبلغ داخلی پروژه می‌تواند تومان باشد و با استفاده از
ZARINPAL_AMOUNT_MULTIPLIER به واحد موردنیاز درگاه تبدیل می‌شود.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_DOWN
from typing import Any

import requests
from django.conf import settings

from core.exceptions import PaymentServiceError

from .base import (
    BasePaymentGateway,
    PaymentRequestResult,
    PaymentVerifyResult,
)


class ZarinpalGateway(BasePaymentGateway):
    """
    پیاده‌سازی درگاه پرداخت زرین‌پال.
    """

    name = "zarinpal"

    REQUEST_URL = (
        "https://api.zarinpal.com/pg/v4/payment/request.json"
    )

    VERIFY_URL = (
        "https://api.zarinpal.com/pg/v4/payment/verify.json"
    )

    START_PAY_URL = (
        "https://www.zarinpal.com/pg/StartPay/{authority}"
    )

    DEFAULT_TIMEOUT = 15

    SUCCESS_CODES = frozenset(
        {
            100,
            101,
        }
    )

    # =========================================================================
    # Initialization
    # =========================================================================

    def __init__(self) -> None:
        self.merchant_id = str(
            getattr(
                settings,
                "ZARINPAL_MERCHANT_ID",
                "",
            )
            or ""
        ).strip()

        self.timeout = self._get_timeout()

        self.amount_multiplier = self._get_amount_multiplier()

        if not self.merchant_id:
            raise PaymentServiceError(
                "شناسه پذیرنده زرین‌پال تنظیم نشده است.",
                code="zarinpal_merchant_not_configured",
                status_code=500,
            )

    # =========================================================================
    # Configuration
    # =========================================================================

    @staticmethod
    def _get_timeout() -> int:
        """
        دریافت timeout از settings.

        مقدار نامعتبر یا کمتر از یک ثانیه با مقدار پیش‌فرض
        جایگزین می‌شود.
        """

        value = getattr(
            settings,
            "PAYMENT_GATEWAY_TIMEOUT",
            ZarinpalGateway.DEFAULT_TIMEOUT,
        )

        try:
            timeout = int(value)
        except (TypeError, ValueError):
            return ZarinpalGateway.DEFAULT_TIMEOUT

        if timeout <= 0:
            return ZarinpalGateway.DEFAULT_TIMEOUT

        return timeout

    @staticmethod
    def _get_amount_multiplier() -> Decimal:
        """
        ضریب تبدیل مبلغ داخلی به واحد موردنیاز زرین‌پال.

        مثال:

            تومان -> ریال
            multiplier = 10
        """

        value = getattr(
            settings,
            "ZARINPAL_AMOUNT_MULTIPLIER",
            10,
        )

        try:
            multiplier = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            multiplier = Decimal("10")

        if multiplier <= 0:
            multiplier = Decimal("10")

        return multiplier

    # =========================================================================
    # Amount
    # =========================================================================

    def _amount(self, amount: Decimal | int | str) -> int:
        """
        تبدیل مبلغ داخلی به مبلغ قابل ارسال به زرین‌پال.

        مبلغ نهایی باید عدد صحیح باشد.
        """

        try:
            decimal_amount = Decimal(str(amount))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise PaymentServiceError(
                "مبلغ پرداخت نامعتبر است.",
                code="invalid_payment_amount",
                status_code=400,
            ) from exc

        if decimal_amount <= 0:
            raise PaymentServiceError(
                "مبلغ پرداخت باید بیشتر از صفر باشد.",
                code="invalid_payment_amount",
                status_code=400,
            )

        converted = (
                decimal_amount
                * self.amount_multiplier
        )

        return int(
            converted.quantize(
                Decimal("1"),
                rounding=ROUND_DOWN,
            )
        )

    # =========================================================================
    # HTTP Helpers
    # =========================================================================

    @staticmethod
    def _headers() -> dict[str, str]:
        """
        Headerهای موردنیاز API زرین‌پال.
        """

        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @staticmethod
    def _safe_json(response: requests.Response) -> dict[str, Any]:
        """
        تبدیل response به JSON با مدیریت پاسخ نامعتبر.
        """

        try:
            data = response.json()
        except ValueError:
            return {}

        if not isinstance(data, dict):
            return {}

        return data

    # =========================================================================
    # Error Helpers
    # =========================================================================

    @staticmethod
    def _error_message(raw: dict[str, Any]) -> str:
        """
        استخراج پیام خطا از ساختارهای مختلف پاسخ زرین‌پال.
        """

        errors = raw.get("errors")

        if isinstance(errors, dict):
            message = errors.get("message")

            if message:
                return str(message)

            # بعضی پاسخ‌ها ممکن است error یا code داشته باشند.
            error = errors.get("error")

            if error:
                return str(error)

        if isinstance(errors, list):
            messages: list[str] = []

            for item in errors:
                if isinstance(item, dict):
                    message = item.get("message")

                    if message:
                        messages.append(str(message))

                elif item:
                    messages.append(str(item))

            if messages:
                return "، ".join(messages)

        if isinstance(errors, str) and errors.strip():
            return errors.strip()

        return "خطا در ارتباط با درگاه پرداخت."

    @staticmethod
    def _response_data(
            raw: dict[str, Any],
    ) -> dict[str, Any]:
        """
        دریافت بخش data از پاسخ زرین‌پال.
        """

        data = raw.get("data")

        if isinstance(data, dict):
            return data

        return {}

    @classmethod
    def _response_code(
            cls,
            raw: dict[str, Any],
    ) -> int | None:
        """
        استخراج code از پاسخ زرین‌پال.
        """

        data = cls._response_data(raw)

        value = data.get("code")

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _is_success(
            cls,
            raw: dict[str, Any],
    ) -> bool:
        """
        بررسی موفق بودن پاسخ زرین‌پال.
        """

        return cls._response_code(raw) in cls.SUCCESS_CODES

    # =========================================================================
    # Create Payment
    # =========================================================================

    def create_payment(
            self,
            *,
            amount: Decimal | int | str,
            description: str,
            callback_url: str,
            metadata: dict[str, Any] | None = None,
    ) -> PaymentRequestResult:
        """
        ایجاد درخواست پرداخت.

        metadata در API فعلی زرین‌پال مستقیماً ارسال نمی‌شود،
        اما برای سازگاری با BasePaymentGateway دریافت می‌شود.

        اطلاعات metadata بهتر است در مدل Payment خود پروژه ذخیره شود.
        """

        del metadata

        if not description:
            raise PaymentServiceError(
                "توضیحات پرداخت الزامی است.",
                code="invalid_payment_description",
                status_code=400,
            )

        if not callback_url:
            raise PaymentServiceError(
                "آدرس بازگشت پرداخت تنظیم نشده است.",
                code="invalid_payment_callback",
                status_code=400,
            )

        payload = {
            "merchant_id": self.merchant_id,
            "amount": self._amount(amount),
            "description": str(description).strip(),
            "callback_url": str(callback_url).strip(),
        }

        try:
            response = requests.post(
                self.REQUEST_URL,
                json=payload,
                headers=self._headers(),
                timeout=self.timeout,
            )

        except requests.Timeout as exc:
            raise PaymentServiceError(
                "زمان ارتباط با درگاه پرداخت به پایان رسید.",
                code="payment_gateway_timeout",
                status_code=504,
            ) from exc

        except requests.RequestException as exc:
            raise PaymentServiceError(
                "ارتباط با درگاه پرداخت برقرار نشد.",
                code="payment_gateway_connection_error",
                status_code=502,
            ) from exc

        raw = self._safe_json(response)

        # در صورت پاسخ HTTP ناموفق، جزئیات درگاه را بررسی می‌کنیم.
        if not response.ok:
            return PaymentRequestResult(
                success=False,
                message=self._error_message(raw),
                raw_response=raw,
            )

        data = self._response_data(raw)

        authority = str(
            data.get("authority")
            or ""
        ).strip()

        if not self._is_success(raw) or not authority:
            return PaymentRequestResult(
                success=False,
                message=self._error_message(raw),
                raw_response=raw,
            )

        return PaymentRequestResult(
            success=True,
            authority=authority,
            payment_url=self.START_PAY_URL.format(
                authority=authority,
            ),
            raw_response=raw,
        )

    # =========================================================================
    # Verify Payment
    # =========================================================================

    def verify_payment(
            self,
            *,
            amount: Decimal | int | str,
            authority: str,
    ) -> PaymentVerifyResult:
        """
        تأیید تراکنش پرداخت با زرین‌پال.
        """

        authority = str(
            authority or ""
        ).strip()

        if not authority:
            raise PaymentServiceError(
                "شناسه تراکنش زرین‌پال معتبر نیست.",
                code="invalid_payment_authority",
                status_code=400,
            )

        payload = {
            "merchant_id": self.merchant_id,
            "amount": self._amount(amount),
            "authority": authority,
        }

        try:
            response = requests.post(
                self.VERIFY_URL,
                json=payload,
                headers=self._headers(),
                timeout=self.timeout,
            )

        except requests.Timeout as exc:
            raise PaymentServiceError(
                "زمان ارتباط با درگاه برای تأیید پرداخت به پایان رسید.",
                code="payment_verify_timeout",
                status_code=504,
            ) from exc

        except requests.RequestException as exc:
            raise PaymentServiceError(
                "ارتباط با درگاه برای تأیید پرداخت برقرار نشد.",
                code="payment_verify_connection_error",
                status_code=502,
            ) from exc

        raw = self._safe_json(response)

        if not response.ok:
            return PaymentVerifyResult(
                success=False,
                message=self._error_message(raw),
                raw_response=raw,
            )

        data = self._response_data(raw)

        reference_id = str(
            data.get("ref_id")
            or ""
        ).strip()

        if not self._is_success(raw):
            return PaymentVerifyResult(
                success=False,
                message=self._error_message(raw),
                raw_response=raw,
            )

        return PaymentVerifyResult(
            success=True,
            reference_id=reference_id,
            raw_response=raw,
        )


__all__ = [
    "ZarinpalGateway",
]
