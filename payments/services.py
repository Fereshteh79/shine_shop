from __future__ import annotations

import uuid

from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from core.constants import OrderStatus, PaymentStatus
from core.exceptions import (
    PaymentServiceError,
    ValidationServiceError,
)

from orders.models import Order
from orders.services import OrderService

from .gateways import get_payment_gateway
from .models import Payment


class PaymentService:
    """
    سرویس اصلی مدیریت پرداخت سفارش‌ها.

    مسئولیت‌ها:
    - ایجاد تراکنش پرداخت
    - دریافت آدرس درگاه
    - جلوگیری از ایجاد پرداخت‌های تکراری
    - تأیید تراکنش پس از بازگشت از درگاه
    - به‌روزرسانی وضعیت Payment و Order
    - مدیریت تراکنش‌های منقضی یا ناموفق
    """

    @staticmethod
    def _generate_transaction_id() -> str:
        """
        تولید شناسه یکتا برای تراکنش داخلی فروشگاه.
        """
        return uuid.uuid4().hex

    @staticmethod
    def _build_callback_url(request) -> str:
        """
        ساخت URL بازگشت از درگاه.
        """
        if request is None:
            raise PaymentServiceError(
                "آدرس بازگشت پرداخت مشخص نشده است.",
                code="payment_callback_missing",
                status_code=400,
            )

        return request.build_absolute_uri(
            reverse("payments:callback")
        )

    @staticmethod
    def _get_locked_order(
            *,
            order_id,
            user=None,
    ) -> Order:
        """
        دریافت سفارش با قفل database.

        در صورت ارسال user، مالکیت سفارش نیز بررسی می‌شود.
        """
        queryset = (
            Order.objects
            .select_for_update()
        )

        if user is not None:
            queryset = queryset.filter(user=user)

        return queryset.get(pk=order_id)

    @staticmethod
    def _mark_payment_failed(
            payment: Payment,
            *,
            message: str,
            raw_response=None,
    ) -> Payment:
        """
        ثبت وضعیت ناموفق برای Payment.
        """
        payment.status = PaymentStatus.FAILED
        payment.error_message = message

        if raw_response is not None:
            payment.gateway_response = raw_response

        payment.save(
            update_fields=[
                "status",
                "error_message",
                "gateway_response",
                "updated_at",
            ]
        )

        return payment

    @staticmethod
    def _mark_payment_cancelled(
            payment: Payment,
            *,
            message: str,
    ) -> Payment:
        """
        ثبت وضعیت لغوشده برای Payment.
        """
        payment.status = PaymentStatus.CANCELLED
        payment.error_message = message

        payment.save(
            update_fields=[
                "status",
                "error_message",
                "updated_at",
            ]
        )

        return payment

    @staticmethod
    @transaction.atomic
    def create_payment(
            *,
            user,
            order,
            gateway_name: str = "zarinpal",
            request=None,
    ) -> Payment:
        """
        ایجاد پرداخت جدید برای سفارش.

        روند:
        1. ساخت callback URL
        2. قفل سفارش
        3. بررسی وضعیت سفارش
        4. بررسی انقضای مهلت پرداخت
        5. بررسی پرداخت pending قبلی
        6. ایجاد Payment
        7. درخواست ایجاد تراکنش از درگاه
        8. ذخیره authority و payment URL
        """

        callback_url = PaymentService._build_callback_url(request)

        # همیشه سفارش را قبل از Payment قفل می‌کنیم.
        # در verify_payment نیز همین ترتیب رعایت می‌شود
        # تا احتمال deadlock کاهش پیدا کند.
        order = PaymentService._get_locked_order(
            order_id=order.pk,
            user=user,
        )

        if order.status != OrderStatus.PENDING:
            raise ValidationServiceError(
                "این سفارش در وضعیت قابل پرداخت نیست.",
                code="order_not_payable",
            )

        if order.is_payment_expired:
            OrderService.expire_order(order.id)

            raise ValidationServiceError(
                "مهلت پرداخت این سفارش به پایان رسیده است.",
                code="payment_expired",
            )

        existing_payment = (
            Payment.objects
            .filter(
                order=order,
                status=PaymentStatus.PENDING,
            )
            .order_by("-created_at")
            .first()
        )

        if existing_payment:
            # اگر تراکنش قبلی authority و payment_url دارد،
            # همان تراکنش قابل ادامه است.
            if existing_payment.payment_url:
                return existing_payment

            PaymentService._mark_payment_failed(
                existing_payment,
                message="پرداخت قبلی ناقص بوده است.",
            )

        gateway = get_payment_gateway(gateway_name)

        payment = Payment.objects.create(
            order=order,
            user=user,
            amount=order.total_amount,
            gateway=gateway.name,
            transaction_id=PaymentService._generate_transaction_id(),
            callback_url=callback_url,
        )

        try:
            result = gateway.create_payment(
                amount=payment.amount,
                description=(
                    f"پرداخت سفارش #{payment.order_id} "
                    "در فروشگاه Shine"
                ),
                callback_url=callback_url,
                metadata={
                    "order_id": str(order.id),
                    "transaction_id": payment.transaction_id,
                },
            )
        except PaymentServiceError:
            raise
        except Exception as exc:
            PaymentService._mark_payment_failed(
                payment,
                message="خطا در برقراری ارتباط با درگاه پرداخت.",
                raw_response={
                    "error": str(exc),
                },
            )

            raise PaymentServiceError(
                "خطا در برقراری ارتباط با درگاه پرداخت.",
                code="payment_gateway_error",
                status_code=502,
            ) from exc

        payment.gateway_response = result.raw_response or {}

        if not result.success:
            PaymentService._mark_payment_failed(
                payment,
                message=result.message,
            )

            raise PaymentServiceError(
                result.message,
                code="payment_creation_failed",
                status_code=502,
                details={
                    "transaction_id": payment.transaction_id,
                },
            )

        if not result.authority:
            PaymentService._mark_payment_failed(
                payment,
                message="شناسه تراکنش از درگاه دریافت نشد.",
            )

            raise PaymentServiceError(
                "شناسه تراکنش از درگاه دریافت نشد.",
                code="payment_authority_missing",
                status_code=502,
            )

        if not result.payment_url:
            PaymentService._mark_payment_failed(
                payment,
                message="آدرس پرداخت از درگاه دریافت نشد.",
            )

            raise PaymentServiceError(
                "آدرس پرداخت از درگاه دریافت نشد.",
                code="payment_url_missing",
                status_code=502,
            )

        payment.authority = result.authority
        payment.payment_url = result.payment_url

        payment.save(
            update_fields=[
                "authority",
                "payment_url",
                "gateway_response",
                "updated_at",
            ]
        )

        return payment

    @staticmethod
    @transaction.atomic
    def verify_payment(
            *,
            authority: str,
            payment_status: str,
    ) -> Payment:
        """
        تأیید پرداخت پس از بازگشت کاربر از درگاه.

        ترتیب قفل:
        Order -> Payment

        این ترتیب باید در مسیرهای مختلف پرداخت یکسان باشد
        تا احتمال deadlock در تراکنش‌های همزمان کاهش پیدا کند.
        """

        if not authority:
            raise PaymentServiceError(
                "شناسه پرداخت دریافت نشد.",
                code="payment_authority_missing",
                status_code=400,
            )

        # ابتدا Payment را بدون lock می‌خوانیم تا order_id مشخص شود.
        payment_info = (
            Payment.objects
            .select_related("order")
            .filter(authority=authority)
            .first()
        )

        if payment_info is None:
            raise PaymentServiceError(
                "تراکنش پرداخت پیدا نشد.",
                code="payment_not_found",
                status_code=404,
            )

        # ابتدا Order قفل می‌شود.
        order = (
            Order.objects
            .select_for_update()
            .get(pk=payment_info.order_id)
        )

        # سپس Payment با همان تراکنش قفل می‌شود.
        payment = (
            Payment.objects
            .select_for_update()
            .select_related("order")
            .get(pk=payment_info.pk)
        )

        # اگر قبلاً موفق شده، callback تکراری نباید
        # دوباره عملیات پرداخت را اجرا کند.
        if payment.status == PaymentStatus.SUCCESS:
            return payment

        # تراکنش‌های failed/cancelled دیگر قابل verify نیستند.
        if payment.status != PaymentStatus.PENDING:
            return payment

        if order.status != OrderStatus.PENDING:
            raise PaymentServiceError(
                "وضعیت سفارش با پرداخت سازگار نیست.",
                code="order_payment_state_mismatch",
                status_code=409,
            )

        if order.is_payment_expired:
            OrderService.expire_order(order.id)

            PaymentService._mark_payment_cancelled(
                payment,
                message="مهلت پرداخت سفارش به پایان رسیده است.",
            )

            return payment

        # در callback زرين‌پال معمولاً Status برابر OK است.
        if payment_status.upper() != "OK":
            PaymentService._mark_payment_cancelled(
                payment,
                message="پرداخت توسط کاربر لغو شد.",
            )

            return payment

        gateway = get_payment_gateway(payment.gateway)

        try:
            result = gateway.verify_payment(
                amount=payment.amount,
                authority=authority,
            )
        except PaymentServiceError:
            raise
        except Exception as exc:
            PaymentService._mark_payment_failed(
                payment,
                message="خطا در برقراری ارتباط با درگاه پرداخت.",
                raw_response={
                    "error": str(exc),
                },
            )

            raise PaymentServiceError(
                "خطا در برقراری ارتباط با درگاه پرداخت.",
                code="payment_verification_gateway_error",
                status_code=502,
            ) from exc

        payment.gateway_response = result.raw_response or {}

        if not result.success:
            PaymentService._mark_payment_failed(
                payment,
                message=result.message,
            )

            raise PaymentServiceError(
                result.message,
                code="payment_verification_failed",
                status_code=502,
            )

        # در این مرحله دوباره وضعیت سفارش را بررسی می‌کنیم.
        # چون Payment و Order هر دو lock شده‌اند، وضعیت پایدار است.
        if order.status != OrderStatus.PENDING:
            raise PaymentServiceError(
                "وضعیت سفارش با تکمیل پرداخت سازگار نیست.",
                code="order_payment_state_mismatch",
                status_code=409,
            )

        payment.status = PaymentStatus.SUCCESS
        payment.reference_id = result.reference_id
        payment.paid_at = timezone.now()

        payment.save(
            update_fields=[
                "status",
                "reference_id",
                "paid_at",
                "gateway_response",
                "updated_at",
            ]
        )

        order.status = OrderStatus.PAID
        order.payment_expires_at = None

        order.save(
            update_fields=[
                "status",
                "payment_expires_at",
                "updated_at",
            ]
        )

        return payment
