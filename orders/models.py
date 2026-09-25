"""
مدل‌های سفارش پروژهٔ Shine Shop.

شامل:
- Order
- OrderItem

اطلاعات محصول و قیمت در OrderItem به‌صورت Snapshot ذخیره می‌شوند
تا تغییرات بعدی محصول روی سفارش‌های قبلی اثر نگذارد.
"""

from __future__ import annotations

import secrets
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from core.constants import OrderStatus

# ============================================================================
# Constants
# ============================================================================

ZERO = Decimal("0.00")

TRACKING_CODE_LENGTH = 12
TRACKING_CODE_DIGITS = "0123456789"

MONEY_MAX_DIGITS = 14
MONEY_DECIMAL_PLACES = 2


# ============================================================================
# Order
# ============================================================================

class Order(models.Model):
    """
    سفارش مشتری.

    اطلاعات مالی و مشخصات محصول در زمان ثبت سفارش به‌صورت Snapshot
    نگهداری می‌شوند تا تغییرات بعدی محصولات روی سفارش‌های قبلی اثر نگذارد.
    """

    # ------------------------------------------------------------------
    # Customer
    # ------------------------------------------------------------------

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="کاربر",
    )

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True,
        verbose_name="وضعیت",
    )

    status_updated_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="آخرین تغییر وضعیت",
    )

    # ------------------------------------------------------------------
    # Amounts
    # ------------------------------------------------------------------

    subtotal = models.DecimalField(
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        validators=[MinValueValidator(ZERO)],
        verbose_name="جمع کالاها",
    )

    shipping_cost = models.DecimalField(
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        default=ZERO,
        validators=[MinValueValidator(ZERO)],
        verbose_name="هزینه ارسال",
    )

    discount_amount = models.DecimalField(
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        default=ZERO,
        validators=[MinValueValidator(ZERO)],
        verbose_name="تخفیف",
    )

    total_amount = models.DecimalField(
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        validators=[MinValueValidator(ZERO)],
        verbose_name="مبلغ نهایی",
    )

    # ------------------------------------------------------------------
    # Shipping
    # ------------------------------------------------------------------

    recipient_name = models.CharField(
        max_length=150,
        verbose_name="نام گیرنده",
    )

    phone_number = models.CharField(
        max_length=20,
        verbose_name="شماره تماس",
    )

    province = models.CharField(
        max_length=100,
        verbose_name="استان",
    )

    city = models.CharField(
        max_length=100,
        verbose_name="شهر",
    )

    address = models.TextField(
        verbose_name="آدرس",
    )

    postal_code = models.CharField(
        max_length=20,
        verbose_name="کد پستی",
    )

    notes = models.TextField(
        blank=True,
        verbose_name="توضیحات",
    )

    # ------------------------------------------------------------------
    # Payment
    # ------------------------------------------------------------------

    payment_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="مهلت پرداخت",
    )

    # ------------------------------------------------------------------
    # Tracking
    # ------------------------------------------------------------------

    tracking_code = models.CharField(
        max_length=TRACKING_CODE_LENGTH,
        blank=True,
        null=True,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="کد رهگیری",
    )

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی",
    )

    # ------------------------------------------------------------------
    # Meta
    # ------------------------------------------------------------------

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارش‌ها"

        ordering = ("-created_at",)

        indexes = [
            models.Index(
                fields=("user", "-created_at"),
                name="order_user_created_idx",
            ),
            models.Index(
                fields=("status", "-created_at"),
                name="order_status_created_idx",
            ),
            models.Index(
                fields=("status", "payment_expires_at"),
                name="order_payment_expiry_idx",
            ),
        ]

    # ------------------------------------------------------------------
    # String
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        if self.tracking_code:
            return f"سفارش #{self.tracking_code}"

        if self.pk:
            return f"سفارش #{self.pk}"

        return "سفارش جدید"

    # ==================================================================
    # Tracking code
    # ==================================================================

    @classmethod
    def generate_tracking_code(cls) -> str:
        """
        تولید کد رهگیری تصادفی ۱۲ رقمی.

        یکتایی نهایی توسط unique=True در دیتابیس تضمین می‌شود.
        """
        return "".join(
            secrets.choice(TRACKING_CODE_DIGITS)
            for _ in range(TRACKING_CODE_LENGTH)
        )

    def _ensure_tracking_code(self) -> None:
        """
        در صورت نداشتن کد رهگیری، یک کد جدید تولید می‌کند.

        بررسی اولیه برای کاهش احتمال برخورد انجام می‌شود؛
        unique constraint دیتابیس تضمین نهایی را بر عهده دارد.
        """
        if self.tracking_code:
            return

        for _ in range(10):
            code = self.generate_tracking_code()

            if not type(self).objects.filter(
                    tracking_code=code,
            ).exists():
                self.tracking_code = code
                return

        # احتمال برخورد ۱۰ بار بسیار پایین است.
        # در نهایت اجازه می‌دهیم unique constraint دیتابیس
        # برخورد احتمالی را مشخص کند.
        self.tracking_code = self.generate_tracking_code()

    # ==================================================================
    # Save
    # ==================================================================

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        ذخیره سفارش.

        اگر status قبل از ذخیره تغییر کرده باشد، زمان تغییر وضعیت
        نیز به‌روزرسانی می‌شود.
        """
        self._ensure_tracking_code()

        if self.pk:
            previous_status = (
                type(self)
                .objects
                .filter(pk=self.pk)
                .values_list("status", flat=True)
                .first()
            )

            if (
                    previous_status is not None
                    and previous_status != self.status
            ):
                self.status_updated_at = timezone.now()

        elif not self.status_updated_at:
            self.status_updated_at = timezone.now()

        super().save(*args, **kwargs)

    # ==================================================================
    # Status helpers
    # ==================================================================

    @property
    def is_paid(self) -> bool:
        """آیا سفارش وارد یکی از وضعیت‌های بعد از پرداخت شده است؟"""
        return self.status in {
            OrderStatus.PAID,
            OrderStatus.PROCESSING,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
        }

    @property
    def is_terminal(self) -> bool:
        """آیا سفارش به وضعیت نهایی رسیده است؟"""
        return self.status in {
            OrderStatus.DELIVERED,
            OrderStatus.CANCELLED,
        }

    @property
    def is_payment_expired(self) -> bool:
        """آیا مهلت پرداخت سفارش تمام شده است؟"""
        return (
                self.status == OrderStatus.PENDING
                and self.payment_expires_at is not None
                and self.payment_expires_at <= timezone.now()
        )

    # ==================================================================
    # Payment timer
    # ==================================================================

    @property
    def remaining_payment_seconds(self) -> int:
        """
        تعداد ثانیه باقی‌مانده تا پایان مهلت پرداخت.

        اگر مهلت پرداخت وجود نداشته باشد یا تمام شده باشد، صفر برمی‌گرداند.
        """
        if not self.payment_expires_at:
            return 0

        remaining = (
                self.payment_expires_at - timezone.now()
        ).total_seconds()

        return max(0, int(remaining))

    # ==================================================================
    # Status timeline
    # ==================================================================

    @property
    def status_timeline(self) -> list[dict[str, Any]]:
        """
        مراحل وضعیت سفارش برای استفاده در Frontend.

        برای سفارش لغوشده، مراحل بعد از وضعیت فعلی به‌عنوان انجام‌شده
        نمایش داده نمی‌شوند.
        """
        status = self.status

        paid_statuses = {
            OrderStatus.PAID,
            OrderStatus.PROCESSING,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
        }

        processing_statuses = {
            OrderStatus.PROCESSING,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
        }

        shipped_statuses = {
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
        }

        return [
            {
                "key": OrderStatus.PENDING,
                "label": "ثبت سفارش",
                "done": True,
            },
            {
                "key": OrderStatus.PAID,
                "label": "تأیید و پرداخت",
                "done": status in paid_statuses,
            },
            {
                "key": OrderStatus.PROCESSING,
                "label": "آماده‌سازی و بسته‌بندی",
                "done": status in processing_statuses,
            },
            {
                "key": OrderStatus.SHIPPED,
                "label": "ارسال",
                "done": status in shipped_statuses,
            },
            {
                "key": OrderStatus.DELIVERED,
                "label": "تحویل به مشتری",
                "done": status == OrderStatus.DELIVERED,
            },
        ]

    # ==================================================================
    # Amount helpers
    # ==================================================================

    @property
    def calculated_total(self) -> Decimal:
        """
        محاسبه مبلغ نهایی بر اساس Snapshotهای مالی سفارش.

        فرمول:
            subtotal + shipping_cost - discount_amount
        """
        subtotal = self.subtotal or ZERO
        shipping = self.shipping_cost or ZERO
        discount = self.discount_amount or ZERO

        return max(
            ZERO,
            subtotal + shipping - discount,
        )

    @property
    def item_count(self) -> int:
        """تعداد کل واحدهای کالا در سفارش."""
        if not self.pk:
            return 0

        result = self.items.aggregate(
            total=models.Sum("quantity"),
        )

        return int(result["total"] or 0)


# ============================================================================
# OrderItem
# ============================================================================

class OrderItem(models.Model):
    """
    آیتم سفارش.

    فیلدهای product_name، variant_name، sku و unit_price به‌صورت Snapshot
    ذخیره می‌شوند تا تغییرات آینده محصول روی سفارش قدیمی اثر نگذارد.
    """

    # ------------------------------------------------------------------
    # Relations
    # ------------------------------------------------------------------

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="سفارش",
    )

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="محصول",
    )

    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.PROTECT,
        related_name="order_items",
        null=True,
        blank=True,
        verbose_name="تنوع",
    )

    # ------------------------------------------------------------------
    # Product snapshot
    # ------------------------------------------------------------------

    product_name = models.CharField(
        max_length=255,
        verbose_name="نام محصول",
    )

    variant_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="نام تنوع",
    )

    sku = models.CharField(
        max_length=80,
        verbose_name="SKU",
    )

    # ------------------------------------------------------------------
    # Pricing
    # ------------------------------------------------------------------

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="تعداد",
    )

    unit_price = models.DecimalField(
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        validators=[MinValueValidator(ZERO)],
        verbose_name="قیمت واحد",
    )

    total_price = models.DecimalField(
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        validators=[MinValueValidator(ZERO)],
        verbose_name="قیمت کل",
    )

    # ------------------------------------------------------------------
    # Meta
    # ------------------------------------------------------------------

    class Meta:
        verbose_name = "آیتم سفارش"
        verbose_name_plural = "آیتم‌های سفارش"

        ordering = ("id",)

        indexes = [
            models.Index(
                fields=("order",),
                name="orderitem_order_idx",
            ),
            models.Index(
                fields=("product",),
                name="orderitem_product_idx",
            ),
            models.Index(
                fields=("sku",),
                name="orderitem_sku_idx",
            ),
        ]

    # ------------------------------------------------------------------
    # String
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        return f"{self.product_name} × {self.quantity}"

    # ==================================================================
    # Pricing
    # ==================================================================

    @property
    def calculated_total(self) -> Decimal:
        """محاسبه قیمت کل بر اساس تعداد و قیمت واحد."""
        return (
                (self.unit_price or ZERO)
                * Decimal(self.quantity or 0)
        )

    # ==================================================================
    # Save
    # ==================================================================

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        ذخیره آیتم سفارش.

        total_price به‌صورت خودکار از quantity × unit_price محاسبه می‌شود
        تا مقدار ذخیره‌شده با قیمت واحد و تعداد هماهنگ بماند.
        """
        self.total_price = self.calculated_total

        super().save(*args, **kwargs)
