import uuid

from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from core.constants import OrderStatus, PaymentStatus
from core.exceptions import PaymentError, ValidationError

from orders.models import Order
from orders.services import OrderService

from .gateways import get_payment_gateway
from .models import Payment


class PaymentService:

    @staticmethod
    def _generate_transaction_id():
        return uuid.uuid4().hex

    @staticmethod
    def _build_callback_url(request):
        if request is None:
            raise PaymentError(
                "آدرس بازگشت پرداخت مشخص نشده است."
            )

        return request.build_absolute_uri(
            reverse("payments:callback")
        )

    @staticmethod
    @transaction.atomic
    def create_payment(
            *,
            user,
            order,
            gateway_name="zarinpal",
            request=None,
    ):
        callback_url = (
            PaymentService
            ._build_callback_url(request)
        )

        order = (
            Order.objects
            .select_for_update()
            .get(
                pk=order.pk,
                user=user,
            )
        )

        if order.status != OrderStatus.PENDING:
            raise ValidationError(
                "این سفارش در وضعیت قابل پرداخت نیست."
            )

        if order.is_payment_expired:
            OrderService.expire_order(
                order.id
            )

            raise ValidationError(
                "مهلت پرداخت این سفارش به پایان رسیده است."
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
            if existing_payment.payment_url:
                return existing_payment

            existing_payment.status = (
                PaymentStatus.FAILED
            )

            existing_payment.error_message = (
                "پرداخت قبلی ناقص بوده است."
            )

            existing_payment.save(
                update_fields=[
                    "status",
                    "error_message",
                    "updated_at",
                ]
            )

        gateway = get_payment_gateway(
            gateway_name
        )

        payment = Payment.objects.create(
            order=order,
            user=user,
            amount=order.total_amount,
            gateway=gateway.name,
            transaction_id=(
                PaymentService
                ._generate_transaction_id()
            ),
            callback_url=callback_url,
        )

        result = gateway.create_payment(
            amount=payment.amount,
            description=(
                f"پرداخت سفارش #{payment.order_id} "
                f"در فروشگاه Shine"
            ),
            callback_url=callback_url,
            metadata={
                "order_id": str(order.id),
                "transaction_id": (
                    payment.transaction_id
                ),
            },
        )

        payment.gateway_response = (
                result.raw_response or {}
        )

        if not result.success:
            payment.status = PaymentStatus.FAILED
            payment.error_message = result.message

            payment.save(
                update_fields=[
                    "status",
                    "gateway_response",
                    "error_message",
                    "updated_at",
                ]
            )

            raise PaymentError(result.message)

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
            authority,
            payment_status,
    ):
        if not authority:
            raise PaymentError(
                "شناسه پرداخت دریافت نشد."
            )

        payment = (
            Payment.objects
            .select_for_update()
            .select_related("order")
            .filter(authority=authority)
            .first()
        )

        if payment is None:
            raise PaymentError(
                "تراکنش پرداخت پیدا نشد."
            )

        if payment.status == PaymentStatus.SUCCESS:
            return payment

        if payment.status != PaymentStatus.PENDING:
            return payment

        if payment.order.status != OrderStatus.PENDING:
            raise PaymentError(
                "وضعیت سفارش با پرداخت سازگار نیست."
            )

        if (
                payment.order.is_payment_expired
        ):
            OrderService.expire_order(
                payment.order_id
            )

            payment.status = (
                PaymentStatus.CANCELLED
            )

            payment.error_message = (
                "مهلت پرداخت سفارش به پایان رسیده است."
            )

            payment.save(
                update_fields=[
                    "status",
                    "error_message",
                    "updated_at",
                ]
            )

            return payment

        if payment_status != "OK":
            payment.status = (
                PaymentStatus.CANCELLED
            )

            payment.error_message = (
                "پرداخت توسط کاربر لغو شد."
            )

            payment.save(
                update_fields=[
                    "status",
                    "error_message",
                    "updated_at",
                ]
            )

            return payment

        gateway = get_payment_gateway(
            payment.gateway
        )

        result = gateway.verify_payment(
            amount=payment.amount,
            authority=authority,
        )

        payment.gateway_response = (
                result.raw_response or {}
        )

        if not result.success:
            payment.status = PaymentStatus.FAILED
            payment.error_message = result.message

            payment.save(
                update_fields=[
                    "status",
                    "gateway_response",
                    "error_message",
                    "updated_at",
                ]
            )

            raise PaymentError(
                result.message
            )

        order = (
            Order.objects
            .select_for_update()
            .get(pk=payment.order_id)
        )

        if order.status != OrderStatus.PENDING:
            raise PaymentError(
                "وضعیت سفارش با تکمیل پرداخت سازگار نیست."
            )

        payment.status = PaymentStatus.SUCCESS
        payment.reference_id = (
            result.reference_id
        )
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
