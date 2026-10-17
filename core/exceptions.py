"""درخت خطاهای دامنهای پروژه.

قواعد:
  * لایهٔ سرویس هرگز Http404 / django.core.exceptions.ValidationError پرت نمیکند.
  * هر خطا یک `code` رشتهٔ پایدار دارد تا فرانت/لاگ به آن وابسته شود.
  * `http_status` فقط یک راهنمای اختیاری است؛ در view/DRF به کد پاسخ تبدیل میشود.
"""
from __future__ import annotations

from typing import Any, Mapping


class ShineShopError(Exception):
    """ریشهٔ همهٔ خطاهای پروژه."""

    default_message: str = "خطای غیرمنتظره رخ داد."
    default_code: str = "internal_error"
    http_status: int = 500

    def __init__(
            self,
            message: str | None = None,
            *,
            code: str | None = None,
            context: Mapping[str, Any] | None = None,
            **extra: Any,
    ) -> None:
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.context: dict[str, Any] = dict(context or {})
        if extra:
            self.context.update(extra)
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "context": self.context}


# ---------------------------------------------------------------- اعتبارسنجی
class ValidationServiceError(ShineShopError):
    """ورودی نامعتبر در لایهٔ سرویس (نه خطای فرم)."""

    default_message = "دادههای ارسالی نامعتبر است."
    default_code = "validation_error"
    http_status = 400


# ---------------------------------------------------------------- یافت نشدن
class ObjectNotFoundError(ShineShopError):
    default_message = "مورد درخواستی یافت نشد."
    default_code = "not_found"
    http_status = 404


class OrderNotFoundError(ObjectNotFoundError):
    default_message = "سفارش مورد نظر یافت نشد."
    default_code = "order_not_found"


class ProductNotFoundError(ObjectNotFoundError):
    default_message = "محصول مورد نظر یافت نشد."
    default_code = "product_not_found"


class VariantNotFoundError(ObjectNotFoundError):
    default_message = "تنوع محصول مورد نظر یافت نشد."
    default_code = "variant_not_found"


class CartNotFoundError(ObjectNotFoundError):
    default_message = "سبد خرید یافت نشد."
    default_code = "cart_not_found"


class PaymentNotFoundError(ObjectNotFoundError):
    default_message = "تراکنش پرداخت یافت نشد."
    default_code = "payment_not_found"


class OtpNotFoundError(ObjectNotFoundError):
    default_message = "کد تأیید یافت نشد. لطفاً دوباره درخواست کنید."
    default_code = "otp_not_found"


# ---------------------------------------------------------------- دسترسی
class PermissionDeniedError(ShineShopError):
    default_message = "شما به این مورد دسترسی ندارید."
    default_code = "permission_denied"
    http_status = 403


class NotOwnerError(PermissionDeniedError):
    default_message = "این مورد به شما تعلق ندارد."
    default_code = "not_owner"


# ---------------------------------------------------------------- تعارض وضعیت
class ConflictError(ShineShopError):
    """وضعیت فعلی اجازهٔ این عملیات را نمیدهد."""

    default_message = "عملیات در وضعیت فعلی امکانپذیر نیست."
    default_code = "conflict"
    http_status = 409


class InvalidStateTransitionError(ConflictError):
    default_message = "تغییر وضعیت درخواستی مجاز نیست."
    default_code = "invalid_state_transition"


class DuplicateObjectError(ConflictError):
    default_message = "این مورد از قبل وجود دارد."
    default_code = "duplicate_object"


class InsufficientStockError(ConflictError):
    default_message = "موجودی کافی نیست."
    default_code = "insufficient_stock"


# ---------------------------------------------------------------- سبد و سفارش
class CartError(ShineShopError):
    default_code = "cart_error"
    http_status = 400


class CartLimitExceededError(CartError):
    default_message = "تعداد اقلام سبد خرید به حد مجاز رسیده است."
    default_code = "cart_limit_exceeded"


class OrderError(ShineShopError):
    default_code = "order_error"
    http_status = 400


class PaymentExpiredError(OrderError):
    default_message = "مهلت پرداخت این سفارش به پایان رسیده است."
    default_code = "payment_expired"


class OrderAlreadyPaidError(ConflictError):
    default_message = "این سفارش قبلاً پرداخت شده است."
    default_code = "order_already_paid"


# ---------------------------------------------------------------- پرداخت و درگاه
class PaymentServiceError(ShineShopError):
    default_message = "پردازش پرداخت با خطا مواجه شد."
    default_code = "payment_error"
    http_status = 400


class PaymentGatewayError(PaymentServiceError):
    """خطای ارتباط با درگاه (شبکه/تایماوت/پاسخ نامفهوم)."""

    default_message = "ارتباط با درگاه پرداخت برقرار نشد."
    default_code = "payment_gateway_error"
    http_status = 502


class PaymentVerificationError(PaymentServiceError):
    default_message = "تأیید پرداخت ناموفق بود."
    default_code = "payment_verification_failed"


class PaymentAlreadyFinalizedError(ConflictError):
    default_message = "این تراکنش قبلاً نهایی شده است."
    default_code = "payment_already_finalized"


# ---------------------------------------------------------------- OTP و احراز هویت
class OtpError(ShineShopError):
    default_code = "otp_error"
    http_status = 400


class OtpExpiredError(OtpError):
    default_message = "کد تأیید منقضی شده است. لطفاً دوباره درخواست کنید."
    default_code = "otp_expired"


class OtpInvalidError(OtpError):
    default_message = "کد تأیید واردشده صحیح نیست."
    default_code = "otp_invalid"


class TooManyAttemptsError(ShineShopError):
    default_message = "تعداد تلاشهای شما بیش از حد مجاز است. کمی بعد تلاش کنید."
    default_code = "too_many_attempts"
    http_status = 429
