from decimal import Decimal

import requests
from django.conf import settings

from core.exceptions import PaymentError

from .base import (
    BasePaymentGateway,
    PaymentRequestResult,
    PaymentVerifyResult,
)


class ZarinpalGateway(BasePaymentGateway):
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

    def __init__(self):
        self.merchant_id = (
            settings.ZARINPAL_MERCHANT_ID
        )

        self.timeout = (
            settings.PAYMENT_GATEWAY_TIMEOUT
        )

        self.amount_multiplier = (
            settings.ZARINPAL_AMOUNT_MULTIPLIER
        )

        if not self.merchant_id:
            raise PaymentError(
                "شناسه پذیرنده زرین‌پال تنظیم نشده است."
            )

    def _amount(self, amount):
        return int(
            Decimal(amount)
            * self.amount_multiplier
        )

    def _headers(self):
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def create_payment(
            self,
            *,
            amount,
            description,
            callback_url,
            metadata=None,
    ):
        payload = {
            "merchant_id": self.merchant_id,
            "amount": self._amount(amount),
            "description": description,
            "callback_url": callback_url,
        }

        try:
            response = requests.post(
                self.REQUEST_URL,
                json=payload,
                headers=self._headers(),
                timeout=self.timeout,
            )

            response.raise_for_status()
            data = response.json()

        except (
                requests.RequestException,
                ValueError,
        ) as exc:
            raise PaymentError(
                "ارتباط با درگاه پرداخت برقرار نشد."
            ) from exc

        raw = data or {}
        code = (
            raw.get("data", {})
            .get("code")
        )

        authority = (
            raw.get("data", {})
            .get("authority", "")
        )

        if code not in (100, 101) or not authority:
            message = (
                    raw.get("errors", {})
                    or "خطا در ایجاد تراکنش پرداخت."
            )

            return PaymentRequestResult(
                success=False,
                message=str(message),
                raw_response=raw,
            )

        return PaymentRequestResult(
            success=True,
            authority=authority,
            payment_url=self.START_PAY_URL.format(
                authority=authority
            ),
            raw_response=raw,
        )

    def verify_payment(
            self,
            *,
            amount,
            authority,
    ):
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

            response.raise_for_status()
            data = response.json()

        except (
                requests.RequestException,
                ValueError,
        ) as exc:
            raise PaymentError(
                "ارتباط با درگاه برای تأیید پرداخت برقرار نشد."
            ) from exc

        raw = data or {}

        code = (
            raw.get("data", {})
            .get("code")
        )

        reference_id = str(
            raw.get("data", {})
            .get("ref_id", "")
        )

        if code not in (100, 101):
            message = (
                    raw.get("errors", {})
                    or "پرداخت توسط درگاه تأیید نشد."
            )

            return PaymentVerifyResult(
                success=False,
                message=str(message),
                raw_response=raw,
            )

        return PaymentVerifyResult(
            success=True,
            reference_id=reference_id,
            raw_response=raw,
        )
