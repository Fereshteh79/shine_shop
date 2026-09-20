from core.exceptions import PaymentError

from .base import BasePaymentGateway, PaymentRequestResult, PaymentVerifyResult
from .zarinpal import ZarinpalGateway

__all__ = [
    "BasePaymentGateway",
    "PaymentRequestResult",
    "PaymentVerifyResult",
    "get_payment_gateway",
]

GATEWAYS = {
    ZarinpalGateway.name: ZarinpalGateway,
}


def get_payment_gateway(name: str) -> BasePaymentGateway:
    """بازگرداندن نمونه درگاه پرداخت بر اساس نام — قابل توسعه برای درگاه‌های جدید."""
    gateway_class = GATEWAYS.get(name)

    if gateway_class is None:
        raise PaymentError(f"درگاه پرداخت «{name}» پشتیبانی نمی‌شود.")

    return gateway_class()
