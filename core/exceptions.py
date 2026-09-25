# core/exception.py
"""
مدیریت خطاهای پروژه Shine Gallery.

این فایل مسئول:

1. تعریف خطاهای دامنه و کسب‌وکار
2. تبدیل خطاهای Django به پاسخ استاندارد API
3. تبدیل خطاهای Django REST Framework به پاسخ استاندارد API
4. فراهم کردن helperهای ساده برای ایجاد خطا در لایه سرویس

ساختار عمومی پاسخ API:

{
    "detail": "پیام خطا",
    "code": "error_code"
}

در خطاهای validation:

{
    "detail": "اطلاعات ارسال‌شده معتبر نیست.",
    "code": "validation_error",
    "details": {...}
}
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from django.core.exceptions import (
    PermissionDenied as DjangoPermissionDenied,
    ValidationError as DjangoValidationError,
)
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied as DRFPermissionDenied,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

# ============================================================================
# Constants
# ============================================================================

DEFAULT_SERVICE_ERROR_CODE = "service_error"
DEFAULT_API_ERROR_CODE = "api_error"

VALIDATION_ERROR_CODE = "validation_error"
NOT_FOUND_ERROR_CODE = "not_found"
PERMISSION_ERROR_CODE = "permission_denied"
AUTHENTICATION_ERROR_CODE = "not_authenticated"
CONFLICT_ERROR_CODE = "conflict"
PAYMENT_ERROR_CODE = "payment_error"
INSUFFICIENT_STOCK_ERROR_CODE = "insufficient_stock"
ORDER_STATE_ERROR_CODE = "invalid_order_state"

DEFAULT_VALIDATION_MESSAGE = "اطلاعات ارسال‌شده معتبر نیست."
DEFAULT_NOT_FOUND_MESSAGE = "مورد موردنظر پیدا نشد."
DEFAULT_PERMISSION_MESSAGE = "شما اجازه انجام این عملیات را ندارید."
DEFAULT_AUTHENTICATION_MESSAGE = (
    "برای انجام این عملیات باید وارد حساب کاربری شوید."
)
DEFAULT_CONFLICT_MESSAGE = (
    "امکان انجام این عملیات در وضعیت فعلی وجود ندارد."
)
DEFAULT_PAYMENT_MESSAGE = "پرداخت با خطا مواجه شد."
DEFAULT_INSUFFICIENT_STOCK_MESSAGE = "موجودی محصول کافی نیست."
DEFAULT_ORDER_STATE_MESSAGE = (
    "تغییر وضعیت سفارش در این مرحله مجاز نیست."
)


# ============================================================================
# Base Service Error
# ============================================================================


class ServiceError(Exception):
    """
    خطای پایه برای خطاهای قابل انتظار لایه سرویس.

    این خطا برای شرایطی استفاده می‌شود که از نظر فنی exception
    محسوب می‌شوند اما بخشی از منطق قابل انتظار برنامه هستند.

    مثال:

        raise ServiceError(
            "موجودی محصول کافی نیست.",
            code="insufficient_stock",
            status_code=409,
        )
    """

    default_message = "خطای غیرمنتظره در پردازش درخواست."
    default_code = DEFAULT_SERVICE_ERROR_CODE
    default_status_code = status.HTTP_400_BAD_REQUEST

    def __init__(
            self,
            message: str | None = None,
            *,
            code: str | None = None,
            status_code: int | None = None,
            details: Any | None = None,
    ) -> None:
        self.message = (
            str(message)
            if message is not None
            else self.default_message
        )

        self.code = (
            str(code)
            if code is not None
            else self.default_code
        )

        self.status_code = (
            int(status_code)
            if status_code is not None
            else self.default_status_code
        )

        self.details = details

        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


# ============================================================================
# Domain / Business Errors
# ============================================================================


class ValidationServiceError(ServiceError):
    """
    خطای اعتبارسنجی داده یا قوانین کسب‌وکار.
    """

    default_message = DEFAULT_VALIDATION_MESSAGE
    default_code = VALIDATION_ERROR_CODE
    default_status_code = status.HTTP_400_BAD_REQUEST


class NotFoundServiceError(ServiceError):
    """
    منبع یا شیء موردنظر پیدا نشد.
    """

    default_message = DEFAULT_NOT_FOUND_MESSAGE
    default_code = NOT_FOUND_ERROR_CODE
    default_status_code = status.HTTP_404_NOT_FOUND


class PermissionServiceError(ServiceError):
    """
    کاربر احراز هویت شده ولی اجازه انجام عملیات را ندارد.
    """

    default_message = DEFAULT_PERMISSION_MESSAGE
    default_code = PERMISSION_ERROR_CODE
    default_status_code = status.HTTP_403_FORBIDDEN


class AuthenticationServiceError(ServiceError):
    """
    کاربر برای انجام عملیات احراز هویت نشده است.
    """

    default_message = DEFAULT_AUTHENTICATION_MESSAGE
    default_code = AUTHENTICATION_ERROR_CODE
    default_status_code = status.HTTP_401_UNAUTHORIZED


class ConflictServiceError(ServiceError):
    """
    عملیات با وضعیت فعلی منبع تعارض دارد.
    """

    default_message = DEFAULT_CONFLICT_MESSAGE
    default_code = CONFLICT_ERROR_CODE
    default_status_code = status.HTTP_409_CONFLICT


class PaymentServiceError(ServiceError):
    """خطای مربوط به پرداخت یا درگاه بانکی."""

    default_message = "پرداخت با خطا مواجه شد."

    default_code = PAYMENT_ERROR_CODE

    default_status_code = 400


# سازگاری با ماژول‌هایی که نام کوتاه‌تر را ایمپورت می‌کنند
PaymentError = PaymentServiceError


class InsufficientStockError(ServiceError):
    """موجودی محصول برای انجام سفارش کافی نیست."""

    default_message = DEFAULT_INSUFFICIENT_STOCK_MESSAGE
    default_code = INSUFFICIENT_STOCK_ERROR_CODE
    default_status_code = status.HTTP_409_CONFLICT


class OrderStateError(ServiceError):
    """
    تغییر وضعیت سفارش طبق state machine مجاز نیست.
    """

    default_message = DEFAULT_ORDER_STATE_MESSAGE
    default_code = ORDER_STATE_ERROR_CODE
    default_status_code = status.HTTP_409_CONFLICT


# سازگاری با کدهای قدیمی احتمالی پروژه.
ValidationError = ValidationServiceError


# ============================================================================
# Validation Normalization
# ============================================================================


def _normalize_validation_error(
        exc: DjangoValidationError,
) -> Any:
    """
    Django ValidationError را به ساختار قابل استفاده در API تبدیل می‌کند.

    حالت‌های معمول Django:

        message_dict
        messages
    """

    if hasattr(exc, "message_dict"):
        message_dict = exc.message_dict

        if isinstance(message_dict, Mapping):
            return dict(message_dict)

        return message_dict

    messages = getattr(exc, "messages", None)

    if messages is not None:
        messages = list(messages)

        if len(messages) == 1:
            return messages[0]

        return messages

    return str(exc)


# ============================================================================
# Response Builders
# ============================================================================


def _build_error_data(
        *,
        message: Any,
        code: str,
        details: Any | None = None,
) -> dict[str, Any]:
    """
    ساخت بدنه استاندارد پاسخ خطا.
    """

    data: dict[str, Any] = {
        "detail": message,
        "code": code,
    }

    if details is not None:
        data["details"] = details

    return data


def _build_response(
        *,
        message: Any,
        code: str,
        status_code: int,
        details: Any | None = None,
        headers: Mapping[str, str] | None = None,
) -> Response:
    """
    ساخت Response استاندارد خطا.
    """

    data = _build_error_data(
        message=message,
        code=code,
        details=details,
    )

    return Response(
        data,
        status=status_code,
        headers=headers,
    )


# ============================================================================
# DRF Detail Helpers
# ============================================================================


def _extract_drf_detail(
        data: Any,
) -> Any:
    """
    استخراج detail از response.data مربوط به DRF.

    اگر detail وجود نداشته باشد، کل data برگردانده می‌شود.
    """

    if isinstance(data, Mapping):
        if "detail" in data:
            return data["detail"]

        return data

    return data


def _extract_drf_code(
        exc: APIException,
) -> str:
    """
    استخراج کد استاندارد از DRF exception.
    """

    code = getattr(exc, "default_code", None)

    if code:
        return str(code)

    return DEFAULT_API_ERROR_CODE


# ============================================================================
# Main Exception Handler
# ============================================================================


def api_exception_handler(
        exc: Exception,
        context: Mapping[str, Any],
) -> Response | None:
    """
    Exception Handler اصلی پروژه.

    این handler ابتدا خطاهای اختصاصی پروژه را بررسی می‌کند
    و سپس خطاهای Django و DRF را به ساختار استاندارد تبدیل می‌کند.

    اگر DRF بتواند exception را مدیریت کند، response آن نیز
    به ساختار استاندارد پروژه تبدیل خواهد شد.

    برای exceptionهای ناشناخته، None برگردانده می‌شود تا
    DRF/Django بتواند رفتار پیش‌فرض خود را انجام دهد.
    """

    # ------------------------------------------------------------------------
    # 1. Project Service Errors
    # ------------------------------------------------------------------------

    if isinstance(exc, ServiceError):
        return _build_response(
            message=exc.message,
            code=exc.code,
            status_code=exc.status_code,
            details=exc.details,
        )

    # ------------------------------------------------------------------------
    # 2. Django ValidationError
    # ------------------------------------------------------------------------

    if isinstance(exc, DjangoValidationError):
        details = _normalize_validation_error(exc)

        return _build_response(
            message=DEFAULT_VALIDATION_MESSAGE,
            code=VALIDATION_ERROR_CODE,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )

    # ------------------------------------------------------------------------
    # 3. Django Http404
    # ------------------------------------------------------------------------

    if isinstance(exc, Http404):
        return _build_response(
            message=DEFAULT_NOT_FOUND_MESSAGE,
            code=NOT_FOUND_ERROR_CODE,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # ------------------------------------------------------------------------
    # 4. Django PermissionDenied
    # ------------------------------------------------------------------------

    if isinstance(exc, DjangoPermissionDenied):
        return _build_response(
            message=DEFAULT_PERMISSION_MESSAGE,
            code=PERMISSION_ERROR_CODE,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # ------------------------------------------------------------------------
    # 5. Let DRF handle its own exception first
    # ------------------------------------------------------------------------

    response = drf_exception_handler(
        exc,
        context,
    )

    if response is None:
        return None

    # ------------------------------------------------------------------------
    # 6. Authentication
    # ------------------------------------------------------------------------

    if isinstance(
            exc,
            (
                    NotAuthenticated,
                    AuthenticationFailed,
            ),
    ):
        detail = _extract_drf_detail(response.data)

        if not detail:
            detail = DEFAULT_AUTHENTICATION_MESSAGE

        code = (
            AUTHENTICATION_ERROR_CODE
            if isinstance(exc, NotAuthenticated)
            else _extract_drf_code(exc)
        )

        return _build_response(
            message=detail,
            code=code,
            status_code=response.status_code,
            headers=response.headers,
        )

    # ------------------------------------------------------------------------
    # 7. DRF PermissionDenied
    # ------------------------------------------------------------------------

    if isinstance(exc, DRFPermissionDenied):
        detail = _extract_drf_detail(response.data)

        if not detail:
            detail = DEFAULT_PERMISSION_MESSAGE

        return _build_response(
            message=detail,
            code=PERMISSION_ERROR_CODE,
            status_code=status.HTTP_403_FORBIDDEN,
            headers=response.headers,
        )

    # ------------------------------------------------------------------------
    # 8. DRF Validation Errors
    # ------------------------------------------------------------------------

    if response.status_code == status.HTTP_400_BAD_REQUEST:
        return _build_response(
            message=DEFAULT_VALIDATION_MESSAGE,
            code=VALIDATION_ERROR_CODE,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=response.data,
            headers=response.headers,
        )

    # ------------------------------------------------------------------------
    # 9. Generic DRF APIException
    # ------------------------------------------------------------------------

    if isinstance(exc, APIException):
        detail = _extract_drf_detail(response.data)
        code = _extract_drf_code(exc)

        return _build_response(
            message=detail,
            code=code,
            status_code=response.status_code,
            headers=response.headers,
        )

    # ------------------------------------------------------------------------
    # 10. Fallback
    # ------------------------------------------------------------------------

    return response


# ============================================================================
# Service Error Helpers
# ============================================================================


def service_error(
        message: str,
        *,
        code: str = DEFAULT_SERVICE_ERROR_CODE,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Any | None = None,
) -> ServiceError:
    """
    ساخت سریع ServiceError.

    مثال:

        raise service_error(
            "موجودی کافی نیست.",
            code="insufficient_stock",
            status_code=409,
        )
    """

    return ServiceError(
        message,
        code=code,
        status_code=status_code,
        details=details,
    )


def validation_error(
        message: str = DEFAULT_VALIDATION_MESSAGE,
        *,
        details: Any | None = None,
) -> ValidationServiceError:
    """
    ساخت خطای validation.
    """

    return ValidationServiceError(
        message,
        details=details,
    )


def not_found_error(
        message: str = DEFAULT_NOT_FOUND_MESSAGE,
        *,
        details: Any | None = None,
) -> NotFoundServiceError:
    """
    ساخت خطای not found.
    """

    return NotFoundServiceError(
        message,
        details=details,
    )


def permission_error(
        message: str = DEFAULT_PERMISSION_MESSAGE,
        *,
        details: Any | None = None,
) -> PermissionServiceError:
    """
    ساخت خطای permission.
    """

    return PermissionServiceError(
        message,
        details=details,
    )


def authentication_error(
        message: str = DEFAULT_AUTHENTICATION_MESSAGE,
        *,
        details: Any | None = None,
) -> AuthenticationServiceError:
    """
    ساخت خطای authentication.
    """

    return AuthenticationServiceError(
        message,
        details=details,
    )


def conflict_error(
        message: str = DEFAULT_CONFLICT_MESSAGE,
        *,
        details: Any | None = None,
) -> ConflictServiceError:
    """
    ساخت خطای conflict.
    """

    return ConflictServiceError(
        message,
        details=details,
    )


def payment_error(
        message: str = DEFAULT_PAYMENT_MESSAGE,
        *,
        details: Any | None = None,
) -> PaymentServiceError:
    """
    ساخت خطای پرداخت.
    """

    return PaymentServiceError(
        message,
        details=details,
    )


def insufficient_stock_error(
        message: str = DEFAULT_INSUFFICIENT_STOCK_MESSAGE,
        *,
        details: Any | None = None,
) -> InsufficientStockError:
    """
    ساخت خطای کمبود موجودی.
    """

    return InsufficientStockError(
        message,
        details=details,
    )


def order_state_error(
        message: str = DEFAULT_ORDER_STATE_MESSAGE,
        *,
        details: Any | None = None,
) -> OrderStateError:
    """
    ساخت خطای وضعیت سفارش.
    """

    return OrderStateError(
        message,
        details=details,
    )


__all__ = [
    "ServiceError",
    "ValidationServiceError",
    "ValidationError",
    "NotFoundServiceError",
    "PermissionServiceError",
    "AuthenticationServiceError",
    "ConflictServiceError",
    "PaymentServiceError",
    "InsufficientStockError",
    "OrderStateError",
    "api_exception_handler",
    "service_error",
    "validation_error",
    "not_found_error",
    "permission_error",
    "authentication_error",
    "conflict_error",
    "payment_error",
    "insufficient_stock_error",
    "order_state_error",
]
