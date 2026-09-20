from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from cart.models import Cart
from core.constants import OrderStatus
from core.exceptions import InsufficientStockError, ValidationError
from products.models import Product, ProductVariant

from .models import Order, OrderItem


class OrderService:

    @staticmethod
    def _payment_deadline():
        minutes = max(
            5,
            settings.ORDER_PAYMENT_TIMEOUT_MINUTES,
        )

        return timezone.now() + timedelta(
            minutes=minutes,
        )

    @staticmethod
    @transaction.atomic
    def create_from_cart(*, user, shipping_data):
        cart = (
            Cart.objects
            .select_for_update()
            .filter(user=user)
            .first()
        )

        if not cart:
            raise ValidationError("سبد خرید پیدا نشد.")

        cart_items = list(
            cart.items
            .select_related("product", "variant")
            .select_for_update()
        )

        if not cart_items:
            raise ValidationError("سبد خرید خالی است.")

        subtotal = Decimal("0.00")

        locked_products = {}
        locked_variants = {}

        for item in cart_items:
            product = (
                Product.objects
                .select_for_update()
                .get(pk=item.product_id)
            )

            if not product.is_available:
                raise ValidationError(
                    f"محصول «{product.name}» دیگر قابل فروش نیست."
                )

            if item.variant_id:
                variant = (
                    ProductVariant.objects
                    .select_for_update()
                    .get(pk=item.variant_id)
                )

                if (
                        not variant.is_active
                        or variant.product_id != product.id
                ):
                    raise ValidationError(
                        f"تنوع محصول «{product.name}» معتبر نیست."
                    )

                if variant.stock < item.quantity:
                    raise InsufficientStockError(
                        f"موجودی «{product.name}» کافی نیست."
                    )

                locked_variants[variant.id] = variant
                unit_price = variant.final_price

            else:
                if product.stock < item.quantity:
                    raise InsufficientStockError(
                        f"موجودی «{product.name}» کافی نیست."
                    )

                locked_products[product.id] = product
                unit_price = product.final_price

            subtotal += unit_price * item.quantity

        shipping_cost = Decimal("0.00")
        discount_amount = Decimal("0.00")

        total_amount = (
                subtotal
                + shipping_cost
                - discount_amount
        )

        if total_amount < 0:
            raise ValidationError(
                "مبلغ سفارش نامعتبر است."
            )

        order = Order.objects.create(
            user=user,
            status=OrderStatus.PENDING,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            discount_amount=discount_amount,
            total_amount=total_amount,
            recipient_name=shipping_data["recipient_name"],
            phone_number=shipping_data["phone_number"],
            province=shipping_data["province"],
            city=shipping_data["city"],
            address=shipping_data["address"],
            postal_code=shipping_data["postal_code"],
            notes=shipping_data.get("notes", ""),
            payment_expires_at=OrderService._payment_deadline(),
        )

        order_items = []

        for item in cart_items:
            if item.variant_id:
                variant = locked_variants[item.variant_id]

                unit_price = variant.final_price

                variant.stock -= item.quantity
                variant.save(
                    update_fields=["stock"]
                )

                sku = variant.sku
                variant_name = variant.name

            else:
                product = locked_products[item.product_id]

                unit_price = product.final_price

                product.stock -= item.quantity
                product.save(
                    update_fields=["stock"]
                )

                sku = product.sku
                variant_name = ""

            order_items.append(
                OrderItem(
                    order=order,
                    product_id=item.product_id,
                    variant_id=item.variant_id,
                    product_name=item.product.name,
                    variant_name=variant_name,
                    sku=sku,
                    quantity=item.quantity,
                    unit_price=unit_price,
                    total_price=(
                            unit_price * item.quantity
                    ),
                )
            )

        OrderItem.objects.bulk_create(
            order_items
        )

        cart.items.all().delete()

        return order

    @staticmethod
    @transaction.atomic
    def cancel_order(*, user, order_id):
        order = get_object_or_404(
            Order.objects.select_for_update(),
            pk=order_id,
            user=user,
        )

        if order.status != OrderStatus.PENDING:
            raise ValidationError(
                "این سفارش در وضعیت فعلی قابل لغو نیست."
            )

        OrderService._restore_stock(order)

        order.status = OrderStatus.CANCELLED
        order.payment_expires_at = None

        order.save(
            update_fields=[
                "status",
                "payment_expires_at",
                "updated_at",
            ]
        )

        return order

    @staticmethod
    @transaction.atomic
    def expire_order(order_id):
        order = (
            Order.objects
            .select_for_update()
            .filter(
                pk=order_id,
                status=OrderStatus.PENDING,
            )
            .first()
        )

        if not order:
            return False

        if (
                order.payment_expires_at
                and order.payment_expires_at > timezone.now()
        ):
            return False

        OrderService._restore_stock(order)

        order.status = OrderStatus.CANCELLED
        order.payment_expires_at = None

        order.save(
            update_fields=[
                "status",
                "payment_expires_at",
                "updated_at",
            ]
        )

        return True

    @staticmethod
    def expire_pending_orders():
        order_ids = list(
            Order.objects
            .filter(
                status=OrderStatus.PENDING,
                payment_expires_at__lte=timezone.now(),
            )
            .values_list("id", flat=True)[:500]
        )

        expired = 0

        for order_id in order_ids:
            if OrderService.expire_order(order_id):
                expired += 1

        return expired

    @staticmethod
    def _restore_stock(order):
        items = list(
            order.items
            .select_related("product", "variant")
        )

        for item in items:
            if item.variant_id:
                variant = (
                    ProductVariant.objects
                    .select_for_update()
                    .get(pk=item.variant_id)
                )

                variant.stock += item.quantity

                variant.save(
                    update_fields=["stock"]
                )

            else:
                product = (
                    Product.objects
                    .select_for_update()
                    .get(pk=item.product_id)
                )

                product.stock += item.quantity

                product.save(
                    update_fields=["stock"]
                )
