from dataclasses import dataclass
from typing import Any


@dataclass
class PaymentRequestResult:
    success: bool
    authority: str = ""
    payment_url: str = ""
    message: str = ""
    raw_response: dict[str, Any] | None = None


@dataclass
class PaymentVerifyResult:
    success: bool
    reference_id: str = ""
    message: str = ""
    raw_response: dict[str, Any] | None = None


class BasePaymentGateway:
    name = "base"

    def create_payment(
            self,
            *,
            amount,
            description,
            callback_url,
            metadata=None,
    ):
        raise NotImplementedError

    def verify_payment(
            self,
            *,
            amount,
            authority,
    ):
        raise NotImplementedError
