from decimal import Decimal
import secrets

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from core.constants import OrderStatus

ZERO = Decimal("0.00")
TRACKING_CODE_LENGTH = 12
TRACKING_CODE_DIGITS = "0123456789"


class Order(models.Model):
    """
    سفارش مشتری.

    اطلاعات مالی و اطلاعات محصول در زمان ثبت سفارش به‌صورت Snapshot
    ذخیره می‌شوند تا تغییرات بعدی محصولات روی سفارش‌های قبلی اثر نگذارد.
    """

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
        choices=OrderStatus.CHOICES,
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
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(ZERO)],
        verbose_name="جمع کالاها",
    )

    shipping_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO,
        validators=[MinValueValidator(ZERO)],
        verbose_name="هزینه ارسال",
    )

    discount_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO,
        validators=[MinValueValidator(ZERO)],
        verbose_name="تخفیف",
    )

    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
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
        unique=True,
        editable=False,
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

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارشات"

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

    def __str__(self):
        return f"Order #{self.pk}"

    # ==================================================================
    # Tracking code
    # ==================================================================

    @classmethod
    def generate_tracking_code(cls) -> str:
        """
        تولید کد رهگیری ۱۲ رقمی.

        unique=True در دیتابیس تضمین نهایی یکتا بودن را انجام می‌دهد.
        """

        return "".join(
            secrets.choice(TRACKING_CODE_DIGITS)
            for _ in range(TRACKING_CODE_LENGTH)
        )

    # ==================================================================
    # Save
    # ==================================================================

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            for _ in range(5):
                code = self.generate_tracking_code()

                if not Order.objects.filter(tracking_code=code).exists():
                    self.tracking_code = code
                    break
            else:
                # پس از ۵ تلاش، خطای یکتایی دیتابیس مسئله را آشکار می‌کند
                self.tracking_code = self.generate_tracking_code()

        super().save(*args, **kwargs)

    # ==================================================================
    # Status helpers
    # ==================================================================

    @property
    def is_paid(self) -> bool:
        return self.status in {
            OrderStatus.PAID,
            OrderStatus.PROCESSING,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
        }

    @property
    def is_payment_expired(self) -> bool:
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
        if not self.payment_expires_at:
            return 0

        remaining = (
                self.payment_expires_at - timezone.now()
        ).total_seconds()

        return max(0, int(remaining))

    # ==================================================================
    # Timeline
    # ==================================================================

    @property
    def status_timeline(self) -> list[dict]:
        """
        مراحل نمایش وضعیت سفارش برای Frontend.
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


class OrderItem(models.Model):
    """
    آیتم سفارش.

    product_name، variant_name، sku و unit_price به‌صورت Snapshot
    ذخیره می‌شوند تا تغییرات محصول در آینده سفارش قدیمی را تغییر ندهد.
    """

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
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(ZERO)],
        verbose_name="قیمت واحد",
    )

    total_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(ZERO)],
        verbose_name="قیمت کل",
    )
