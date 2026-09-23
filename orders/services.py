from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone

from cart.models import Cart
from core.constants import OrderStatus
from core.exceptions import InsufficientStockError, ValidationError
from products.models import Product, ProductVariant

from .models import Order, OrderItem

ZERO = Decimal("0.00")


class OrderService:
    """
    منطق اصلی سفارش.

    مسئولیت‌های این Service:
    - ایجاد سفارش از سبد خرید
    - رزرو موجودی
    - آزادسازی موجودی
    - لغو سفارش
    - انقضای سفارش‌های پرداخت‌نشده

    تمام عملیات حساس به موجودی داخل transaction انجام می‌شوند.
    """

    # ==================================================================
    # Payment
    # ==================================================================

    @staticmethod
    def _payment_deadline():
        timeout_minutes = max(
            5,
            int(settings.ORDER_PAYMENT_TIMEOUT_MINUTES),
        )

        return timezone.now() + timedelta(
            minutes=timeout_minutes,
        )

    # ==================================================================
    # Create order
    # ==================================================================

    @staticmethod
    @transaction.atomic
    def create_from_cart(*, user, shipping_data):
        """
        ایجاد سفارش از سبد خرید.

        در این مرحله:
        1. سبد قفل می‌شود.
        2. آیتم‌های سبد قفل می‌شوند.
        3. Product / Variant قفل می‌شوند.
        4. موجودی بررسی و رزرو می‌شود.
        5. Order ساخته می‌شود.
        6. OrderItemها ساخته می‌شوند.
        7. سبد خالی می‌شود.

        اگر هر مرحله‌ای شکست بخورد، کل transaction rollback می‌شود.
        """

        cart = (
            Cart.objects
            .select_for_update()
            .filter(user=user)
            .first()
        )

        if cart is None:
            raise ValidationError(
                "سبد خرید پیدا نشد."
            )

        cart_items = list(
            cart.items
            .select_related("product", "variant")
            .select_for_update()
            .order_by("product_id", "variant_id")
        )

        if not cart_items:
            raise ValidationError(
                "سبد خرید خالی است."
            )

        subtotal = ZERO

        # آبجکت‌های قفل‌شده را نگه می‌داریم تا دوباره query نزنیم.
        products = {}
        variants = {}

        # --------------------------------------------------------------
        # Validate products and calculate subtotal
        # --------------------------------------------------------------

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

            products[product.pk] = product

            # ----------------------------------------------------------
            # Variant
            # ----------------------------------------------------------

            if item.variant_id:
                variant = (
                    ProductVariant.objects
                    .select_for_update()
                    .get(pk=item.variant_id)
                )

                if variant.product_id != product.pk:
                    raise ValidationError(
                        f"تنوع محصول «{product.name}» معتبر نیست."
                    )

                if not variant.is_active:
                    raise ValidationError(
                        f"تنوع «{variant.name}» دیگر فعال نیست."
                    )

                if variant.stock < item.quantity:
                    raise InsufficientStockError(
                        f"موجودی «{product.name} - {variant.name}» "
                        "کافی نیست."
                    )

                variants[variant.pk] = variant

                unit_price = variant.final_price

            # ----------------------------------------------------------
            # Product without Variant
            # ----------------------------------------------------------

            else:
                if product.stock < item.quantity:
                    raise InsufficientStockError(
                        f"موجودی «{product.name}» کافی نیست."
                    )

                unit_price = product.final_price

            subtotal += (
                    unit_price * item.quantity
            )

        # --------------------------------------------------------------
        # Calculate order amounts
        # --------------------------------------------------------------

        shipping_cost = ZERO
        discount_amount = ZERO

        total_amount = (
                subtotal
                + shipping_cost
                - discount_amount
        )

        if total_amount < ZERO:
            raise ValidationError(
                "مبلغ نهایی سفارش نمی‌تواند منفی باشد."
            )

        # --------------------------------------------------------------
        # Create order
        # --------------------------------------------------------------

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

        # --------------------------------------------------------------
        # Reserve stock + create order items
        # --------------------------------------------------------------

        order_items = []

        for cart_item in cart_items:
            product = products[cart_item.product_id]

            if cart_item.variant_id:
                variant = variants[cart_item.variant_id]

                unit_price = variant.final_price

                variant.stock -= cart_item.quantity

                variant.save(
                    update_fields=[
                        "stock",
                    ]
                )

                sku = variant.sku
                variant_name = variant.name

            else:
                unit_price = product.final_price

                product.stock -= cart_item.quantity

                product.save(
                    update_fields=[
                        "stock",
                    ]
                )

                sku = product.sku
                variant_name = ""

            order_items.append(
                OrderItem(
                    order=order,
                    product_id=product.pk,
                    variant_id=cart_item.variant_id,
                    product_name=product.name,
                    variant_name=variant_name,
                    sku=sku,
                    quantity=cart_item.quantity,
                    unit_price=unit_price,
                    total_price=(
                            unit_price * cart_item.quantity
                    ),
                )
            )

        OrderItem.objects.bulk_create(order_items)

        # --------------------------------------------------------------
        # Clear cart
        # --------------------------------------------------------------

        cart.items.all().delete()

        return order

    # ==================================================================
    # Cancel order
    # ==================================================================

    @staticmethod
    @transaction.atomic
    def cancel_order(*, user, order_id):
        """
        لغو سفارش توسط کاربر.

        فقط سفارش Pending قابل لغو است.
        """

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

        now = timezone.now()

        order.status = OrderStatus.CANCELLED
        order.status_updated_at = now
        order.payment_expires_at = None

        order.save(
            update_fields=[
                "status",
                "status_updated_at",
                "payment_expires_at",
                "updated_at",
            ]
        )

        return order

    # ==================================================================
    # Expire single order
    # ==================================================================

    @staticmethod
    @transaction.atomic
    def expire_order(order_id):
        """
        انقضای یک سفارش Pending.

        اگر سفارش قبلاً پرداخت/لغو شده باشد،
        هیچ کاری انجام نمی‌شود.
        """

        order = (
            Order.objects
            .select_for_update()
            .filter(
                pk=order_id,
                status=OrderStatus.PENDING,
            )
            .first()
        )

        if order is None:
            return False

        if not order.payment_expires_at:
            return False

        if order.payment_expires_at > timezone.now():
            return False

        OrderService._restore_stock(order)

        now = timezone.now()

        order.status = OrderStatus.CANCELLED
        order.status_updated_at = now
        order.payment_expires_at = None

        order.save(
            update_fields=[
                "status",
                "status_updated_at",
                "payment_expires_at",
                "updated_at",
            ]
        )

        return True

    # ==================================================================
    # Expire pending orders
    # ==================================================================

    @staticmethod
    def expire_pending_orders(*, batch_size=500):
        """
        پیدا کردن سفارش‌های منقضی‌شده و آزادسازی موجودی آنها.

        این متد مناسب اجرای دوره‌ای توسط Celery / Cron است.
        """

        now = timezone.now()

        order_ids = list(
            Order.objects
            .filter(
                status=OrderStatus.PENDING,
                payment_expires_at__isnull=False,
                payment_expires_at__lte=now,
            )
            .order_by("id")
            .values_list("id", flat=True)[:batch_size]
        )

        expired_count = 0

        for order_id in order_ids:
            if OrderService.expire_order(order_id):
                expired_count += 1

        return expired_count

    # ==================================================================
    # Restore stock
    # ==================================================================

    @staticmethod
    def _restore_stock(order):
        """
        بازگرداندن موجودی اقلام سفارش.

        با F-expression انجام می‌شود تا حتی اگر
        موجودی هم‌زمان تغییر کرده باشد، جمع درست باشد.
        """

        for item in order.items.all():
            if item.variant_id:
                ProductVariant.objects.filter(
                    pk=item.variant_id,
                ).update(
                    stock=F("stock") + item.quantity,
                )
            else:
                Product.objects.filter(
                    pk=item.product_id,
                ).update(
                    stock=F("stock") + item.quantity,
                )
