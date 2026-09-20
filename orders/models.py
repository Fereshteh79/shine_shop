from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from core.constants import OrderStatus


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="کاربر",
    )

    status = models.CharField(
        max_length=20,
        choices=OrderStatus.CHOICES,
        default=OrderStatus.PENDING,
        db_index=True,
        verbose_name="وضعیت",
    )

    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="جمع کالاها",
    )

    shipping_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="هزینه ارسال",
    )

    discount_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="تخفیف",
    )

    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="مبلغ نهایی",
    )

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

    payment_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="مهلت پرداخت",
    )

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
            ),
            models.Index(
                fields=("status", "-created_at"),
            ),
            models.Index(
                fields=("status", "payment_expires_at"),
            ),
        ]

    def __str__(self):
        return f"Order #{self.pk}"

    @property
    def is_paid(self):
        return self.status in {
            OrderStatus.PAID,
            OrderStatus.PROCESSING,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
        }

    @property
    def is_payment_expired(self):
        return (
                self.status == OrderStatus.PENDING
                and self.payment_expires_at is not None
                and self.payment_expires_at <= timezone.now()
        )

    @property
    def remaining_payment_seconds(self):
        if not self.payment_expires_at:
            return 0

        seconds = (
                self.payment_expires_at - timezone.now()
        ).total_seconds()

        return max(0, int(seconds))


class OrderItem(models.Model):
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

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="تعداد",
    )

    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="قیمت واحد",
    )

    total_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="مجموع",
    )

    class Meta:
        verbose_name = "آیتم سفارش"
        verbose_name_plural = "آیتم‌های سفارش"
        ordering = ("id",)

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"
